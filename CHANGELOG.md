# Changelog

All notable changes to the IR Vibrational Widget project.

## [1.1.0] - 2026-07-15

A second major phase of work on top of 1.0.0: direct Psi4 integration, a full
3-D molecular visualization module, and an automated pytest suite. Core
functionality (the Psi4 path and `mol_visualizer.py`) was developed between
2026-03-13 and 2026-04-14; the test suite was added 2026-07-15 to close the
coverage gap before tagging this release. See `.copilot/plan.md` (Phase 2)
for the detailed workplan and the rationale behind the trickier fixes.

### Added - Direct Psi4 data path (`ir_widget/widget.py`)
- `IRWidget.load_from_psi4_wfn(wfn)` — extracts frequencies, IR intensities,
  atom geometry, and normal-mode Cartesian displacement vectors directly from
  a Psi4 1.10+ wavefunction via PsiAPI (`qcdb.vib.harmonic_analysis`), with no
  file parsing required
- `IRWidget.run_psi4_frequency(geometry, method_basis, ...)` — runs a Psi4
  harmonic frequency calculation from inside the widget and loads the result
- `_prepare_data()` now carries optional `atoms` and per-mode `displacements`,
  consumed by the new molecular visualizer

### Added - `ir_widget/mol_visualizer.py` (new module)
- `MolVisualizerWidget` factory, built from `IRWidget.data`:
  - `view_structure()` — static ball-and-stick model
  - `view_mode(mode_index, amplitude, n_frames)` — single vibrational mode
    animation (cosine-envelope frames for a seamless loop)
  - `view_orbital(cube_data, isovalue, ...)` — one-shot molecular orbital
    isosurface render from a Gaussian `.cube` file
  - `view_linked(...)` — linked IR spectrum + animated-molecule inset, with
    matplotlib-style `loc=` placement (including an auto `'best'` heuristic)
  - `view_mode_selector(...)` / `view_orbital_selector(...)` — dropdown-driven
    variants (`ModeViewWidget`, `OrbitalViewWidget`) with HOMO/LUMO-relative
    orbital auto-labeling
- `LinkedViewWidget`, `ModeViewWidget`, `OrbitalViewWidget` anywidget classes,
  all exported from `ir_widget/__init__.py`
- Marimo compatibility: py3Dmol viewer HTML is wrapped in an `<iframe
  srcdoc>` so its inline `<script>` bootstrapper actually executes (Marimo's
  `renderHTML` otherwise drops inline scripts silently)
- Psi4 calculation caching in the example notebook to avoid re-running
  expensive calculations on every Marimo reload

### Fixed
- Dropdown UI hidden behind 3Dmol's WebGL canvas stacking context
- Stale orbital isosurfaces accumulating across rapid dropdown changes (now
  recreates the viewer per orbital change instead of clearing it in place)
- Orbital compositing artifacts from overlapping async isosurface computations
  (`_updateSeq` guard so stale continuations bail out)
- Camera/zoom state resetting on every mode/orbital switch
- Molecular orbital atom coordinates now loaded from XYZ data rather than
  parsed out of the `.cube` file (unreliable across 3Dmol.js/py3Dmol versions)
- H-atom rendering/visibility and CPK color restoration in the 3-D viewers

### Added - Testing
- Real pytest suite (52 tests, `pixi run pytest`, ~2s):
  - `tests/test_widget.py` — `IRWidget` data loading, formula generation,
    cclib error paths (mocked), and a real end-to-end Psi4 HF/STO-3G
    frequency calculation on H₂
  - `tests/test_mol_visualizer.py` — inset-placement helpers, XYZ/animation
    helpers, and all `MolVisualizerWidget` view methods, including
    HOMO/LUMO auto-labeling and the `OrbitalViewWidget` index-swap observer
  - Replaces the previous `tests/test_widget.py`, which was a manual
    print-based smoke-test script rather than an automated suite

### Dependencies added
- `psi4`, `py3dmol`, `nglview` (superseded by py3dmol, still listed),
  `scipy`, `matplotlib`, `jupyter-marimo-proxy`, `pytest` (dev/test only)

### Known gaps
- `README.md` still only documents the 1.0.0 IR-table-and-spectrum feature
  set — Psi4 integration and the 3-D visualizer are undocumented for users
- See `.copilot/plan.md` (Phase 3) for the remaining feature backlog
  (spectrum/CSV export, peak picking, Raman support, etc.)

## [1.0.0] - 2026-02-12

### Added - Initial Release

#### Core Widget
- `IRWidget` class for displaying IR vibrational spectra
- cclib integration for parsing quantum chemistry output files
- Support for Gaussian, ORCA, Psi4, NWChem, GAMESS, Q-Chem, and more
- Direct data loading from numpy arrays
- Automatic molecular formula generation

#### Display Features
- Interactive sortable frequency table (mode, frequency, intensity)
- Canvas-based IR spectrum plot
- Three broadening types: stick, Lorentzian, Gaussian
- Customizable FWHM (full-width at half-maximum)
- Adjustable wavenumber range (x_min, x_max)
- Toggle table and plot visibility
- Responsive design for different screen sizes

#### Sample Data
- Pre-loaded IR data for 7 common molecules:
  - H₂O (Water) - 3 modes
  - CO₂ (Carbon Dioxide) - 3 modes
  - CH₄ (Methane) - 4 modes
  - NH₃ (Ammonia) - 4 modes
  - C₂H₄ (Ethylene) - 11 modes
  - C₆H₆ (Benzene) - 20 modes
  - C₃H₆O (Acetone) - 14 modes
- `get_sample_data()` function for easy access
- `print_molecule_info()` for exploring available samples

#### Examples
- Marimo notebook (`ir_widget_example.py`) with interactive controls
- Jupyter notebook (`ir_widget_example.ipynb`) with detailed examples
- Quick test script (`quick_test.py`) for validation

#### Documentation
- Comprehensive README.md
- GETTING_STARTED.md with step-by-step instructions
- IMPLEMENTATION_SUMMARY.md with technical details
- Inline code documentation and docstrings

#### Technical Features
- Pure Python backend with traitlets
- Vanilla JavaScript frontend (no external plotting dependencies)
- Efficient spectrum calculation with configurable resolution
- Error handling and validation
- Support for both Jupyter and Marimo notebooks

### Dependencies
- Python 3.13+
- anywidget >= 0.9.21
- cclib >= 1.8.1
- numpy >= 2.3.5

### Testing
- All basic functionality tested
- Widget creation and data loading verified
- Property updates validated
- Multiple molecule support confirmed
- Sample data integration tested

## Future Enhancements (Not Yet Implemented)

Delivered in 1.1.0 and removed from this list: vibrational mode animation,
3-D molecular structure viewer integration, and normal mode displacement
vector visualization (see the `[1.1.0]` entry above).

### Planned Features
- Peak picking and annotation
- Export spectrum as image (PNG, SVG)
- Export data as CSV
- Multiple spectrum overlay for comparison
- Experimental spectrum overlay
- Automatic peak assignment suggestions
- Zoom and pan controls for plot
- Isotope effects visualization

### Under Consideration
- Raman spectroscopy support
- Interactive peak labeling
- Spectrum fitting tools
- Database integration for reference spectra

---

## Version History

- **v1.1.0** (2026-07-15) - Direct Psi4 integration, 3-D molecular/orbital
  visualization (`mol_visualizer.py`), automated pytest suite
- **v1.0.0** (2026-02-12) - Initial release with core functionality
