"""Shared fixtures for the ir_widget test suite.

Centralizing the canonical H2O sample data here (rather than hand-copying the
frequency/intensity numbers into every test file) keeps the test suite in
sync with ``examples/sample_data.py`` — the same module the docs point users
to — and means the numbers only need to be updated in one place.
"""

import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
if str(_EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES_DIR))

from sample_data import get_sample_data  # noqa: E402  (path must be set first)


@pytest.fixture
def h2o_sample():
    """Canonical H2O frequency/intensity data from ``examples/sample_data.py``."""
    return get_sample_data("H2O")


@pytest.fixture
def water_data(h2o_sample):
    """Full IRWidget-shaped H2O data (atoms + per-mode displacements).

    Frequencies/intensities come from ``h2o_sample`` so they can't drift from
    ``examples/sample_data.py``; the atom geometry and displacement vectors
    are hand-picked, illustrative values not present in ``sample_data.py``.
    """
    freqs = h2o_sample["frequencies"]
    intensities = h2o_sample["intensities"]
    displacements = [
        [[0.0, 0.0, 0.1], [0.1, 0.0, 0.0], [-0.1, 0.1, 0.0]],
        [[0.0, 0.05, 0.0], [0.05, 0.0, 0.0], [0.0, 0.0, 0.05]],
        [[0.0, 0.0, 0.05], [0.0, 0.05, 0.0], [0.05, 0.0, 0.0]],
    ]
    return {
        "formula": h2o_sample["formula"],
        "n_modes": len(freqs),
        "atoms": [
            {"symbol": "O", "x": 0.0, "y": 0.0, "z": 0.0},
            {"symbol": "H", "x": 0.96, "y": 0.0, "z": 0.0},
            {"symbol": "H", "x": -0.24, "y": 0.93, "z": 0.0},
        ],
        "modes": [
            {
                "mode": i + 1,
                "frequency": float(freq),
                "intensity": float(intensity),
                "displacements": disp,
            }
            for i, (freq, intensity, disp) in enumerate(
                zip(freqs, intensities, displacements)
            )
        ],
    }
