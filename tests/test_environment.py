"""Environment module tests."""

import pytest

from pyteslacoil.engine.environment import (
    calculate_environment,
    equivalent_sphere_radius,
    proximity_factor,
)
from pyteslacoil.models.environment_model import EnvironmentInput

C_TOP = 20e-12  # a 20 pF topload: equivalent sphere radius ≈ 0.18 m


def test_free_space_factor_is_one():
    assert proximity_factor(EnvironmentInput(), 1.0, C_TOP) == 1.0
    out = calculate_environment(EnvironmentInput())
    assert "Free space" in out.notes
    assert out.proximity_correction_factor == 1.0


def test_large_ground_plane_matches_the_image_charge_formula():
    """A sphere of radius a at height h over an infinite plane: C ≈ C₀ / (1 − a/(2h))."""
    a = equivalent_sphere_radius(C_TOP)
    factor = proximity_factor(EnvironmentInput(ground_plane_radius=1e6), 1.0, C_TOP)
    assert factor == pytest.approx(1.0 / (1.0 - a / 2.0), rel=1e-6)


def test_ground_plane_effect_shrinks_with_height_and_plane_size():
    env = EnvironmentInput(ground_plane_radius=3.0)
    low = proximity_factor(env, 0.5, C_TOP)
    high = proximity_factor(env, 2.0, C_TOP)
    assert low > high > 1.0
    small_plane = proximity_factor(EnvironmentInput(ground_plane_radius=0.3), 0.5, C_TOP)
    assert 1.0 < small_plane < low


def test_closer_walls_and_ceiling_raise_capacitance_more():
    near = proximity_factor(EnvironmentInput(wall_radius=1.0), 1.0, C_TOP)
    far = proximity_factor(EnvironmentInput(wall_radius=10.0), 1.0, C_TOP)
    assert near > far > 1.0
    low_ceiling = proximity_factor(EnvironmentInput(ceiling_height=1.5), 1.0, C_TOP)
    high_ceiling = proximity_factor(EnvironmentInput(ceiling_height=5.0), 1.0, C_TOP)
    assert low_ceiling > high_ceiling > 1.0


def test_ceiling_below_the_topload_is_ignored_with_a_warning():
    out = calculate_environment(EnvironmentInput(ceiling_height=0.5), 1.0, C_TOP)
    assert out.proximity_correction_factor == 1.0
    assert any("ceiling" in w for w in out.warnings)


def test_no_topload_means_no_correction():
    out = calculate_environment(EnvironmentInput(ground_plane_radius=2.0))
    assert out.proximity_correction_factor == 1.0
    assert "No topload" in out.notes


def test_extreme_proximity_is_capped_and_reported():
    out = calculate_environment(EnvironmentInput(wall_radius=0.25), 1.0, C_TOP)
    assert out.proximity_correction_factor == pytest.approx(2.0)
    assert out.warnings
