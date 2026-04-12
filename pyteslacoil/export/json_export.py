"""JSON export / import for PyTeslaCoil designs.

Round-trippable: ``from_json(to_json(design))`` reconstructs an equal
design. Outputs are also serialized so a saved file is a snapshot of
the entire calculation, not just the inputs.
"""

from __future__ import annotations

import json

from pyteslacoil.models import CoilDesign, FullSystemOutput


def to_json(design: CoilDesign, outputs: FullSystemOutput | None = None) -> str:
    payload = {
        "design": design.model_dump(mode="json"),
        "outputs": outputs.model_dump(mode="json") if outputs else None,
    }
    return json.dumps(payload, indent=2)


def from_json(text: str) -> CoilDesign:
    data = json.loads(text)
    return CoilDesign.model_validate(data["design"])
