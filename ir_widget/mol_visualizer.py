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
    vis.view_linked()                     # linked spectrum + animation panel
"""

from __future__ import annotations

import html as _html_mod
import math
import pathlib
import re

import anywidget
import numpy as np
import traitlets as _tr


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


# ── inset location helpers ───────────────────────────────────────────────────

# Mapping from matplotlib legend loc names / integer codes to canonical names.
_LOC_INT_TO_NAME: dict[int, str] = {
    0: "best",         1: "upper right",  2: "upper left",
    3: "lower left",   4: "lower right",  5: "right",
    6: "center left",  7: "center right", 8: "lower center",
    9: "upper center", 10: "center",
}
_LOC_NAMES: frozenset[str] = frozenset(_LOC_INT_TO_NAME.values())

# Matplotlib typically leaves these fractions of the figure for axis labels.
# Used by the 'best' placement algorithm to map data → pixel coordinates.
_AX_LEFT   = 0.105   # fraction of figure width  (left of axes box)
_AX_RIGHT  = 0.970   # fraction of figure width  (right of axes box)
_AX_TOP    = 0.090   # fraction of figure height (top of axes box, from top)
_AX_BOTTOM = 0.895   # fraction of figure height (bottom of axes box, from top)

_INSET_PAD = 10      # px gap between inset edge and figure edge


def _inset_css(loc: str, W: int, H: int, iw: int, ih: int) -> str:
    """
    Return a CSS position string (``top/bottom/left/right`` in pixels) that
    places an ``iw × ih`` inset inside a ``W × H`` container at location
    *loc* (a matplotlib legend ``loc`` name).

    The inset is offset ``_INSET_PAD`` pixels from every edge it is anchored
    to.  Centre positions are computed from absolute pixel values so they
    work correctly inside a ``position:relative`` div.
    """
    loc = _validate_loc(loc)
    p = _INSET_PAD
    cx = (W - iw) // 2   # left edge for horizontally-centred inset
    cy = (H - ih) // 2   # top  edge for vertically-centred inset

    return {
        "upper right":  f"top:{p}px;right:{p}px;",
        "upper left":   f"top:{p}px;left:{p}px;",
        "lower left":   f"top:{H-ih-p}px;left:{p}px;",
        "lower right":  f"top:{H-ih-p}px;right:{p}px;",
        "right":        f"top:{cy}px;right:{p}px;",
        "center left":  f"top:{cy}px;left:{p}px;",
        "center right": f"top:{cy}px;right:{p}px;",
        "lower center": f"top:{H-ih-p}px;left:{cx}px;",
        "upper center": f"top:{p}px;left:{cx}px;",
        "center":       f"top:{cy}px;left:{cx}px;",
    }[loc]


def _inset_bbox(loc: str, W: int, H: int, iw: int, ih: int) \
        -> tuple[int, int, int, int]:
    """
    Return the pixel bounding box ``(x0, y0, x1, y1)`` (origin = top-left of
    the figure image) for the inset at *loc*.
    """
    p = _INSET_PAD
    cx = (W - iw) // 2
    cy = (H - ih) // 2
    return {
        "upper right":  (W-iw-p, p,       W-p,    p+ih),
        "upper left":   (p,      p,        p+iw,   p+ih),
        "lower left":   (p,      H-ih-p,   p+iw,   H-p),
        "lower right":  (W-iw-p, H-ih-p,   W-p,    H-p),
        "right":        (W-iw-p, cy,        W-p,   cy+ih),
        "center left":  (p,      cy,        p+iw,  cy+ih),
        "center right": (W-iw-p, cy,        W-p,   cy+ih),
        "lower center": (cx,     H-ih-p,   cx+iw,  H-p),
        "upper center": (cx,     p,        cx+iw,  p+ih),
        "center":       (cx,     cy,       cx+iw,  cy+ih),
    }[loc]


def _validate_loc(loc: "str | int") -> str:
    """Normalise *loc* to a canonical location name; raise on unknown values."""
    if isinstance(loc, int):
        if loc not in _LOC_INT_TO_NAME:
            raise ValueError(
                f"Unknown integer loc code {loc!r}. "
                f"Valid codes: {sorted(_LOC_INT_TO_NAME)}"
            )
        loc = _LOC_INT_TO_NAME[loc]
    loc = loc.strip().lower()
    if loc not in _LOC_NAMES:
        raise ValueError(
            f"Unknown loc {loc!r}. "
            f"Valid names: {sorted(_LOC_NAMES)}"
        )
    return loc


def _best_inset_loc(
    x_pts: np.ndarray, y_pts_norm: np.ndarray,
    freqs: np.ndarray, intensities_norm: np.ndarray,
    x_min: float, x_max: float,
    W: int, H: int, iw: int, ih: int,
) -> str:
    """
    Choose the inset location (excluding ``'best'``) that overlaps the least
    spectrum "ink" — the approach used by matplotlib's ``legend(loc='best')``.

    *y_pts_norm* and *intensities_norm* are already normalised to 0–100 %.

    The algorithm converts data coordinates to pixel coordinates using the
    estimated axes bounding box (``_AX_LEFT`` … ``_AX_BOTTOM``) and then
    counts how many sampled curve/stick points fall inside each candidate box.
    """
    ax_l = _AX_LEFT  * W
    ax_r = _AX_RIGHT * W
    ax_t = _AX_TOP   * H
    ax_b = _AX_BOTTOM * H

    def _to_px(xd: np.ndarray, yd: np.ndarray):
        xp = ax_l + (xd - x_min) / (x_max - x_min) * (ax_r - ax_l)
        yp = ax_t + (1.0 - yd / 100.0) * (ax_b - ax_t)
        return xp, yp

    # Envelope points
    ex, ey = _to_px(x_pts, y_pts_norm)

    # Stick points: sample each stick as a dense vertical line
    stick_x_list, stick_y_list = [], []
    n_samples = 20
    for f, h in zip(freqs, intensities_norm):
        ys = np.linspace(0, h, n_samples)
        xs = np.full(n_samples, f)
        sx, sy = _to_px(xs, ys)
        stick_x_list.append(sx)
        stick_y_list.append(sy)

    all_x = np.concatenate([ex, *stick_x_list])
    all_y = np.concatenate([ey, *stick_y_list])

    candidates = [k for k in _LOC_NAMES if k != "best"]
    best_loc, best_count = "upper right", float("inf")
    for cand in candidates:
        x0, y0, x1, y1 = _inset_bbox(cand, W, H, iw, ih)
        count = int(np.sum(
            (all_x >= x0) & (all_x <= x1) & (all_y >= y0) & (all_y <= y1)
        ))
        if count < best_count:
            best_count = count
            best_loc = cand
    return best_loc


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


# ── LinkedViewWidget (anywidget) ─────────────────────────────────────────────

_LINKED_VIEW_JS = r"""
const _3DMOL_SRC = 'https://cdn.jsdelivr.net/npm/3dmol@2.5.4/build/3Dmol-min.js';

// Module-level promise ensures 3Dmol.js is loaded only once per page.
let _3dmolPromise = null;

function ensure3Dmol() {
  if (_3dmolPromise) return _3dmolPromise;
  _3dmolPromise = new Promise((resolve, reject) => {
    if (window.$3Dmol) { resolve(window.$3Dmol); return; }
    const s = document.createElement('script');
    s.src = _3DMOL_SRC;
    s.onload  = () => resolve(window.$3Dmol);
    s.onerror = () => { _3dmolPromise = null; reject(new Error('3Dmol.js failed to load')); };
    document.head.appendChild(s);
  });
  return _3dmolPromise;
}

function render({ model, el }) {
  const W  = model.get('_width');
  const H  = model.get('_height');
  const IW = model.get('_inset_width');
  const IH = model.get('_inset_height');
  const insetStyle = model.get('_inset_css_str');
  const xMin    = model.get('_x_min');
  const xMax    = model.get('_x_max');
  const formula = model.get('_formula');
  const xPts    = model.get('_x_pts');
  const yNorm   = model.get('_y_norm');
  const freqs   = model.get('_freqs');
  const iNorm   = model.get('_i_norm');
  const molFrames = model.get('_mol_frames');
  const labels    = model.get('_mode_labels');

  // ── DOM structure ────────────────────────────────────────────────────────
  el.style.cssText = 'display:inline-block;font-family:sans-serif;';

  const selectWrapper = document.createElement('div');
  selectWrapper.style.cssText = `display:flex;align-items:center;gap:8px;margin-bottom:6px;width:${W}px;`;

  const selectLabel = document.createElement('label');
  selectLabel.textContent = 'Mode:';
  selectLabel.style.cssText = 'font-size:13px;font-weight:bold;white-space:nowrap;';

  const selectEl = document.createElement('select');
  selectEl.style.cssText = 'flex:1;padding:4px 8px;font-size:13px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
  labels.forEach((label, i) => {
    const opt = document.createElement('option');
    opt.value = String(i);
    opt.textContent = label;
    selectEl.appendChild(opt);
  });
  selectEl.value = String(model.get('mode_index'));

  selectWrapper.appendChild(selectLabel);
  selectWrapper.appendChild(selectEl);

  const plotArea = document.createElement('div');
  plotArea.style.cssText = `position:relative;width:${W}px;height:${H}px;`;

  const dpr = window.devicePixelRatio || 1;
  const canvas = document.createElement('canvas');
  canvas.width  = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  canvas.style.cssText = `position:absolute;top:0;left:0;width:${W}px;height:${H}px;`;

  const molDiv = document.createElement('div');
  molDiv.style.cssText = `position:absolute;${insetStyle}width:${IW}px;height:${IH}px;border-radius:6px;overflow:hidden;`;

  plotArea.appendChild(canvas);
  plotArea.appendChild(molDiv);
  el.appendChild(selectWrapper);
  el.appendChild(plotArea);

  // ── Spectrum drawing ─────────────────────────────────────────────────────
  const margin = { top: 35, right: 20, bottom: 48, left: 65 };

  function drawSpectrum(modeIdx) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.scale(dpr, dpr);

    const pw = W - margin.left - margin.right;
    const ph = H - margin.top - margin.bottom;
    const baseline = margin.top + ph;

    const toX = xd => margin.left + (xd - xMin) / (xMax - xMin) * pw;
    const toY = yd => margin.top  + (1 - yd / 100) * ph;

    // White background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);

    // Title
    ctx.fillStyle = '#222';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(formula ? `IR Spectrum \u2014 ${formula}` : 'IR Spectrum', W / 2, 20);

    // Axes
    ctx.strokeStyle = '#444';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top);
    ctx.lineTo(margin.left, baseline);
    ctx.lineTo(margin.left + pw, baseline);
    ctx.stroke();

    // X-axis ticks + labels
    ctx.fillStyle = '#444';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    const nxTicks = 6;
    for (let i = 0; i <= nxTicks; i++) {
      const v = xMin + (xMax - xMin) * i / nxTicks;
      const x = toX(v);
      ctx.beginPath(); ctx.moveTo(x, baseline); ctx.lineTo(x, baseline + 4); ctx.stroke();
      ctx.fillText(Math.round(v).toString(), x, baseline + 16);
    }
    ctx.fillText('Wavenumber (cm\u207b\u00b9)', W / 2, H - 8);

    // Y-axis ticks + label
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const v = i * 25;
      const y = toY(v);
      ctx.beginPath(); ctx.moveTo(margin.left - 4, y); ctx.lineTo(margin.left, y); ctx.stroke();
      ctx.fillText(v + '%', margin.left - 8, y + 4);
    }
    ctx.save();
    ctx.translate(14, H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('Relative Intensity', 0, 0);
    ctx.restore();

    // Dashed vertical guide for selected mode
    const sf = freqs[modeIdx];
    if (sf >= xMin && sf <= xMax) {
      ctx.save();
      ctx.strokeStyle = '#cc3333';
      ctx.lineWidth = 0.8;
      ctx.setLineDash([4, 4]);
      ctx.globalAlpha = 0.45;
      ctx.beginPath();
      ctx.moveTo(toX(sf), margin.top);
      ctx.lineTo(toX(sf), baseline);
      ctx.stroke();
      ctx.restore();
    }

    // Grey sticks (all non-selected)
    for (let i = 0; i < freqs.length; i++) {
      if (i === modeIdx) continue;
      const f = freqs[i];
      if (f < xMin || f > xMax) continue;
      ctx.strokeStyle = '#aaaaaa';
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.moveTo(toX(f), baseline);
      ctx.lineTo(toX(f), toY(iNorm[i]));
      ctx.stroke();
    }
    // Selected stick on top in red
    if (freqs[modeIdx] >= xMin && freqs[modeIdx] <= xMax) {
      ctx.strokeStyle = '#cc3333';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(toX(freqs[modeIdx]), baseline);
      ctx.lineTo(toX(freqs[modeIdx]), toY(iNorm[modeIdx]));
      ctx.stroke();
    }

    // Lorentzian envelope
    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 1.0;
    ctx.beginPath();
    let first = true;
    for (let i = 0; i < xPts.length; i++) {
      if (xPts[i] < xMin || xPts[i] > xMax) continue;
      const x = toX(xPts[i]);
      const y = toY(yNorm[i]);
      if (first) { ctx.moveTo(x, y); first = false; } else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.restore();
  }

  // ── 3Dmol viewer ─────────────────────────────────────────────────────────
  let viewer = null;

  function applyBallAndStick() {
    viewer.setStyle({}, { sphere: { scale: 0.4, colorscheme: 'Jmol' }, stick: { radius: 0.20 } });
    viewer.setStyle({ elem: 'H' }, { sphere: { scale: 0.3, color: 'white' }, stick: { radius: 0.20, color: 'white' } });
  }

  function updateMol(modeIdx) {
    if (!viewer) return;
    const frames = molFrames[modeIdx];
    if (!frames) return;
    viewer.stopAnimate();          // stop existing timer before replacing models
    viewer.removeAllModels();
    viewer.addModelsAsFrames(frames, 'xyz');
    applyBallAndStick();
    viewer.zoomTo({}, 0);          // instant zoom (duration=0), no camera animation
    viewer.animate({ loop: 'forward', reps: 0, step: 1, interval: 40 });
  }

  ensure3Dmol().then(() => {
    viewer = window.$3Dmol.createViewer(molDiv, { alpha: true });
    viewer.setBackgroundColor(0x000000, 0);  // transparent
    requestAnimationFrame(() => {
      viewer.resize();
      updateMol(model.get('mode_index'));
    });
  }).catch(err => {
    molDiv.style.cssText += 'display:flex;align-items:center;justify-content:center;';
    molDiv.innerHTML = '<span style="color:#cc3333;font-size:12px;padding:8px;">3Dmol.js failed to load</span>';
  });

  // ── event wiring ─────────────────────────────────────────────────────────
  drawSpectrum(model.get('mode_index'));

  selectEl.addEventListener('change', e => {
    const idx = parseInt(e.target.value, 10);
    model.set('mode_index', idx);
    model.save_changes();
    drawSpectrum(idx);
    updateMol(idx);
  });

  model.on('change:mode_index', () => {
    const idx = model.get('mode_index');
    selectEl.value = String(idx);
    drawSpectrum(idx);
    updateMol(idx);
  });

  return () => {
    if (viewer) { try { viewer.stopAnimate(); viewer.removeAllModels(); } catch (_) {} }
  };
}

export default { render };
"""


class LinkedViewWidget(anywidget.AnyWidget):
    """
    Linked IR spectrum + animated molecular viewer as an anywidget.

    Works in both JupyterLab and Marimo.  Instantiate via
    :meth:`MolVisualizerWidget.view_linked` rather than directly.
    """

    _esm = _LINKED_VIEW_JS

    #: Currently selected mode (0-based); synced to the dropdown in the UI.
    mode_index = _tr.Int(0).tag(sync=True)

    # ── spectrum data (precomputed in Python, read-only in JS) ────────────
    _x_pts  = _tr.List(_tr.Float()).tag(sync=True)
    _y_norm = _tr.List(_tr.Float()).tag(sync=True)
    _freqs  = _tr.List(_tr.Float()).tag(sync=True)
    _i_norm = _tr.List(_tr.Float()).tag(sync=True)
    _x_min  = _tr.Float(0.0).tag(sync=True)
    _x_max  = _tr.Float(4000.0).tag(sync=True)

    # ── molecular animation (one multiframe-XYZ string per mode) ─────────
    _mol_frames  = _tr.List(_tr.Unicode()).tag(sync=True)
    _mode_labels = _tr.List(_tr.Unicode()).tag(sync=True)

    # ── layout ────────────────────────────────────────────────────────────
    _width        = _tr.Int(800).tag(sync=True)
    _height       = _tr.Int(480).tag(sync=True)
    _inset_width  = _tr.Int(300).tag(sync=True)
    _inset_height = _tr.Int(250).tag(sync=True)
    _inset_css_str = _tr.Unicode("top:10px;right:10px;").tag(sync=True)
    _formula      = _tr.Unicode("").tag(sync=True)


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
        width: int = 800,
        height: int = 480,
        inset_width: int = 300,
        inset_height: int = 250,
        loc: "str | int" = "best",
    ) -> LinkedViewWidget:
        """
        Return a linked view: IR spectrum with an animated molecular viewer
        inset.

        Works in both JupyterLab and Marimo via anywidget.

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
            Pixel dimensions of the overall panel.
        inset_width, inset_height : int
            Pixel dimensions of the molecule viewer inset.
        loc : str or int
            Inset placement — same names and integer codes as matplotlib's
            ``legend(loc=...)`` argument:

            * ``'best'`` (default) — auto-selects the corner with the least
              spectrum overlap.
            * ``'upper right'`` / ``1``
            * ``'upper left'``  / ``2``
            * ``'lower left'``  / ``3``
            * ``'lower right'`` / ``4``
            * ``'right'``       / ``5``
            * ``'center left'`` / ``6``
            * ``'center right'``/ ``7``
            * ``'lower center'``/ ``8``
            * ``'upper center'``/ ``9``
            * ``'center'``      / ``10``

        Returns
        -------
        LinkedViewWidget
            anywidget ready to display in Jupyter or Marimo.
        """
        self._require_geometry()

        modes = self.data["modes"]
        freqs = np.array([m["frequency"] for m in modes])
        intensities = np.array([m["intensity"] for m in modes])
        max_intensity = intensities.max() if intensities.max() > 0 else 1.0

        _x_min = float(max(0.0, freqs.min() - 200)) if x_min is None else x_min
        _x_max = float(freqs.max() + 200) if x_max is None else x_max

        # Lorentzian envelope, normalised to 0–100 %
        x_pts = np.linspace(_x_min, _x_max, 2000)
        gamma = fwhm / 2.0
        y_pts = np.zeros_like(x_pts)
        for f, I in zip(freqs, intensities):
            y_pts += I * gamma**2 / ((x_pts - f)**2 + gamma**2)
        y_max = y_pts.max() if y_pts.max() > 0 else 1.0
        y_norm = y_pts / y_max * 100
        i_norm = intensities / max_intensity * 100

        # Resolve inset location
        _loc = _validate_loc(loc)
        if _loc == "best":
            _loc = _best_inset_loc(
                x_pts, y_norm, freqs, i_norm,
                _x_min, _x_max, width, height, inset_width, inset_height,
            )
        inset_css = _inset_css(_loc, width, height, inset_width, inset_height)

        # Build one multiframe-XYZ string per mode (empty string if no displacements)
        atoms = self.data["atoms"]
        symbols = [a["symbol"] for a in atoms]
        coords0 = np.array([[a["x"], a["y"], a["z"]] for a in atoms])
        mol_frames = []
        for mi, mode in enumerate(modes):
            if "displacements" in mode:
                disps = np.array(mode["displacements"])
                frames = _cosine_frames(coords0, disps, amplitude, n_frames)
                mol_frames.append(_make_multiframe_xyz(symbols, frames))
            else:
                # Static single-frame fallback when displacements are absent
                mol_frames.append(_make_multiframe_xyz(symbols, [coords0]))

        mode_labels = [
            f"Mode {m['mode']}: {m['frequency']:.1f} cm\u207b\u00b9"
            f"  ({m['intensity']:.1f} km/mol)"
            for m in modes
        ]

        return LinkedViewWidget(
            mode_index=0,
            _x_pts=x_pts.tolist(),
            _y_norm=y_norm.tolist(),
            _freqs=freqs.tolist(),
            _i_norm=i_norm.tolist(),
            _x_min=_x_min,
            _x_max=_x_max,
            _mol_frames=mol_frames,
            _mode_labels=mode_labels,
            _width=width,
            _height=height,
            _inset_width=inset_width,
            _inset_height=inset_height,
            _inset_css_str=inset_css,
            _formula=self.data.get("formula", ""),
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
