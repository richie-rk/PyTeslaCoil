"""Small argument checks shared by the engine helpers."""

from __future__ import annotations


def require_positive(**values: float) -> None:
    """Raise :class:`ValueError` unless every keyword value is strictly positive."""
    for name, value in values.items():
        if not value > 0:
            raise ValueError(f"{name} must be positive, got {value!r}")


def require_set(value: float | None, name: str) -> float:
    """Return ``value``, raising :class:`ValueError` if it is ``None``."""
    if value is None:
        raise ValueError(f"{name} is required for a stand-alone calculation")
    return value
