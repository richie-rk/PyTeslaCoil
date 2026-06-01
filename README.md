<div align="center">

[![PyTeslaCoil](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/pyTesla-coil_header.png)](docs/pyTesla-coil_header.png)

A Tesla coil design calculator written in pure Python, built as an open-source replacement for JavaTC. It has a physics engine, Pydantic v2 models, and a NiceGUI web frontend.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/) [![Tests](https://img.shields.io/badge/Tests-73%20passed-brightgreen.svg)](https://github.com/richie-rk/PyTeslaCoil/blob/main) [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Richie-rk/pyteslacoil)

</div>

[![PyTeslaCoil Results Dashboard](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/08_results_tab.png)](docs/screenshots/08_results_tab.png)

## Why I built this

Back when I was at uni studying high-voltage engineering, I built Tesla coils as a hobby and used JavaTC to design and tune my primary and secondary coils, toplaods, and so on. JavaTC is a brilliant tool and it was free, but it was never open source.

Over the years, other high-voltage enthusiasts from uni and elsewhere kept asking me how to fine-tune their coils, and I always pointed them at JavaTC. Eventually I realised there was no open-source equivalent for the Tesla coil hobbyist community, so I decided to build one in Python. That's what PyTeslaCoil is.

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Physics Reference](#physics-reference)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Overview

PyTeslaCoil is a design tool for spark-gap (SGTC) and dual-resonant solid-state (DRSSTC) Tesla coils. It covers the core ground that JavaTC (classictesla.com) has covered for the community since around 2000, but in a modern, all-Python stack with a browser-based UI.

It computes secondary and primary inductance, self-capacitance, coupling coefficient, resonant frequencies, spark-gap behaviour, transformer sizing, and estimated spark length. You can use it as a standalone library in your own scripts and notebooks, or run the full app with live-updating calculations and a 2D coil visualizer.

## Screenshots

### Secondary Coil Design

Enter coil geometry, wire gauge, and winding parameters. Results update live as you type.

[![Secondary Coil Tab](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/01_secondary_tab.png)](docs/screenshots/01_secondary_tab.png)

### Primary Coil Design

Configure flat spiral, helical, or conical primaries with auto-tune to match the secondary frequency.

[![Primary Coil Tab](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/02_primary_tab.png)](docs/screenshots/02_primary_tab.png)

### Coupling Analysis

View the computed coupling coefficient with quality indicators, and auto-adjust primary height to hit a target k.

[![Coupling Tab](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/04_coupling_tab.png)](docs/screenshots/04_coupling_tab.png)

### Spark Gap Configuration

Static and rotary gap parameters with breakdown voltage, BPS, and energy-per-bang calculations.

[![Spark Gap Tab](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/05_spark_gap_tab.png)](docs/screenshots/05_spark_gap_tab.png)

### Results Dashboard

Headline metrics (resonant frequency, coupling, spark length), detailed subsection results, a coil cross-section visualizer, and one-click export to text, JSON, or PDF.

[![Results Dashboard](https://github.com/richie-rk/PyTeslaCoil/raw/main/docs/screenshots/08_results_tab.png)](docs/screenshots/08_results_tab.png)

## Features

- Secondary coil design with solenoid, conical, and inverse conical geometries (Wheeler inductance, Medhurst self-capacitance)
- Primary coil design with flat spiral (pancake), helical, and conical options, including lead inductance correction
- Topload capacitance for toroids (empirical fit) and spheres (exact analytical), with multi-stage stacking
- Coupling coefficient via Neumann mutual inductance using complete elliptic integrals, vectorized with NumPy
- Auto-tune that solves for primary turns to match the secondary resonant frequency using SciPy root-finding
- Static and rotary spark gaps with Paschen breakdown, BPS, dwell time, cap charge fraction, and energy-per-bang
- Transformer sizing for NST, OBIT, MOT, and pole-pig, with resonant and LTR capacitor recommendations
- Spark length estimation using the Freau empirical formula
- 2D coil visualizer rendering a proportional SVG cross-section
- Export to JavaTC-style text, round-trippable JSON, and single-page PDF
- Three built-in demo coils (small SGTC, medium SGTC with rotary gap, compact DRSSTC)
- Library mode so you can import and use the engine with no UI at all
- Dark-themed web UI with live recalculation

## Installation

### Prerequisites

- Python 3.10+ (tested on 3.10 through 3.13)
- pip or uv
- 4GB+ RAM
- Optional: [reportlab](https://pypi.org/project/reportlab/) for PDF export

### Setup

Clone the repository:

```bash
git clone https://github.com/richie-rk/PyTeslaCoil.git
cd PyTeslaCoil
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies (pick one):

```bash
pip install -e ".[dev]"      # development, includes pytest, ruff, mypy
pip install -e ".[dev,pdf]"  # adds PDF export via reportlab
pip install -e .             # runtime only
```

Verify the install:

```bash
python -c "from pyteslacoil import calculate_secondary; print('Engine OK')"
pytest tests/ -q
```

## Usage

### Web UI

Launch the app:

```bash
pyteslacoil
# or
python -m ui.main
```

Then open <http://localhost:8080>. Click **Load Demo** in the header to load a preset (small SGTC, medium SGTC, or DRSSTC).

### Library mode

```python
from pyteslacoil import calculate_secondary
from pyteslacoil.models import SecondaryInput
from pyteslacoil.units import inches_to_meters

secondary = SecondaryInput(
    radius_1=inches_to_meters(2.125),
    radius_2=inches_to_meters(2.125),
    height_1=inches_to_meters(3.0),
    height_2=inches_to_meters(19.0),
    turns=711,
    wire_awg=24,
)
sec_out = calculate_secondary(secondary)

print(f"Inductance:    {sec_out.inductance_mh:.3f} mH")
print(f"Self-cap:      {sec_out.self_capacitance_pf:.2f} pF")
print(f"Resonant freq: {sec_out.resonant_frequency_khz:.2f} kHz")
print(f"Q factor:      {sec_out.q_factor:.0f}")
```

### Loading a preset and exporting

```python
from pyteslacoil.presets import load_preset
from pyteslacoil.export import to_text, to_json
from ui.state import AppState

state = AppState(load_preset("small_sgtc"))
state.recalculate()

print(to_text(state.design, state.outputs))

with open("my_coil.json", "w") as f:
    f.write(to_json(state.design, state.outputs))
```

## Configuration

The UI lets you switch between inches and centimetres from the header dropdown. Internally everything runs in SI (meters, henries, farads, hertz), and conversion happens at the input/output boundary in `pyteslacoil/units.py`.

Built-in presets:

| Preset ID | Description | Secondary | Primary | Gap Type |
| --- | --- | --- | --- | --- |
| `small_sgtc` | Hackaday Mini SGTC | 1.66" OD, 570T AWG32 | Helical, 11T | Static |
| `medium_sgtc` | TCML Reference Coil | 4.25" OD, 711T AWG24 | Flat spiral, 10.8T | Rotary |
| `drsstc` | Compact DRSSTC | 3" OD, 1000T AWG30 | Conical, 6T | Solid-state |

## Testing

```bash
pytest tests/ -v                    # full suite (73 tests)
pytest tests/ -v --cov=pyteslacoil  # with coverage
ruff check pyteslacoil/             # lint
```

## Physics Reference

| Formula | Equation | Source |
| --- | --- | --- |
| Solenoid inductance | `L = (u0 * N^2 * pi * r^2) / (l + 0.9r)` | Wheeler (1928) |
| Flat spiral inductance | `L = (u0 * N^2 * r_avg^2) / (8*r_avg + 11*w)` | Wheeler (1928) |
| Self-capacitance | `C [pF] = H * D [cm]` | Medhurst (1947) |
| Resonant frequency | `f = 1 / (2*pi*sqrt(L*C))` | LC resonance |
| Sphere capacitance | `C = 4*pi*e0*r` | Gauss's law |
| Mutual inductance | `M = u0*sqrt(ab)*((2/k-k)*K(k^2) - (2/k)*E(k^2))` | Maxwell (1873) |
| Coupling coefficient | `k = M / sqrt(L1*L2)` | Definition |
| Skin depth | `d = sqrt(rho / (pi*f*u0))` | EM theory |
| Spark length | `L [in] = 1.7 * sqrt(P [W])` | Freau (empirical) |

Data sources: a 20-point Medhurst L/D lookup interpolated with `numpy.interp`, an AWG 4 to 44 wire table from standard references, and a toroid capacitance fit calibrated against JavaTC and experimental data.

## Contributing

Contributions are welcome, whether it's a bug fix, a new feature, or better physics. Here's the flow I'd like you to follow.

1. Fork the repository and clone your fork locally.
2. Before you write any code, open an issue. If it's a bug, describe how to reproduce it. If it's a feature, explain what you want to add and why. This gives us a place to agree on the approach before any work happens, and it saves you from building something that ends up not fitting the project.
3. Create a branch for your change off `main`.
4. Make your change, and add or update tests where it makes sense. Run `pytest tests/` and `ruff check pyteslacoil/` before you push.
5. Open a pull request and link it to the issue (for example, "Closes #12"). That keeps the bug or feature and the work that fixed it tied together.

If you're not sure whether something is worth doing, open an issue anyway and ask. I'd rather talk it through early than have you spend time on something I can't merge.

## Acknowledgements

- Inspired by [JavaTC](http://classictesla.com) by Bart Anderson, the tool that got me through my own coil builds.
- Physics based on the work of Paul Nicholson (GEOTC/TSSP), R.G. Medhurst, H.A. Wheeler, F.W. Grover, and the wider Tesla coil community.
- Built with [NiceGUI](https://nicegui.io/), [Pydantic](https://docs.pydantic.dev/), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), and [Plotly](https://plotly.com/).

Built as an open-source Python native alternative to JavaTC for the Tesla coil hobbyist community.
