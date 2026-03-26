"""
Molecular structure and vibrational mode visualiser using py3Dmol.

py3Dmol renders 3-D molecular graphics via the 3Dmol.js library loaded from
a CDN — no Jupyter extension install required.

Typical usage after a Psi4 frequency calculation::

    from ir_widget import IRWidget, MolVisualizerWidget

    widget = IRWidget()
    widget.load_from_psi4_wfn(wfn)       # populates atoms + displacements

    vis = MolVisualizerWidget(widget.data)
    vis.view_structure()                  # ball-and-stick model
    vis.view_mode(2)                      # animate mode index 2
    vis.view_orbital('Psi_a_006_6-A.cube')  # MO isosurface (needs cube file)
"""

from __future__ import annotations

import math
import pathlib

import numpy as np


# ── private helpers ──────────────────────────────────────────────────────────

_STICK_R   = 0.20   # stick (bond) cylinder radius, Å
_SPHERE_S  = 0.40   # sphere scale factor for heavy atoms (× VDW radius)
_H_SPHERE  = 0.30   # sphere scale factor for H — slightly smaller than heavy atoms

# ~10% black (each channel = 0.90 × 255 ≈ 230 = 0xe6)
_DEFAULT_BG = "0xe6e6e6"


def _apply_ball_and_stick(view) -> None:
    """
    Apply standard CPK ball-and-stick style.

    Uses Jmol colour scheme (H=white, C=grey, N=blue, O=red, …) for all
    atoms, then overrides H sphere size to be slightly smaller than heavy
    atoms so the model looks proportional.
    """
    view.setStyle({}, {
        "stick":  {"radius": _STICK_R,  "colorscheme": "Jmol"},
        "sphere": {"scale":  _SPHERE_S, "colorscheme": "Jmol"},
    })
    # H: keep CPK white, just reduce sphere size
    view.setStyle({"elem": "H"}, {
        "sphere": {"scale": _H_SPHERE, "color": "white"},
        "stick":  {"radius": _STICK_R, "color": "white"},
    })


def _make_xyz_frame(symbols: list[str], coords: np.ndarray,
                    comment: str = "") -> str:
    """Return a single XYZ-format frame string."""
    lines = [str(len(symbols)), comment]
    for sym, (x, y, z) in zip(symbols, coords):
        lines.append(f"{sym:<3}  {x:12.6f}  {y:12.6f}  {z:12.6f}")
    return "\n".join(lines)


def _make_multiframe_xyz(symbols: list[str], frames: list[np.ndarray]) -> str:
    """Return a multi-frame XYZ string (frames concatenated, no separator)."""
    return "\n".join(
        _make_xyz_frame(symbols, coords, f"frame {i + 1}")
        for i, coords in enumerate(frames)
    )


def _sine_frames(coords0: np.ndarray, disps: np.ndarray,
                 amplitude: float, n_frames: int) -> list[np.ndarray]:
    """Pre-compute one full oscillation cycle of displaced coordinates."""
    return [
        coords0 + amplitude * math.sin(2 * math.pi * i / n_frames) * disps
        for i in range(n_frames)
    ]


def _read_cube(cube_data: "str | pathlib.Path") -> str:
    """Return cube file contents as a string, accepting path or raw string."""
    path = pathlib.Path(cube_data)
    if path.exists():
        return path.read_text()
    # treat as raw string content
    return str(cube_data)


# ── public class ─────────────────────────────────────────────────────────────

class MolVisualizerWidget:
    """
    Molecular structure and vibrational mode visualiser backed by py3Dmol.

    Create from an :class:`~ir_widget.IRWidget` whose data was loaded via
    :meth:`~ir_widget.IRWidget.load_from_psi4_wfn` or
    :meth:`~ir_widget.IRWidget.run_psi4_frequency` (those methods populate
    atom coordinates and normal-mode displacement vectors).

    Parameters
    ----------
    data : dict
        The ``.data`` dict from an ``IRWidget``.

    Examples
    --------
    >>> from ir_widget import IRWidget, MolVisualizerWidget
    >>> widget = IRWidget()
    >>> widget.load_from_psi4_wfn(wfn)
    >>> vis = MolVisualizerWidget(widget.data)
    >>> vis.view_structure()
    >>> vis.view_mode(2)
    >>> vis.view_orbital('Psi_a_006_6-A.cube')
    """

    def __init__(self, data: dict):
        self.data = data

    # ── public view methods ───────────────────────────────────────────────────

    def view_structure(self, width: int = 500, height: int = 400,
                       background: str = _DEFAULT_BG) -> "py3Dmol.view":
        """
        Return a py3Dmol viewer showing a ball-and-stick model of the molecule.

        Parameters
        ----------
        width, height : int
            Viewer dimensions in pixels.
        background : str
            3Dmol.js colour string for the viewer background.
            Defaults to ``'0xb3b3b3'`` (≈30 % black / 70 % white grey)
            so that white hydrogen atoms are visible.

        Returns
        -------
        py3Dmol.view
            Displays automatically when returned from a notebook cell.

        Raises
        ------
        ValueError
            If atom coordinates are not available in the data dict.
        """
        import py3Dmol

        self._require_geometry()
        atoms = self.data["atoms"]
        symbols = [a["symbol"] for a in atoms]
        coords = np.array([[a["x"], a["y"], a["z"]] for a in atoms])

        view = py3Dmol.view(width=width, height=height)
        view.setBackgroundColor(background)
        view.addModel(_make_xyz_frame(symbols, coords), "xyz")
        _apply_ball_and_stick(view)
        view.zoomTo()
        view.render()
        return view

    def view_mode(self, mode_index: int, amplitude: float = 0.5,
                  n_frames: int = 30, width: int = 500,
                  height: int = 400, background: str = _DEFAULT_BG) -> "py3Dmol.view":
        """
        Return a py3Dmol viewer that animates a vibrational normal mode.

        The molecule oscillates along the mode's Cartesian displacement vector
        with a sine-wave envelope.  Animation loops back-and-forth automatically.

        Parameters
        ----------
        mode_index : int
            0-based index into ``data['modes']``.
        amplitude : float
            Maximum displacement scale factor (Å).  0.3–0.8 Å works well.
        n_frames : int
            Frames per oscillation cycle (controls smoothness).
        width, height : int
            Viewer dimensions in pixels.
        background : str
            3Dmol.js colour string for the viewer background.

        Returns
        -------
        py3Dmol.view

        Raises
        ------
        ValueError
            If atom coordinates or displacement vectors are not available.
        IndexError
            If *mode_index* is out of range.
        """
        import py3Dmol

        self._require_geometry()
        self._require_displacements(mode_index)

        atoms = self.data["atoms"]
        mode = self.data["modes"][mode_index]
        symbols = [a["symbol"] for a in atoms]
        coords0 = np.array([[a["x"], a["y"], a["z"]] for a in atoms])
        disps = np.array(mode["displacements"])

        frames = _sine_frames(coords0, disps, amplitude, n_frames)

        view = py3Dmol.view(width=width, height=height)
        view.setBackgroundColor(background)
        view.addModelsAsFrames(_make_multiframe_xyz(symbols, frames), "xyz")
        _apply_ball_and_stick(view)
        view.zoomTo()
        view.animate({"loop": "backAndForth", "reps": 0, "step": 1})
        view.render()

        freq = mode["frequency"]
        sign = "i" if freq < 0 else ""
        print(
            f"Mode {mode['mode']}:  {abs(freq):.1f}{sign} cm⁻¹  "
            f"({n_frames} frames, amplitude={amplitude} Å)"
        )
        return view

    def view_orbital(self, cube_data: "str | pathlib.Path",
                     isovalue: float = 0.02, opacity: float = 0.7,
                     pos_color: str = "blue", neg_color: str = "red",
                     width: int = 500, height: int = 400,
                     background: str = _DEFAULT_BG) -> "py3Dmol.view":
        """
        Show a molecular orbital as dual isosurface lobes from a ``.cube`` file.

        Generate the cube file with ``psi4.cubeprop()`` before calling this::

            psi4.set_options({'cubeprop_tasks': ['orbitals'],
                              'cubeprop_orbitals': [5, 6, 7]})
            psi4.cubeprop(wfn)            # writes e.g. Psi_a_006_6-A.cube
            vis.view_orbital('Psi_a_006_6-A.cube', isovalue=0.02)

        Parameters
        ----------
        cube_data : str or path-like
            Path to a Gaussian ``.cube`` file, **or** its contents as a string.
        isovalue : float
            Isosurface cutoff value (absolute; both ±isovalue lobes are drawn).
        opacity : float
            Lobe transparency (0 = fully transparent, 1 = opaque).
        pos_color, neg_color : str
            3Dmol.js colour strings for the positive and negative lobes.
        width, height : int
            Viewer dimensions in pixels.

        Returns
        -------
        py3Dmol.view
        """
        import py3Dmol

        cube_str = _read_cube(cube_data)

        view = py3Dmol.view(width=width, height=height)
        view.setBackgroundColor(background)

        # Add the molecule from the cube header (first 6 lines are metadata;
        # py3Dmol/3Dmol.js parses the geometry embedded in the cube format)
        view.addModel(cube_str, "cube")
        _apply_ball_and_stick(view)

        # Positive lobe
        view.addVolumetricData(
            cube_str, "cube",
            {"isoval":  isovalue, "color": pos_color, "opacity": opacity},
        )
        # Negative lobe
        view.addVolumetricData(
            cube_str, "cube",
            {"isoval": -isovalue, "color": neg_color, "opacity": opacity},
        )
        view.zoomTo()
        return view

    # ── helpers ───────────────────────────────────────────────────────────────

    def _require_geometry(self):
        if "atoms" not in self.data or not self.data["atoms"]:
            raise ValueError(
                "Atom coordinates are not available.\n"
                "Load data with IRWidget.load_from_psi4_wfn() or "
                "IRWidget.run_psi4_frequency() to obtain geometry."
            )

    def _require_displacements(self, mode_index: int):
        modes = self.data.get("modes", [])
        if mode_index < 0 or mode_index >= len(modes):
            raise IndexError(
                f"mode_index {mode_index} is out of range "
                f"(0–{len(modes) - 1})."
            )
        if "displacements" not in modes[mode_index]:
            raise ValueError(
                f"Mode {mode_index} has no displacement vectors.\n"
                "Load data with IRWidget.load_from_psi4_wfn() or "
                "IRWidget.run_psi4_frequency() to obtain normal modes."
            )
