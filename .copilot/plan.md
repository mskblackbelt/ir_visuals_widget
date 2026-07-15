# IR Vibrational Widget Implementation Plan

**Status:** ✅ Phase 1 & 2 COMPLETE — Phase 3 not started
**Current version:** 1.0.0 (package version has not been bumped since Phase 2 landed)

## Problem Statement
Build a notebook-native (Jupyter + Marimo) toolkit for visualizing quantum
chemistry vibrational/electronic-structure results without a server backend:
- Parse calculation output (cclib) or pull data directly from a live Psi4
  wavefunction
- Display a table + spectrum of IR frequencies and intensities
- Visualize the 3-D molecular structure, animate individual vibrational
  normal modes, and render molecular orbital isosurfaces from `.cube` files

## Phase 1: IR Spectrum Widget ✅ COMPLETE (2026-02-12)

Self-contained anywidget with a Python backend (cclib parsing) and vanilla
JS/Canvas frontend.

- [x] `ir_widget/widget.py` — `IRWidget` class
- [x] cclib-based `load_file()` parsing (Gaussian, ORCA, Psi4, NWChem, GAMESS,
      Q-Chem, Molpro, MOPAC, …)
- [x] Direct array loading via `load_data()`
- [x] Molecular formula generation (Hill order)
- [x] `ir_widget.js` — sortable frequency table + Canvas IR spectrum plot
- [x] Three broadening modes: none (stick), Lorentzian, Gaussian
- [x] `ir_widget.css` styling, responsive layout
- [x] Sample data (`examples/sample_data.py`, 7 molecules), example notebooks
      (Jupyter + Marimo), docs (`docs/GETTING_STARTED.md`,
      `docs/IMPLEMENTATION_SUMMARY.md`)

## Phase 2: Psi4 Integration + 3-D Molecular Visualization ✅ COMPLETE (2026-03-13 → 2026-04-14)

Not part of the original plan — added after Phase 1 shipped. Two major
additions to `IRWidget` plus an entirely new `mol_visualizer` module.

### 2a. Direct Psi4 data path (`ir_widget/widget.py`)
- [x] `load_from_psi4_wfn(wfn)` — extracts frequencies, IR intensities, atom
      geometry, and Cartesian normal-mode displacement vectors straight from
      a `psi4.frequency(..., return_wfn=True)` result via
      `psi4.driver.qcdb.vib.harmonic_analysis`, bypassing cclib/file I/O
      entirely (PsiAPI path, recommended for Psi4 1.10+)
- [x] `run_psi4_frequency(geometry, method_basis, ...)` — runs the Psi4
      calculation itself and feeds the result into `load_from_psi4_wfn`
- [x] `_prepare_data()` extended to carry optional `atoms` (equilibrium
      Cartesian coords) and per-mode `displacements`, consumed by
      `mol_visualizer`
- [x] Psi4 result caching in the example notebook to avoid re-running
      expensive calculations on every Marimo reload

### 2b. `mol_visualizer.py` — py3Dmol-based 3-D viewers
- [x] `MolVisualizerWidget` — factory built from an `IRWidget.data` dict
  - [x] `view_structure()` — static ball-and-stick model (CPK/Jmol coloring,
        proportional H spheres)
  - [x] `view_mode(mode_index, amplitude, n_frames)` — single-mode animation
        using cosine-envelope frames for a seamless animation loop
  - [x] `view_orbital(cube_data, isovalue, ...)` — one-shot ± isosurface
        render from a Gaussian `.cube` file
  - [x] `view_linked(...)` — combined spectrum + animated-molecule inset,
        with matplotlib-style `loc=` placement including an auto `'best'`
        heuristic that minimizes overlap with spectrum ink
  - [x] `view_mode_selector(...)` → `ModeViewWidget` — standalone animated
        viewer with a mode-selection dropdown
  - [x] `view_orbital_selector(cube_files, homo_index=..., ...)` →
        `OrbitalViewWidget` — dropdown orbital viewer with HOMO/LUMO-relative
        auto-labeling; only the active orbital's cube data is synced to JS
        per selection change (keeps comm messages small)
- [x] Three dedicated anywidget subclasses (`LinkedViewWidget`,
      `ModeViewWidget`, `OrbitalViewWidget`), all exported from
      `ir_widget/__init__.py`
- [x] Marimo compatibility layer: `_make_iframe_html()` wraps the py3Dmol
      viewer in an `<iframe srcdoc>` because Marimo's `renderHTML` silently
      drops inline `<script>` tags (only `<script src>` is processed), so the
      3Dmol.js CDN loader never fired outside an iframe's own browsing context
- [x] Hardening against a long tail of 3Dmol/Marimo rendering bugs (see
      git history 2026-03-26 → 2026-03-30 for the blow-by-blow):
  - dropdown UI hidden behind 3Dmol's WebGL canvas stacking context (fixed
    with `position:relative;z-index:1` on the control row)
  - stale isosurfaces accumulating across rapid dropdown changes (fixed by
    recreating the viewer per orbital change rather than trying to clear it)
  - camera/zoom state getting reset on every mode/orbital switch (fixed by
    capturing `getView()`/`setView()` around the swap)
  - async isosurface compute races when switching orbitals quickly (fixed
    with a monotonic `_updateSeq` guard so stale continuations bail out)
  - atom coordinates loaded from XYZ rather than parsed out of the `.cube`
    file, since cube-format atom parsing isn't reliable across
    3Dmol.js/py3Dmol versions

### Dependencies added
- `psi4`, `py3dmol`, `nglview` (superseded by py3dmol, still in pixi.toml),
  `scipy`, `matplotlib`, `jupyter-marimo-proxy` (see `pixi.toml`)

## Phase 3: Not started

Carried over / updated from the original "future enhancements" list — items
already delivered in Phase 2 have been removed:

- [ ] Automated test coverage for `mol_visualizer.py` (currently zero —
      `tests/test_widget.py` is a manual smoke-test script, not pytest, and
      only exercises `IRWidget`)
- [ ] Export spectrum as PNG/SVG
- [ ] Export frequency/intensity data as CSV
- [ ] Multiple spectrum overlay (compare molecules/conformers)
- [ ] Experimental spectrum overlay
- [ ] Automatic peak assignment / peak picking & annotation
- [ ] Zoom/pan controls on the Canvas spectrum plot
- [ ] Raman spectroscopy support
- [ ] Isotope effects visualization
- [ ] README.md / package version bump to reflect Phase 2 scope (still
      describes only the Phase 1 IR-table-and-spectrum widget)

## Technical Notes

### Spectrum Broadening Formulas
- **Lorentzian**: I(ν) = I₀ · γ² / ((ν − ν₀)² + γ²)
- **Gaussian**: I(ν) = I₀ · exp(−((ν − ν₀)/σ)²)

Where γ is FWHM/2 for Lorentzian, σ = FWHM/(2√(2ln2)) for Gaussian.

### Supported input paths
1. cclib file parsing — Gaussian, ORCA, Psi4, NWChem, GAMESS, Q-Chem, Molpro,
   MOPAC, and more (`IRWidget.load_file` / `file_path=`)
2. Direct array input (`IRWidget.load_data`)
3. Live Psi4 wavefunction (`IRWidget.load_from_psi4_wfn`) or an in-widget
   Psi4 run (`IRWidget.run_psi4_frequency`) — the only paths that populate
   `atoms`/`displacements` for 3-D visualization

### Widget/class inventory
- `IRWidget` — table + spectrum (`ir_widget.py`/`.js`/`.css`)
- `MolVisualizerWidget` — plain Python factory, not itself an anywidget
- `LinkedViewWidget`, `ModeViewWidget`, `OrbitalViewWidget` — anywidget
  subclasses returned by `MolVisualizerWidget`'s `view_linked()` /
  `view_mode_selector()` / `view_orbital_selector()`

## Project Status

**Phase 1 completed:** 2026-02-12
**Phase 2 completed:** 2026-04-14 (last commit: `a73353a`, "Ignore calculated
cube files")
**Phase 3:** not started — see backlog above.
