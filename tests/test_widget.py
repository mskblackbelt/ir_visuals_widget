"""Tests for ``ir_widget.widget.IRWidget``."""

import sys

import numpy as np
import pytest

from ir_widget import IRWidget


# ── load_data() / _prepare_data() ────────────────────────────────────────────

def test_load_data_basic(h2o_sample):
    freqs, intensities = h2o_sample["frequencies"], h2o_sample["intensities"]
    widget = IRWidget()
    widget.load_data(freqs.tolist(), intensities.tolist(), formula=h2o_sample["formula"])

    assert widget.error_message == ""
    assert widget.data["formula"] == "H2O"
    assert widget.data["n_modes"] == 3
    assert widget.data["modes"] == [
        {"mode": i + 1, "frequency": float(f), "intensity": float(inten)}
        for i, (f, inten) in enumerate(zip(freqs, intensities))
    ]


def test_load_data_without_intensities_defaults_to_ones():
    widget = IRWidget()
    widget.load_data([1000.0, 2000.0])

    assert [m["intensity"] for m in widget.data["modes"]] == [1.0, 1.0]


def test_load_data_pads_short_intensities_with_zero():
    widget = IRWidget()
    widget.load_data([1000.0, 2000.0, 3000.0], [10.0])

    assert [m["intensity"] for m in widget.data["modes"]] == [10.0, 0.0, 0.0]


def test_load_data_truncates_long_intensities():
    widget = IRWidget()
    widget.load_data([1000.0, 2000.0], [10.0, 20.0, 30.0])

    assert [m["intensity"] for m in widget.data["modes"]] == [10.0, 20.0]


def test_prepare_data_includes_atoms_only_when_provided():
    widget = IRWidget()
    widget.load_data([1000.0])
    assert "atoms" not in widget.data

    data_with_atoms = widget._prepare_data(
        np.array([1000.0]), None, "H2",
        atoms=[{"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.0}],
    )
    assert data_with_atoms["atoms"] == [{"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.0}]


def test_prepare_data_includes_displacements_only_when_provided():
    widget = IRWidget()
    data = widget._prepare_data(
        np.array([1000.0, 2000.0]), None, "H2",
        normal_modes=[[[0.0, 0.0, 0.1]]],
    )
    assert data["modes"][0]["displacements"] == [[0.0, 0.0, 0.1]]
    assert "displacements" not in data["modes"][1]


# ── formula generation ───────────────────────────────────────────────────────

@pytest.mark.parametrize("symbols,expected", [
    (["O", "H", "H"], "H2O"),
    (["C", "H", "H", "H", "H"], "CH4"),
    (["N", "H", "H", "H"], "H3N"),
    (["C"] * 6 + ["H"] * 6, "C6H6"),
    (["C"] * 3 + ["H"] * 6 + ["O"], "C3H6O"),
])
def test_generate_formula_from_symbols(symbols, expected):
    widget = IRWidget()
    assert widget._generate_formula_from_symbols(symbols) == expected


def test_generate_formula_from_atomic_numbers():
    widget = IRWidget()
    # O, H, H
    assert widget._generate_formula([8, 1, 1]) == "H2O"


# ── load_file() via cclib ────────────────────────────────────────────────────

class _FakeParser:
    """Stand-in for a parsed cclib.data.ccData object."""

    def __init__(self, vibfreqs=None, vibirs=None, atomnos=None):
        if vibfreqs is not None:
            self.vibfreqs = vibfreqs
        if vibirs is not None:
            self.vibirs = vibirs
        if atomnos is not None:
            self.atomnos = atomnos


def test_load_file_parses_frequencies_intensities_and_formula(monkeypatch, h2o_sample):
    fake = _FakeParser(
        vibfreqs=h2o_sample["frequencies"],
        vibirs=h2o_sample["intensities"],
        atomnos=np.array([8, 1, 1]),
    )
    monkeypatch.setattr("cclib.io.ccread", lambda path: fake)

    widget = IRWidget()
    widget.load_file("water.log")

    assert widget.error_message == ""
    assert widget.data["formula"] == "H2O"
    assert widget.data["n_modes"] == 3


def test_load_file_reports_unparseable_file(monkeypatch):
    monkeypatch.setattr("cclib.io.ccread", lambda path: None)

    widget = IRWidget()
    widget.load_file("garbage.log")

    assert "Unable to parse file" in widget.error_message
    assert widget.data == {}


def test_load_file_reports_missing_vibrational_data(monkeypatch):
    monkeypatch.setattr("cclib.io.ccread", lambda path: _FakeParser())

    widget = IRWidget()
    widget.load_file("no_freq.log")

    assert "No vibrational frequency data" in widget.error_message
    assert widget.data == {}


def test_load_file_reports_cclib_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "cclib", None)

    widget = IRWidget()
    widget.load_file("anything.log")

    assert "cclib not installed" in widget.error_message
    assert widget.data == {}


def test_load_file_reports_unexpected_exception(monkeypatch):
    def _boom(path):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr("cclib.io.ccread", _boom)

    widget = IRWidget()
    widget.load_file("anything.log")

    assert "disk on fire" in widget.error_message
    assert widget.data == {}


def test_file_path_change_triggers_load(monkeypatch):
    calls = []
    widget = IRWidget()
    monkeypatch.setattr(widget, "load_file", lambda path: calls.append(path))

    widget.file_path = "molecule.out"

    assert calls == ["molecule.out"]


def test_init_with_file_path_loads_immediately(monkeypatch):
    fake = _FakeParser(vibfreqs=np.array([1000.0]))
    monkeypatch.setattr("cclib.io.ccread", lambda path: fake)

    widget = IRWidget(file_path="molecule.out")

    assert widget.file_path == "molecule.out"
    assert widget.data["n_modes"] == 1


# ── traits / validation ──────────────────────────────────────────────────────

def test_default_traits():
    widget = IRWidget()
    assert widget.data == {}
    assert widget.error_message == ""
    assert widget.show_table is True
    assert widget.show_plot is True
    assert widget.broadening == "lorentzian"
    assert widget.fwhm == 15.0
    assert widget.x_min == 400.0
    assert widget.x_max == 4000.0


def test_broadening_rejects_invalid_value():
    import traitlets

    widget = IRWidget()
    with pytest.raises(traitlets.TraitError):
        widget.broadening = "not-a-real-mode"


# ── Psi4 integration ──────────────────────────────────────────────────────────

def test_load_from_psi4_wfn_reports_import_error_when_psi4_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, "psi4", None)

    widget = IRWidget()
    widget.load_from_psi4_wfn(wfn=object())

    assert "psi4 not available" in widget.error_message


def test_run_psi4_frequency_reports_import_error_when_psi4_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, "psi4", None)

    widget = IRWidget()
    widget.run_psi4_frequency(geometry="H\nH 1 0.74", method_basis="hf/sto-3g")

    assert "psi4 not available" in widget.error_message


@pytest.mark.slow
def test_run_psi4_frequency_h2_hf_sto3g(tmp_path):
    """End-to-end check against a real (tiny, fast) Psi4 calculation.

    H2 is homonuclear, so IR intensity should be ~0 by symmetry, and being
    diatomic it has exactly one vibrational mode after projecting out
    translations/rotations.
    """
    pytest.importorskip("psi4")

    widget = IRWidget()
    widget.run_psi4_frequency(
        geometry="H\nH 1 0.74",
        method_basis="hf/sto-3g",
        memory="500 MB",
        psi4_output_file=str(tmp_path / "psi4_output.dat"),
    )

    assert widget.error_message == ""
    assert widget.data["formula"] == "H2"
    assert widget.data["n_modes"] == 1

    mode = widget.data["modes"][0]
    assert mode["frequency"] == pytest.approx(5040.0, abs=5.0)
    assert mode["intensity"] == pytest.approx(0.0, abs=1e-3)

    atoms = widget.data["atoms"]
    assert [a["symbol"] for a in atoms] == ["H", "H"]
    bond_length = abs(atoms[0]["z"] - atoms[1]["z"])
    assert bond_length == pytest.approx(0.74, abs=1e-2)

    displacements = np.array(mode["displacements"])
    assert displacements.shape == (2, 3)
    # The two H atoms should move along z in opposite directions.
    assert displacements[0][2] == pytest.approx(-displacements[1][2], abs=1e-6)
