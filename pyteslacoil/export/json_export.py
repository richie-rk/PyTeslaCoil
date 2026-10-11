"""JSON export / import for PyTeslaCoil designs.

Round-trippable: ``from_json(to_json(design))`` reconstructs an equal
design. Outputs are also serialized so a saved file is a snapshot of
the entire calculation, not just the inputs (they are recomputed, not read
back, on import).
"""

from __future__ import annotations

import json

from pyteslacoil.models import CoilDesign, FullSystemOutput

SCHEMA_VERSION = 2
"""Version of the export format. Files without a version are version 1."""


def to_json(design: CoilDesign, outputs: FullSystemOutput | None = None) -> str:
    payload = {
        "format": "pyteslacoil",
        "schema_version": SCHEMA_VERSION,
        "design": design.model_dump(mode="json"),
        "outputs": outputs.model_dump(mode="json") if outputs else None,
    }
    return json.dumps(payload, indent=2)


def from_json(text: str) -> CoilDesign:
    """Load the design from a :func:`to_json` export.

    Raises :class:`ValueError` (including Pydantic's ``ValidationError``) if
    the text is not a PyTeslaCoil export or the design is invalid.
    """
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("design"), dict):
        raise ValueError("Not a PyTeslaCoil export: the 'design' object is missing")
    version = data.get("schema_version", 1)
    if not isinstance(version, int) or version > SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported export schema version {version!r}; this version reads up to "
            f"{SCHEMA_VERSION}"
        )
    # Version 1 designs are field-compatible with version 2.
    return CoilDesign.model_validate(data["design"])
