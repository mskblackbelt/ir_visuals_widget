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

import html as _html_mod
import math
import pathlib
import re

import numpy as np


def _make_iframe_html(view) -> str:
    """
    Wrap the py3Dmol viewer HTML in an ``<iframe srcdoc="...">`` for Marimo.

    Marimo's ``renderHTML`` pipeline (``RenderHTML.tsx``) parses HTML with
    ``html-react-parser``.  It has two relevant behaviours:

    * **Inline ``<script>`` blocks are silently ignored.**  Only
      ``<script src="...">`` tags are processed (injected into
      ``document.head``).  py3Dmol generates a large inline ``<script>``
      containing the ``loadScriptAsync`` bootstrapper — this is never
      executed, so 3Dmol.js never loads, and the pink "failed to load"
      warning paragraph remains.

    * **``<iframe>`` elements are rendered as real DOM iframes** via
      ``dangerouslySetInnerHTML`` (``replaceValidIframes`` in
      ``RenderHTML.tsx``).  Inside an ``srcdoc`` iframe the browser creates a
      fresh browsing context where all inline scripts execute normally and
      the CDN ``loadScriptAsync`` pattern works without restriction.
    """
    raw_html = view._make_html()

    # Extract viewer dimensions from the generated div style
    w_match = re.search(r"width:\s*(\d+)px", raw_html)
    h_match = re.search(r"height:\s*(\d+)px", raw_html)
    width  = int(w_match.group(1)) if w_match else 640
    height = int(h_match.group(1)) if h_match else 480

    # Escape HTML for use as an attribute value (double-quote delimited)
    srcdoc = _html_mod.escape(raw_html, quote=True)

    return (
        f'<iframe srcdoc="{srcdoc}" '
        f'width="{width}" height="{height}" '
        f'style="border:none;" frameborder="0"></iframe>'
    )


def _display_view(view):
    """
    Return a display-ready object for the current notebook environment.

    - **Marimo**: wraps the viewer in an ``<iframe srcdoc>`` so that the
      py3Dmol inline scripts and CDN loading work inside the iframe's
      own browsing context (Marimo ignores inline scripts in ``mo.Html``).
    - **Jupyter / IPython**: returns the ``py3Dmol.view`` object directly;
      Jupyter calls ``_repr_html_`` which fires ``publish_display_data``.
    """
    try:
        import marimo as _mo
        if _mo.running_in_notebook():
            return _mo.Html(_make_iframe_html(view))
    except Exception:
        pass
    return view


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


def _cosine_frames(coords0: np.ndarray, disps: np.ndarray,
                   amplitude: float, n_frames: int) -> list[np.ndarray]:
    """
    Pre-compute one full oscillation cycle using a cosine envelope.

    Using cosine (instead of sine) places the loop wrap-around at the
    maximum displacement where the instantaneous velocity is zero, so the
    jump from the last frame back to the first is nearly imperceptible and
    the animation loops smoothly without the stutter that ``backAndForth``
    mode produces at its turnaround points.

      frame 0       → +amplitude  (maximum positive displacement)
      frame n/4     → equilibrium (moving toward negative)
      frame n/2     → −amplitude  (maximum negative displacement)
      frame 3n/4    → equilibrium (moving toward positive)
      frame n−1     → ≈ +amplitude (one step before frame 0)

    The step from frame n−1 to frame 0 is
    ``amplitude × (1 − cos(2π/n))``, which for n ≥ 30 is < 1 % of the
    full displacement range — visually seamless.
    """
    return [
        coords0 + amplitude * math.cos(2 * math.pi * i / n_frames) * disps
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
        return _display_view(view)

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

        frames = _cosine_frames(coords0, disps, amplitude, n_frames)

        view = py3Dmol.view(width=width, height=height)
        view.setBackgroundColor(background)
        view.addModelsAsFrames(_make_multiframe_xyz(symbols, frames), "xyz")
        _apply_ball_and_stick(view)
        view.zoomTo()
        view.animate({"loop": "forward", "reps": 0, "step": 1})
        view.render()

        freq = mode["frequency"]
        sign = "i" if freq < 0 else ""
        print(
            f"Mode {mode['mode']}:  {abs(freq):.1f}{sign} cm⁻¹  "
            f"({n_frames} frames, amplitude={amplitude} Å)"
        )
        return _display_view(view)

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
        return _display_view(view)

    def view_linked(
        self,
        amplitude: float = 0.5,
        n_frames: int = 30,
        fwhm: float = 15.0,
        x_min: float | None = None,
        x_max: float | None = None,
        width: int = 960,
        height: int = 480,
        inset_width: int = 300,
        inset_height: int = 250,
        inset_pos: str = "top-right",
        background: str = _DEFAULT_BG,
    ):
        """
        Display a linked view for Jupyter: IR spectrum with an animated
        molecular viewer inset.

        A dropdown selects the vibrational mode.  The spectrum panel shows the
        Lorentzian-broadened envelope plus stick spectrum; the selected mode's
        stick is highlighted in red.  The molecular viewer sits as an inset
        over the spectrum and animates the selected mode.

        Parameters
        ----------
        amplitude : float
            Maximum vibrational displacement amplitude in Å.
        n_frames : int
            Animation frames per oscillation cycle.
        fwhm : float
            Full-width at half-maximum for Lorentzian broadening (cm⁻¹).
        x_min, x_max : float, optional
            Wavenumber axis limits.  Default: auto (±200 cm⁻¹ from data range).
        width, height : int
            Pixel dimensions of the overall panel (spectrum background).
        inset_width, inset_height : int
            Pixel dimensions of the molecule viewer inset.
        inset_pos : {"top-right", "top-left", "bottom-right", "bottom-left"}
            Corner in which to place the molecule inset.
        background : str
            3Dmol.js background colour string.  Use ``"transparent"`` for a
            fully transparent molecule background (requires WebGL alpha support).

        Returns
        -------
        ipywidgets.VBox
            Combined widget ready to display in a Jupyter cell.
        """
        import base64
        import io

        import ipywidgets as widgets
        import matplotlib.pyplot as plt
        import py3Dmol
        from IPython.display import HTML as ipy_HTML
        from IPython.display import display as ipy_display

        self._require_geometry()

        modes = self.data["modes"]
        freqs = np.array([m["frequency"] for m in modes])
        intensities = np.array([m["intensity"] for m in modes])
        max_intensity = intensities.max() if intensities.max() > 0 else 1.0

        _x_min = float(max(0.0, freqs.min() - 200)) if x_min is None else x_min
        _x_max = float(freqs.max() + 200) if x_max is None else x_max

        # Precompute Lorentzian envelope once
        x_pts = np.linspace(_x_min, _x_max, 2000)
        gamma = fwhm / 2.0
        y_pts = np.zeros_like(x_pts)
        for f, I in zip(freqs, intensities):
            y_pts += I * gamma**2 / ((x_pts - f)**2 + gamma**2)
        y_max = y_pts.max() if y_pts.max() > 0 else 1.0

        # CSS for the four inset corner positions (20 px padding from edges)
        _inset_css = {
            "top-right":    "top:20px;right:20px;",
            "top-left":     "top:20px;left:20px;",
            "bottom-right": "bottom:20px;right:20px;",
            "bottom-left":  "bottom:20px;left:20px;",
        }
        inset_edge = _inset_css.get(inset_pos, _inset_css["top-right"])

        # ── dropdown ─────────────────────────────────────────────────────────
        options = [
            (
                f"Mode {m['mode']}: {m['frequency']:.1f} cm⁻¹"
                f"  ({m['intensity']:.1f} km/mol)",
                i,
            )
            for i, m in enumerate(modes)
        ]
        dropdown = widgets.Dropdown(
            options=options,
            description="Mode:",
            layout=widgets.Layout(width=f"{width}px"),
            style={"description_width": "initial"},
        )

        output = widgets.Output()

        # ── spectrum → PNG base64 ────────────────────────────────────────────

        def _spec_png_b64(mode_idx: int) -> str:
            fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)

            ax.plot(x_pts, y_pts / y_max * 100, color="#2563eb",
                    linewidth=1.5, zorder=2)

            for i, (f, I) in enumerate(zip(freqs, intensities)):
                if _x_min <= f <= _x_max:
                    selected = i == mode_idx
                    ax.vlines(
                        f, 0, I / max_intensity * 100,
                        colors="#cc3333" if selected else "#aaaaaa",
                        linewidths=2.5 if selected else 1.0,
                        zorder=4 if selected else 1,
                    )

            ax.axvline(freqs[mode_idx], color="#cc3333",
                       linestyle="--", linewidth=0.8, alpha=0.45, zorder=1)

            ax.set_xlim(_x_min, _x_max)
            ax.set_ylim(0, 110)
            ax.set_xlabel("Wavenumber (cm⁻¹)")
            ax.set_ylabel("Relative Intensity (%)")
            formula = self.data.get("formula", "")
            ax.set_title(f"IR Spectrum{' — ' + formula if formula else ''}")
            ax.tick_params(direction="in", which="both")

            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100)
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode()

        # ── molecule inset HTML ───────────────────────────────────────────────

        def _mol_html(mode_idx: int) -> str:
            """Return py3Dmol HTML string with optional transparent background."""
            self._require_displacements(mode_idx)
            atoms = self.data["atoms"]
            mode = modes[mode_idx]
            symbols = [a["symbol"] for a in atoms]
            coords0 = np.array([[a["x"], a["y"], a["z"]] for a in atoms])
            disps = np.array(mode["displacements"])
            frames = _cosine_frames(coords0, disps, amplitude, n_frames)

            view = py3Dmol.view(width=inset_width, height=inset_height)
            view.setBackgroundColor("0x000000", 0)   # transparent (alpha=0)
            view.addModelsAsFrames(
                _make_multiframe_xyz(symbols, frames), "xyz"
            )
            _apply_ball_and_stick(view)
            view.zoomTo()
            view.animate({"loop": "forward", "reps": 0, "step": 1})
            view.render()

            html = view._make_html()
            # Enable WebGL alpha channel so the transparent background is
            # honoured; py3Dmol hard-codes {backgroundColor:"white"} in the
            # createViewer call — we patch that here.
            html = html.replace(
                '{backgroundColor:"white"}',
                '{backgroundColor:"white",alpha:true}',
            )
            return html

        # ── combined HTML ─────────────────────────────────────────────────────

        def _render(mode_idx: int) -> None:
            spec_b64 = _spec_png_b64(mode_idx)
            mol = _mol_html(mode_idx)

            combined = (
                f'<div style="position:relative;width:{width}px;'
                f'display:inline-block;line-height:0;">\n'
                f'  <img src="data:image/png;base64,{spec_b64}"'
                f'       style="width:{width}px;display:block;" />\n'
                f'  <div style="position:absolute;{inset_edge}'
                f'width:{inset_width}px;height:{inset_height}px;'
                f'border-radius:6px;overflow:hidden;'
                f'box-shadow:0 2px 12px rgba(0,0,0,0.25);">\n'
                f'    {mol}\n'
                f'  </div>\n'
                f'</div>'
            )

            output.clear_output(wait=True)
            with output:
                ipy_display(ipy_HTML(combined))

        # ── wire up and initialise ────────────────────────────────────────────

        dropdown.observe(
            lambda c: _render(c["new"]) if c["name"] == "value" else None,
            names="value",
        )
        _render(0)

        return widgets.VBox([dropdown, output])

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
