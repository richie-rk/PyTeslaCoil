"""Topload module tests.

Toroid values are checked against an independent numerical solution: the
method of fundamental solutions (charge rings inside the torus, potential
matched on its surface), which converges to the exact capacitance.
"""

import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.special import ellipk

from pyteslacoil.constants import EPSILON_0, PI
from pyteslacoil.engine.topload import (
    calculate_sphere_capacitance,
    calculate_topload,
    calculate_toroid_capacitance,
    torus_capacitance,
)
from pyteslacoil.models.coil_design import ToploadType
from pyteslacoil.models.topload_model import ToploadInput
from pyteslacoil.units import inches_to_meters


def _mfs_torus_capacitance(centre_radius: float, tube_radius: float, points: int = 400) -> float:
    theta = np.linspace(0.0, 2.0 * np.pi, points, endpoint=False)
    rc, zc = centre_radius + tube_radius * np.cos(theta), tube_radius * np.sin(theta)
    rs, zs = centre_radius + 0.6 * tube_radius * np.cos(theta), 0.6 * tube_radius * np.sin(theta)
    den = (rc[:, None] + rs[None, :]) ** 2 + (zc[:, None] - zs[None, :]) ** 2
    m = 4.0 * rc[:, None] * rs[None, :] / den
    potential = (2.0 / np.pi) * ellipk(m) / np.sqrt(den) / (4.0 * np.pi * EPSILON_0)
    charges = np.linalg.solve(potential, np.ones(points))
    return float(charges.sum())


def test_sphere_capacitance_exact():
    """Sphere of 1 m diameter has C = 4πε₀ · 0.5 m."""
    assert calculate_sphere_capacitance(1.0) == pytest.approx(4.0 * PI * EPSILON_0 * 0.5, rel=1e-9)


def test_sphere_capacitance_inches_rule_of_thumb():
    """C(pF) ≈ 1.412 · diameter[in] for an isolated sphere."""
    pf = calculate_sphere_capacitance(inches_to_meters(12.0)) * 1e12
    assert pf == pytest.approx(1.412 * 12.0, rel=0.01)


@pytest.mark.parametrize("ratio", [0.05, 0.1, 0.2, 0.3, 0.45])
def test_toroid_matches_independent_field_solution(ratio):
    major = inches_to_meters(20.0)
    minor = ratio * major
    reference = _mfs_torus_capacitance(0.5 * (major - minor), 0.5 * minor)
    assert calculate_toroid_capacitance(major, minor) == pytest.approx(reference, rel=1e-4)


def test_thin_toroid_approaches_thin_ring_limit():
    """C → 4π² ε₀ R / ln(8R/a) for a thin ring."""
    centre, tube = 0.5, 0.0005
    limit = 4.0 * PI * PI * EPSILON_0 * centre / math.log(8.0 * centre / tube)
    assert torus_capacitance(centre, tube) == pytest.approx(limit, rel=0.002)


def test_empirical_fit_agrees_for_typical_toroids():
    """The JavaTC-style fit 2.8·(1.2781 − d/D)·√(π(D−d)d/4) pF is within 2 % here."""
    for d_in, big_d_in in [(4.0, 20.0), (4.0, 13.0), (6.0, 24.0)]:
        fit_pf = 2.8 * (1.2781 - d_in / big_d_in) * math.sqrt(PI * (big_d_in - d_in) * d_in / 4)
        pf = calculate_toroid_capacitance(inches_to_meters(big_d_in), inches_to_meters(d_in)) * 1e12
        assert pf == pytest.approx(fit_pf, rel=0.02)


def test_toroid_capacitance_is_continuous_across_aspect_ratios():
    major = inches_to_meters(20.0)
    values = [calculate_toroid_capacitance(major, r * major) for r in np.linspace(0.02, 0.48, 47)]
    steps = np.diff(values)
    assert np.all(steps > 0)  # fatter tube, more capacitance
    assert np.max(np.abs(np.diff(steps))) < 0.5 * np.max(steps)  # no jumps


def test_small_toroid_value():
    """A 4 in × 1 in toroid is about 4.4 pF."""
    pf = calculate_toroid_capacitance(inches_to_meters(4.0), inches_to_meters(1.0)) * 1e12
    assert pf == pytest.approx(4.37, abs=0.05)


def test_toroid_minor_must_leave_a_hole():
    with pytest.raises(ValueError):
        calculate_toroid_capacitance(inches_to_meters(4.0), inches_to_meters(2.0))
    with pytest.raises(ValidationError):
        ToploadInput(
            major_diameter=inches_to_meters(4.0),
            minor_diameter=inches_to_meters(2.5),
            height=inches_to_meters(20.0),
        )


def test_topload_dispatch_toroid():
    inp = ToploadInput(
        topload_type=ToploadType.TOROID,
        major_diameter=inches_to_meters(6.0),
        minor_diameter=inches_to_meters(1.5),
        height=inches_to_meters(20.0),
    )
    out = calculate_topload(inp)
    assert out.topload_type == ToploadType.TOROID
    assert out.capacitance_pf == pytest.approx(out.capacitance_f * 1e12)


def test_topload_dispatch_sphere():
    inp = ToploadInput(
        topload_type=ToploadType.SPHERE,
        sphere_diameter=inches_to_meters(8.0),
        height=inches_to_meters(20.0),
    )
    out = calculate_topload(inp)
    assert out.topload_type == ToploadType.SPHERE
    assert out.capacitance_f == pytest.approx(calculate_sphere_capacitance(inches_to_meters(8.0)))


def test_topload_none_needs_no_dimensions():
    out = calculate_topload(ToploadInput(topload_type=ToploadType.NONE))
    assert out.capacitance_pf == 0.0


def test_toroid_requires_height():
    with pytest.raises(ValidationError):
        ToploadInput(major_diameter=0.5, minor_diameter=0.1)
