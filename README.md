# IR Vibrational Spectroscopy Widget

An [anywidget](https://anywidget.dev/) toolkit for visualizing quantum
chemistry vibrational and electronic-structure results in Jupyter and Marimo
notebooks — IR frequency tables and spectra, animated 3-D vibrational modes,
and molecular orbital isosurfaces.

![IR Widget Screenshot](https://img.shields.io/badge/anywidget-IR_Spectroscopy-blue)

## Features

- 📊 **Interactive frequency table** with sortable columns
- 📈 **IR spectrum visualization** with customizable broadening
- 🔧 **Multiple broadening functions**: stick spectrum, Lorentzian, and Gaussian
- 🧬 **3-D molecular visualization** via py3Dmol: ball-and-stick structure,
  animated vibrational normal modes, and molecular orbital isosurfaces from
  Gaussian `.cube` files
- 🔗 **Linked spectrum + animation view**, with matplotlib-style inset
  placement (including an automatic "least overlap" placement)
- ⚛️ **Direct Psi4 integration** — load vibrational data, geometry, and normal
  modes straight from a `psi4.frequency(..., return_wfn=True)` result, or run
  the calculation from inside the widget
- 📁 **Wide file-format support** via cclib (Gaussian, ORCA, Psi4, NWChem,
  GAMESS, Q-Chem, and more)
- 🎨 **Clean, scientific styling** optimized for notebooks
- 🪟 **Works in both JupyterLab and Marimo** (including the 3-D viewers)
- 🧪 **Sample data included** for 7 common molecules (H₂O, CO₂, CH₄, NH₃, C₂H₄, C₆H₆, C₃H₆O)

## What It Looks Like

- **A sortable table** showing mode number, frequency (cm⁻¹), and intensity (km/mol)
- **An interactive plot** of the IR spectrum with axes labels and gridlines,
  with stick, Lorentzian, or Gaussian broadening
- **A 3-D molecular viewer** for the equilibrium structure, an animated
  vibrational mode, or a molecular orbital isosurface — standalone, or linked
  to the spectrum with a mode-selection dropdown

## Installation

This widget requires:
- Python 3.10+ (3.13 recommended)
- anywidget, numpy

Optional, for the extra features:
- cclib (file parsing)
- psi4 (direct PsiAPI data loading / in-widget frequency calculations)
- py3Dmol (3-D structure/mode/orbital visualization)

Install dependencies using pixi (recommended — the `pixi.toml` in this repo
pulls in all of the above, plus JupyterLab and Marimo):
```bash
pixi install
```

Or with pip, picking only what you need:
```bash
pip install anywidget numpy cclib psi4 py3Dmol
```

## Quick Start

### Using sample data (no calculation file needed)

```python
from ir_widget import IRWidget
from sample_data import get_sample_data

# Load pre-defined sample data for common molecules
data = get_sample_data("ACETONE")  # or "H2O", "CO2", "BENZENE", etc.

widget = IRWidget()
widget.load_data(data['frequencies'], data['intensities'], formula=data['formula'])
widget
```

See available molecules:
```python
from sample_data import print_molecule_info
print_molecule_info()  # Lists all available samples
```

### Loading from a calculation file (via cclib)

```python
from ir_widget import IRWidget

# Load data from a quantum chemistry output file
widget = IRWidget(file_path="molecule.log")
widget
```

### Loading directly from a Psi4 calculation

For Psi4 1.10+, this is the recommended path — it also populates atom
geometry and normal-mode displacement vectors needed for 3-D visualization
(cclib-parsed files and directly-loaded arrays do not include these).

```python
import psi4
from ir_widget import IRWidget

mol = psi4.geometry("""
  O
  H 1 0.96
  H 1 0.96 2 104.5
""")
energy, wfn = psi4.frequency('hf/sto-3g', molecule=mol, return_wfn=True)

widget = IRWidget()
widget.load_from_psi4_wfn(wfn)
widget
```

Or let the widget run the calculation for you:
```python
widget = IRWidget()
widget.run_psi4_frequency(
    geometry="""
      O
      H 1 0.96
      H 1 0.96 2 104.5
    """,
    method_basis='hf/sto-3g',
    memory='2 GB',
)
widget
```

### Loading data directly

```python
import numpy as np
from ir_widget import IRWidget

# Provide frequencies and intensities directly
frequencies = np.array([1595.0, 3657.0, 3756.0])  # cm⁻¹
intensities = np.array([75.0, 20.0, 45.0])        # km/mol

widget = IRWidget()
widget.load_data(frequencies, intensities, formula="H2O")
widget
```

## 3-D Molecular Visualization

`MolVisualizerWidget` renders a molecule's structure, vibrational modes, and
orbitals with [py3Dmol](https://3dmol.org/). It needs atom geometry (and,
for mode animation, normal-mode displacement vectors), which only the Psi4
data path (`load_from_psi4_wfn` / `run_psi4_frequency`) currently populates.

```python
from ir_widget import IRWidget, MolVisualizerWidget

widget = IRWidget()
widget.load_from_psi4_wfn(wfn)  # populates atoms + displacements

vis = MolVisualizerWidget(widget.data)
```

**Static structure** — ball-and-stick model:
```python
vis.view_structure()
```

**Animate a single vibrational mode**:
```python
vis.view_mode(mode_index=2, amplitude=0.5)  # amplitude in Å
```

**Animated mode with a dropdown selector** (standalone widget):
```python
vis.view_mode_selector(amplitude=0.5)
```

**Molecular orbital isosurface**, from a Gaussian `.cube` file generated by
`psi4.cubeprop()`:
```python
psi4.set_options({'cubeprop_tasks': ['orbitals'],
                   'cubeprop_orbitals': [19, 20, 21, 22, 23]})
psi4.cubeprop(wfn)  # writes Psi_a_019_19-A.cube, Psi_a_020_20-A.cube, ...

vis.view_orbital('Psi_a_021_21-A.cube', isovalue=0.02)
```

**Orbital viewer with a dropdown selector**, with automatic HOMO/LUMO
labeling:
```python
cube_files = [f'Psi_a_{n:03d}_{n}-A.cube' for n in [19, 20, 21, 22, 23]]
vis.view_orbital_selector(cube_files, homo_index=2)  # index 2 -> HOMO
```

**Linked view** — spectrum with an animated-molecule inset, one panel, mode
dropdown selects both the highlighted stick and the animation:
```python
vis.view_linked(amplitude=0.5, loc="best")  # loc: matplotlib-style placement,
                                             # or "best" to auto-avoid the spectrum
```

All of the above work in both JupyterLab and Marimo. In Marimo, the viewer
HTML is automatically wrapped in an `<iframe srcdoc>` so 3Dmol.js's inline
loader script executes correctly (Marimo's `renderHTML` otherwise drops
inline `<script>` tags).

## Customization

### Spectrum broadening

```python
# Change broadening type
widget.broadening = "lorentzian"  # Options: "none", "lorentzian", "gaussian"

# Adjust peak width (FWHM in cm⁻¹)
widget.fwhm = 20.0
```

### Display range

```python
# Set the wavenumber range
widget.x_min = 500    # Minimum wavenumber (cm⁻¹)
widget.x_max = 3500   # Maximum wavenumber (cm⁻¹)
```

### Toggle display elements

```python
widget.show_table = True   # Show/hide frequency table
widget.show_plot = True    # Show/hide spectrum plot
```

## Examples

The `examples/` directory has runnable notebooks and scripts:

- [`ir_widget_example.ipynb`](examples/ir_widget_example.ipynb) — Jupyter example
- [`ir_widget_example.py`](examples/ir_widget_example.py) — Marimo example with
  interactive controls, PsiAPI H₃O⁺ calculation, and an orbital selector
- [`mo_test.py`](examples/mo_test.py) — Marimo scratch notebook for testing
  the orbital/mode dropdown viewers against pre-computed benzene data
  (`benzene_data.json` + `Psi_a_*-A.cube` files)

```bash
pixi run marimo edit examples/ir_widget_example.py
# or
pixi run jupyter lab examples/ir_widget_example.ipynb
```

See also `docs/GETTING_STARTED.md` and `docs/IMPLEMENTATION_SUMMARY.md`.

## Supported File Formats

The widget uses [cclib](https://cclib.github.io/) to parse quantum chemistry output files. Supported formats include:

- **Gaussian** (.log, .out, .fchk)
- **ORCA** (.out)
- **Psi4** (.out)
- **NWChem** (.out)
- **GAMESS** (.log, .out)
- **Q-Chem** (.out)
- **Molpro** (.out)
- **MOPAC** (.out)
- **And many more!**

File formats are automatically detected by cclib. For Psi4 specifically,
prefer `load_from_psi4_wfn`/`run_psi4_frequency` over file parsing — the
direct PsiAPI path also gives you atom geometry and normal modes for 3-D
visualization, which cclib's parsed output does not.

## Comparison with OpenChemistry

This widget is inspired by the [openchemistrypy](https://github.com/OpenChemistry/openchemistrypy) module but offers several advantages:

| Feature | IR Widget | OpenChemistry |
|---------|-----------|---------------|
| Server required | ❌ No | ✅ Yes (Girder) |
| File parsing | ✅ Direct (cclib) | 🔄 Upload to server |
| Dependencies | Minimal | Complex |
| Jupyter support | ✅ Yes | ✅ Yes |
| Marimo support | ✅ Yes | ❌ No |
| Customizable plots | ✅ Yes | Limited |
| 3-D structure/mode/orbital viewer | ✅ Yes | Limited |

## Data Access

Access the parsed vibrational data programmatically:

```python
data = widget.data

print(f"Formula: {data['formula']}")
print(f"Number of modes: {data['n_modes']}")

for mode in data['modes']:
    print(f"Mode {mode['mode']}: {mode['frequency']:.2f} cm⁻¹, "
          f"Intensity: {mode['intensity']:.4f} km/mol")

# Only present when loaded via load_from_psi4_wfn / run_psi4_frequency:
if 'atoms' in data:
    print(f"Atoms: {[a['symbol'] for a in data['atoms']]}")
    print(f"Mode 0 has displacement vectors: {'displacements' in data['modes'][0]}")
```

## Widget Properties

### `IRWidget`

#### Input Properties
- `file_path` (str): Path to quantum chemistry output file (parsed via cclib)
- `data` (dict): Vibrational data dictionary (read/write) — `modes`,
  `formula`, `n_modes`, and optionally `atoms` and per-mode `displacements`
  (populated only by the Psi4 data path)

#### Display Properties
- `show_table` (bool): Display frequency table (default: True)
- `show_plot` (bool): Display spectrum plot (default: True)

#### Spectrum Properties
- `broadening` (str): Broadening type - "none", "lorentzian", or "gaussian" (default: "lorentzian")
- `fwhm` (float): Full-width at half-maximum in cm⁻¹ (default: 15.0)
- `x_min` (float): Minimum wavenumber in cm⁻¹ (default: 400.0)
- `x_max` (float): Maximum wavenumber in cm⁻¹ (default: 4000.0)
- `resolution` (float): Spectrum resolution in points per cm⁻¹ (default: 1.0)

#### Output Properties
- `error_message` (str): Error message if file parsing or calculation fails

#### Methods
- `load_file(file_path)` / `file_path=...` — parse via cclib
- `load_data(frequencies, intensities=None, formula="")` — load arrays directly
- `load_from_psi4_wfn(wfn)` — load from a Psi4 wavefunction (PsiAPI)
- `run_psi4_frequency(geometry, method_basis, ...)` — run Psi4 and load the result

### `MolVisualizerWidget`

Plain Python factory (not itself an anywidget) built from an `IRWidget.data`
dict. Its `view_*` methods return either a `py3Dmol.view` (displays directly
in Jupyter; auto-wrapped in an iframe in Marimo) or one of three anywidget
subclasses — `LinkedViewWidget`, `ModeViewWidget`, `OrbitalViewWidget` — for
the dropdown-driven variants. See [3-D Molecular Visualization](#3-d-molecular-visualization) above.

## Development

The package (`ir_widget/`) consists of:

- `widget.py`: `IRWidget` — Python backend with cclib and Psi4 integration
- `mol_visualizer.py`: `MolVisualizerWidget` and its anywidget subclasses —
  py3Dmol-based 3-D structure/mode/orbital viewers
- `ir_widget.js` / `ir_widget.css`: frontend + styling for the IR table/spectrum

### Testing

Run the automated test suite (pytest, ~2 seconds, includes a real Psi4
frequency calculation on H₂):
```bash
pixi run pytest
```

## License

This project is provided as-is for educational and research purposes.

## Acknowledgments

- Inspired by [openchemistrypy](https://github.com/OpenChemistry/openchemistrypy)
- Powered by [cclib](https://cclib.github.io/) for quantum chemistry file parsing
- Powered by [Psi4](https://psicode.org/) for direct wavefunction/frequency data
- 3-D visualization via [py3Dmol](https://3dmol.org/) / 3Dmol.js
- Built with [anywidget](https://anywidget.dev/)
