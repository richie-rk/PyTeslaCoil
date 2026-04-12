"""Environment module tests."""

from pyteslacoil.engine.environment import calculate_environment, proximity_factor
from pyteslacoil.models.environment_model import EnvironmentInput


def test_free_space_factor_is_one():
    env = EnvironmentInput()
    assert proximity_factor(env, topload_height_m=1.0) == 1.0


def test_walls_and_ceiling_increase_factor():
    env = EnvironmentInput(wall_radius=2.0, ceiling_height=3.0)
    assert proximity_factor(env, topload_height_m=1.0) > 1.0


def test_calculate_environment_notes_free_space():
    out = calculate_environment(EnvironmentInput())
    assert "Free space" in out.notes
    assert out.proximity_correction_factor == 1.0
