"""Tests for ``ir_widget.mol_visualizer``."""

import numpy as np
import pytest

from ir_widget.mol_visualizer import (
    MolVisualizerWidget,
    ModeViewWidget,
    OrbitalViewWidget,
    LinkedViewWidget,
    _AX_TOP,
    _AX_RIGHT,
    _LOC_NAMES,
    _best_inset_loc,
    _cosine_frames,
    _inset_bbox,
    _inset_css,
    _make_multiframe_xyz,
    _make_xyz_frame,
    _read_cube,
    _validate_loc,
)


# ── XYZ frame helpers ────────────────────────────────────────────────────────

def test_make_xyz_frame_format():
    symbols = ["O", "H", "H"]
    coords = np.array([[0.0, 0.0, 0.0], [0.96, 0.0, 0.0], [-0.24, 0.93, 0.0]])

    frame = _make_xyz_frame(symbols, coords, comment="water")
    lines = frame.split("\n")

    assert lines[0] == "3"
    assert lines[1] == "water"
    assert len(lines) == 5
    assert lines[2].split()[0] == "O"
    assert lines[3].split()[0] == "H"


def test_make_multiframe_xyz_concatenates_and_labels_frames():
    symbols = ["H", "H"]
    frames = [
        np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]]),
        np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.80]]),
    ]

    xyz = _make_multiframe_xyz(symbols, frames)
    lines = xyz.split("\n")

    # Each frame is 2 header lines + 2 atom lines = 4 lines.
    assert len(lines) == 8
    assert lines[1] == "frame 1"
    assert lines[5] == "frame 2"


def test_cosine_frames_oscillation_envelope():
    coords0 = np.zeros((2, 3))
    disps = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])

    frames = _cosine_frames(coords0, disps, amplitude=0.5, n_frames=8)

    assert len(frames) == 8
    # frame 0: cos(0) = 1 -> full +amplitude displacement
    np.testing.assert_allclose(frames[0], coords0 + 0.5 * disps)
    # frame n/2: cos(pi) = -1 -> full -amplitude displacement
    np.testing.assert_allclose(frames[4], coords0 - 0.5 * disps, atol=1e-10)


# ── inset placement helpers ──────────────────────────────────────────────────

@pytest.mark.parametrize("loc,expected", [
    ("upper right", "upper right"),
    (" Upper Right ", "upper right"),
    (1, "upper right"),
    (0, "best"),
])
def test_validate_loc_normalizes(loc, expected):
    assert _validate_loc(loc) == expected


def test_validate_loc_rejects_unknown_string():
    with pytest.raises(ValueError):
        _validate_loc("top left")


def test_validate_loc_rejects_unknown_int_code():
    with pytest.raises(ValueError):
        _validate_loc(99)


def test_inset_css_upper_right():
    css = _inset_css("upper right", W=800, H=480, iw=300, ih=250)
    assert css == "top:10px;right:10px;"


def test_inset_bbox_upper_left():
    bbox = _inset_bbox("upper left", W=800, H=480, iw=300, ih=250)
    assert bbox == (10, 10, 310, 260)


def test_inset_css_center_is_centered_in_container():
    css = _inset_css("center", W=800, H=480, iw=300, ih=250)
    assert css == "top:115px;left:250px;"


def test_best_inset_loc_avoids_the_only_occupied_corner():
    # A single envelope point placed exactly at the top-right corner of the
    # plot axes. For these W/H/iw/ih values that pixel falls only inside the
    # "upper right" inset bbox and none of the others, so the heuristic must
    # not choose "upper right" (it would overlap the one bit of spectrum ink).
    W, H, iw, ih = 800, 480, 300, 250
    x_min, x_max = 0.0, 4000.0

    loc = _best_inset_loc(
        x_pts=np.array([x_max]),
        y_pts_norm=np.array([100.0]),
        freqs=np.array([]),
        intensities_norm=np.array([]),
        x_min=x_min, x_max=x_max,
        W=W, H=H, iw=iw, ih=ih,
    )

    assert loc != "upper right"
    assert loc in (_LOC_NAMES - {"best"})


# ── cube file reading ────────────────────────────────────────────────────────

def test_read_cube_from_existing_path(tmp_path):
    cube_file = tmp_path / "orbital.cube"
    cube_file.write_text("cube contents here\n")

    assert _read_cube(cube_file) == "cube contents here\n"


def test_read_cube_from_raw_string_when_not_a_path():
    raw = "not a real path, just raw cube text"
    assert _read_cube(raw) == raw


# ── MolVisualizerWidget ───────────────────────────────────────────────────────
# `water_data` lives in conftest.py so it's shared with test_widget.py and
# stays in sync with examples/sample_data.py.

@pytest.fixture
def geometry_only_data(water_data):
    """Atoms present, but the one mode has no per-mode displacement vector."""
    mode = water_data["modes"][0]
    return {
        "formula": water_data["formula"],
        "n_modes": 1,
        "atoms": water_data["atoms"],
        "modes": [
            {"mode": mode["mode"], "frequency": mode["frequency"], "intensity": mode["intensity"]},
        ],
    }


@pytest.fixture
def no_geometry_data(water_data):
    """No atom coordinates — just formula + a single mode, no displacements."""
    mode = water_data["modes"][0]
    return {
        "formula": water_data["formula"],
        "n_modes": 1,
        "modes": [dict(mode)],
    }


def test_require_geometry_raises_without_atoms(no_geometry_data):
    vis = MolVisualizerWidget(no_geometry_data)
    with pytest.raises(ValueError, match="Atom coordinates"):
        vis.view_structure()


def test_view_structure_returns_py3dmol_view(water_data):
    vis = MolVisualizerWidget(water_data)
    view = vis.view_structure(width=300, height=200)

    # NOTE: py3Dmol exposes no structured introspection API (no "what models
    # are loaded" / "is this animating" query) — its _make_html() private
    # method returns the raw accumulated JS string. Asserting on substrings
    # of that string is a real, accepted coupling to py3Dmol's internals;
    # a future py3Dmol release could reformat this HTML and break these
    # assertions with no actual regression in MolVisualizerWidget itself.
    html = view._make_html()
    assert "addModel" in html
    assert "300px" in html and "200px" in html


def test_view_mode_animates_and_prints_summary(water_data, capsys):
    vis = MolVisualizerWidget(water_data)
    view = vis.view_mode(0, amplitude=0.3, n_frames=10)

    html = view._make_html()
    assert "addModelsAsFrames" in html
    assert "animate" in html

    printed = capsys.readouterr().out
    assert "Mode 1" in printed
    assert "1595.0" in printed


def test_view_mode_out_of_range_raises_index_error(water_data):
    vis = MolVisualizerWidget(water_data)
    with pytest.raises(IndexError):
        vis.view_mode(99)


def test_view_mode_without_displacements_raises(geometry_only_data):
    vis = MolVisualizerWidget(geometry_only_data)
    with pytest.raises(ValueError, match="displacement"):
        vis.view_mode(0)


def test_view_orbital_builds_dual_isosurfaces(water_data):
    vis = MolVisualizerWidget(water_data)

    # _read_cube() accepts raw cube-file content directly (see
    # test_read_cube_from_raw_string_when_not_a_path above), so there's no
    # need to round-trip trivial fake content through a real temp file.
    view = vis.view_orbital(
        "FAKE CUBE DATA\n", isovalue=0.05, pos_color="green", neg_color="orange",
    )

    html = view._make_html()
    assert html.count("addVolumetricData") == 2
    assert "0.05" in html
    assert "green" in html and "orange" in html


def test_view_linked_returns_widget_with_expected_traits(water_data):
    vis = MolVisualizerWidget(water_data)
    widget = vis.view_linked(width=800, height=480, loc="upper left")

    assert isinstance(widget, LinkedViewWidget)
    assert widget.mode_index == 0
    assert len(widget._mol_frames) == 3
    assert len(widget._mode_labels) == 3
    assert widget._formula == "H2O"
    assert widget._inset_css_str == "top:10px;left:10px;"


def test_view_linked_auto_x_range_pads_by_200_wavenumbers(water_data):
    vis = MolVisualizerWidget(water_data)
    widget = vis.view_linked()

    freqs = [m["frequency"] for m in water_data["modes"]]
    assert widget._x_min == pytest.approx(max(0.0, min(freqs) - 200))
    assert widget._x_max == pytest.approx(max(freqs) + 200)


def test_view_mode_selector_widget(water_data):
    vis = MolVisualizerWidget(water_data)
    widget = vis.view_mode_selector(amplitude=0.2, n_frames=5)

    assert isinstance(widget, ModeViewWidget)
    assert len(widget._mol_frames) == 3
    assert widget._mode_labels[0].startswith("Mode 1")


def test_view_orbital_selector_default_index_and_labels_from_homo(water_data):
    vis = MolVisualizerWidget(water_data)
    # Raw strings behave identically to files here (see _read_cube), so no
    # temp files are needed for these trivial fake cube contents.
    cube_files = [f"CUBE {i}\n" for i in range(5)]

    widget = vis.view_orbital_selector(cube_files, homo_index=2)

    assert isinstance(widget, OrbitalViewWidget)
    assert widget.orbital_index == 2
    assert widget._orbital_labels == [
        "HOMO−2", "HOMO−1", "HOMO", "LUMO", "LUMO+1",
    ]
    assert widget._cube_string == "CUBE 2\n"


def test_view_orbital_selector_without_homo_index_uses_generic_labels(water_data):
    vis = MolVisualizerWidget(water_data)
    cube_files = [f"CUBE {i}\n" for i in range(3)]

    widget = vis.view_orbital_selector(cube_files)

    assert widget.orbital_index == 0
    assert widget._orbital_labels == ["Orbital 1", "Orbital 2", "Orbital 3"]


def test_view_orbital_selector_rejects_empty_cube_list(water_data):
    vis = MolVisualizerWidget(water_data)
    with pytest.raises(ValueError):
        vis.view_orbital_selector([])


# ── OrbitalViewWidget observer ────────────────────────────────────────────────

def test_orbital_index_change_swaps_cube_string():
    widget = OrbitalViewWidget(
        orbital_index=0, _cube_string="AAA", _orbital_labels=["a", "b"],
    )
    widget._all_cube_strings = ["AAA", "BBB"]

    widget.orbital_index = 1

    assert widget._cube_string == "BBB"
