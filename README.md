# IR Vibrational Spectroscopy Widget

An [anywidget](https://anywidget.dev/) for displaying IR vibrational frequencies and spectra from quantum chemistry calculations in Jupyter and Marimo notebooks.

![IR Widget Screenshot](https://img.shields.io/badge/anywidget-IR_Spectroscopy-blue)

## Features

- 📊 **Interactive frequency table** with sortable columns
- 📈 **IR spectrum visualization** with customizable broadening
- 🔧 **Multiple broadening functions**: stick spectrum, Lorentzian, and Gaussian
- 📁 **Wide format support** via cclib (Gaussian, ORCA, Psi4, NWChem, GAMESS, Q-Chem, and more)
- 🎨 **Clean, scientific styling** optimized for notebooks
- ⚡ **Fast and lightweight** with no external dependencies for plotting
- 🧪 **Sample data included** for 7 common molecules (H₂O, CO₂, CH₄, NH₃, C₂H₄, C₆H₆, C₃H₆O)

## What It Looks Like

The widget displays:
1. **A sortable table** showing mode number, frequency (cm⁻¹), and intensity (km/mol)
2. **An interactive plot** of the IR spectrum with axes labels and gridlines
3. **Customizable broadening** to simulate realistic peak shapes

The table supports click-to-sort on any column, and the plot automatically updates when you change parameters like broadening type or FWHM.

## Installation

This widget requires:
- Python 3.13+
- anywidget
- cclib
- numpy

Install dependencies using pixi:
```bash
pixi install
```

Or with pip:
```bash
pip install anywidget cclib numpy
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

### Loading from a calculation file

```python
from ir_widget import IRWidget

# Load data from a quantum chemistry output file
widget = IRWidget(file_path="molecule.log")
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

### Jupyter Notebook
See [`ir_widget_example.ipynb`](ir_widget_example.ipynb) for a complete Jupyter example.

### Marimo Notebook
See [`ir_widget_example.py`](ir_widget_example.py) for a Marimo example with interactive controls:

```bash
pixi run marimo edit ir_widget_example.py
```

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

File formats are automatically detected by cclib.

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

## Data Access

Access the parsed vibrational data programmatically:

```python
data = widget.data

print(f"Formula: {data['formula']}")
print(f"Number of modes: {data['n_modes']}")

for mode in data['modes']:
    print(f"Mode {mode['mode']}: {mode['frequency']:.2f} cm⁻¹, "
          f"Intensity: {mode['intensity']:.4f} km/mol")
```

## Widget Properties

### Input Properties
- `file_path` (str): Path to quantum chemistry output file
- `data` (dict): Vibrational data dictionary (read/write)

### Display Properties
- `show_table` (bool): Display frequency table (default: True)
- `show_plot` (bool): Display spectrum plot (default: True)

### Spectrum Properties
- `broadening` (str): Broadening type - "none", "lorentzian", or "gaussian" (default: "lorentzian")
- `fwhm` (float): Full-width at half-maximum in cm⁻¹ (default: 15.0)
- `x_min` (float): Minimum wavenumber in cm⁻¹ (default: 400.0)
- `x_max` (float): Maximum wavenumber in cm⁻¹ (default: 4000.0)
- `resolution` (float): Spectrum resolution in points per cm⁻¹ (default: 1.0)

### Output Properties
- `error_message` (str): Error message if file parsing fails

## Development

The widget consists of three main files:

- `ir_widget.py`: Python backend with cclib integration
- `ir_widget.js`: JavaScript frontend for rendering
- `ir_widget.css`: Styling

### Testing

Run the basic test:
```bash
pixi run python -c "from ir_widget import IRWidget; print('Widget loaded successfully')"
```

## License

This project is provided as-is for educational and research purposes.

## Acknowledgments

- Inspired by [openchemistrypy](https://github.com/OpenChemistry/openchemistrypy)
- Powered by [cclib](https://cclib.github.io/) for quantum chemistry file parsing
- Built with [anywidget](https://anywidget.dev/)
