"""
Molecular structure and vibrational mode visualiser using nglview.

Typical usage after a Psi4 frequency calculation::

    from ir_widget import IRWidget, MolVisualizerWidget

    widget = IRWidget()
    widget.load_from_psi4_wfn(wfn)       # populates atoms + displacements

    vis = MolVisualizerWidget(widget.data)
    vis.view_structure()                  # ball-and-stick model
    vis.view_mode(2)                      # animate mode index 2
"""

import numpy as np

from nglview.base_adaptor import Structure, Trajectory


# ── private helpers ──────────────────────────────────────────────────────────

def _make_pdb(symbols: list, coords: np.ndarray) -> str:
    """Return a minimal PDB string for *symbols* at *coords* (Å)."""
    lines = ["REMARK  MolVisualizerWidget"]
    for i, (sym, (x, y, z)) in enumerate(zip(symbols, coords), start=1):
        # Atom name: right-pad to 4 chars; element symbol right-justified in cols 77-78
        name = f" {sym:<3}" if len(sym) == 1 else f"{sym:<4}"
        lines.append(
            f"HETATM{i:5d} {name} LIG A   1    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {sym:>2}  "
        )
    lines.append("END")
    return "\n".join(lines)


class _VibrationalTrajectory(Structure, Trajectory):
    """
    Combined nglview Structure + Trajectory for a single vibrational normal mode.

    Frames are computed as a full sine-wave oscillation::

        r(t) = r₀ + amplitude · sin(2π · t / n_frames) · displacement

    Parameters
    ----------
    atoms : list of dict
        ``[{"symbol": str, "x": float, "y": float, "z": float}, ...]`` in Å.
    displacements : list of list
        Per-atom Cartesian displacement vectors ``[[dx, dy, dz], ...]`` in Å
        (normalised un-mass-weighted, from ``vibinfo['x']``).
    amplitude : float
        Maximum displacement scaling factor (Å).
    n_frames : int
        Number of animation frames per oscillation cycle.
    """

    def __init__(self, atoms, displacements, amplitude=0.5, n_frames=20):
        Structure.__init__(self)
        Trajectory.__init__(self)
        self.ext = "pdb"
        self.params = {}

        self._symbols = [a["symbol"] for a in atoms]
        coords0 = np.array([[a["x"], a["y"], a["z"]] for a in atoms], dtype=float)
        disps = np.array(displacements, dtype=float)  # (n_atoms, 3)

        # Pre-compute one full oscillation cycle
        self._frames = [
            coords0 + amplitude * np.sin(2 * np.pi * i / n_frames) * disps
            for i in range(n_frames)
        ]
        self._structure_string = _make_pdb(self._symbols, coords0)

    def get_structure_string(self) -> str:
        return self._structure_string

    def get_coordinates(self, index: int) -> np.ndarray:
        """Return (n_atoms, 3) coordinate array for frame *index* (Å)."""
        return self._frames[index % len(self._frames)]

    @property
    def n_frames(self) -> int:
        return len(self._frames)


# ── public class ─────────────────────────────────────────────────────────────

class MolVisualizerWidget:
    """
    Molecular structure and vibrational mode visualiser backed by nglview.

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
    >>> widget.load_from_psi4_wfn(wfn)          # after psi4.frequency(..., return_wfn=True)
    >>> vis = MolVisualizerWidget(widget.data)
    >>> vis.view_structure()                      # display in a notebook cell
    >>> vis.view_mode(2)                          # animate mode index 2 (0-based)
    """

    def __init__(self, data: dict):
        self.data = data

    # ── public view methods ───────────────────────────────────────────────────

    def view_structure(self, **kwargs):
        """
        Return an nglview widget showing a ball-and-stick model of the molecule.

        Parameters
        ----------
        **kwargs
            Passed to ``nglview.NGLWidget.add_ball_and_stick()``.

        Returns
        -------
        nglview.NGLWidget

        Raises
        ------
        ValueError
            If atom coordinates are not available in the data dict.
        """
        import nglview as nv

        self._require_geometry()

        atoms = self.data["atoms"]
        symbols = [a["symbol"] for a in atoms]
        coords = np.array([[a["x"], a["y"], a["z"]] for a in atoms])

        structure = nv.TextStructure(_make_pdb(symbols, coords), ext="pdb")
        view = nv.NGLWidget(structure)
        view.clear_representations()
        view.add_ball_and_stick(**kwargs)
        return view

    def view_mode(self, mode_index: int, amplitude: float = 0.5,
                  n_frames: int = 20, **kwargs):
        """
        Return an nglview widget that animates a vibrational normal mode.

        The molecule oscillates along the mode's Cartesian displacement vector
        with a sine-wave envelope. Press **Play** in the widget controls to start
        the animation.

        Parameters
        ----------
        mode_index : int
            0-based index into ``data['modes']``.
        amplitude : float
            Maximum displacement scale factor (Å).  Larger values exaggerate
            the motion for visibility; 0.3–0.8 Å works well for most modes.
        n_frames : int
            Frames per oscillation cycle (controls animation smoothness).
        **kwargs
            Passed to ``nglview.NGLWidget.add_ball_and_stick()``.

        Returns
        -------
        nglview.NGLWidget

        Raises
        ------
        ValueError
            If atom coordinates or displacement vectors are not available.
        IndexError
            If *mode_index* is out of range.
        """
        import nglview as nv

        self._require_geometry()
        self._require_displacements(mode_index)

        mode = self.data["modes"][mode_index]
        traj = _VibrationalTrajectory(
            self.data["atoms"], mode["displacements"], amplitude, n_frames
        )

        view = nv.NGLWidget(traj)
        view.clear_representations()
        view.add_ball_and_stick(**kwargs)
        view.player.parameters = dict(delay=60, step=1)

        freq = mode["frequency"]
        sign = "i" if freq < 0 else ""
        print(
            f"Mode {mode['mode']}:  {abs(freq):.1f}{sign} cm⁻¹  "
            f"({n_frames} frames, amplitude={amplitude} Å) — press ▶ to animate"
        )
        return view

    def view_orbital(self, cube_data=None, isovalue: float = 0.02,
                     opacity: float = 0.7, **kwargs):
        """
        Show a molecular orbital as a pair of isosurface lobes (future feature).

        .. note::
            **Not yet implemented.**  Planned for a future release.

        When implemented, this method will accept a ``.cube`` file (path or
        string) produced by ``psi4.cubeprop()`` and render the positive and
        negative isosurface lobes using nglview's ``SurfaceRepresentation``.

        Example future workflow::

            psi4.set_options({'cubeprop_tasks': ['orbitals'],
                              'cubeprop_orbitals': [5, 6, 7]})
            psi4.cubeprop(wfn)
            vis.view_orbital('Psi_a_006_6-A.cube', isovalue=0.02)

        Parameters
        ----------
        cube_data : str or path-like
            Path to a Gaussian `.cube` file, or the file contents as a string.
        isovalue : float
            Isosurface cutoff value.
        opacity : float
            Lobe transparency (0 = fully transparent, 1 = opaque).

        Raises
        ------
        NotImplementedError
            Always — this method is a planned stub.
        """
        raise NotImplementedError(
            "Molecular orbital visualisation is not yet implemented.\n"
            "Planned workflow:\n"
            "  1. psi4.set_options({'cubeprop_tasks': ['orbitals']})\n"
            "  2. psi4.cubeprop(wfn)  # writes .cube files\n"
            "  3. vis.view_orbital('Psi_a_006_6-A.cube', isovalue=0.02)"
        )

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
