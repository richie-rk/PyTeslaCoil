"""Surrounding environment effects (ground plane, walls, ceiling).

A topload near a conductive surface has higher capacitance than the same
topload in free space because of image-charge effects. This module
provides a simple proximity-correction multiplier that the system-level
calculator can apply to the bare topload capacitance.

The model used here is intentionally lightweight; serious users should
consult Paul Nicholson's TSSP / GEOTC for higher fidelity.
"""

from __future__ import annotations

from pyteslacoil.models.environment_model import (
    EnvironmentInput,
    EnvironmentOutput,
)


def proximity_factor(env: EnvironmentInput, topload_height_m: float = 0.0) -> float:
    """Return a multiplicative correction for topload capacitance.

    A topload over an infinite ground plane experiences a capacitance
    increase that depends on the topload height. For a sphere of radius
    ``a`` at height ``h`` above an infinite plane, the correction is
    approximately ``1 + a/(2h)`` for ``h ≫ a``. We approximate the same
    behavior for general toploads, treating ``topload_height_m`` as the
    centroid height above the plane.

    Walls and ceilings give an additional small bump (~5 % each at
    typical Tesla coil operating distances). We fold those in as fixed
    multipliers.
    """
    factor = 1.0

    # Ground plane: only applies if a finite plane is present.
    if env.ground_plane_radius > 0 and topload_height_m > 0:
        # Heuristic: correction shrinks as height grows.
        # Saturates around 1.10 for a topload sitting just above the plane.
        factor *= 1.0 + 0.1 / (1.0 + topload_height_m)

    if env.wall_radius > 0:
        factor *= 1.05
    if env.ceiling_height > 0:
        factor *= 1.05
    return factor


def calculate_environment(env: EnvironmentInput) -> EnvironmentOutput:
    f = proximity_factor(env)
    notes = []
    if env.ground_plane_radius > 0:
        notes.append(f"Ground plane radius {env.ground_plane_radius:.2f} m")
    if env.wall_radius > 0:
        notes.append(f"Walls at radius {env.wall_radius:.2f} m")
    if env.ceiling_height > 0:
        notes.append(f"Ceiling at {env.ceiling_height:.2f} m")
    if not notes:
        notes.append("Free space (no proximity effects)")
    return EnvironmentOutput(
        proximity_correction_factor=f,
        notes="; ".join(notes),
    )
