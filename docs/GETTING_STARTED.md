# Getting Started with IR Vibrational Widget

## 1. Quick Test (30 seconds)

Run the quick test to verify everything works:

```bash
pixi run python quick_test.py
```

You should see a list of available sample molecules and a successful test result.

## 2. Try in Marimo (Interactive Notebook)

Launch the Marimo example notebook:

```bash
pixi run marimo edit ir_widget_example.py
```

This will open an interactive notebook in your browser where you can:
- See live examples with sample data
- Adjust broadening parameters with sliders
- Toggle table and plot display
- Experiment with different molecules

## 3. Try in Jupyter

Launch the Jupyter notebook:

```bash
pixi run jupyter lab ir_widget_example.ipynb
```

This notebook includes step-by-step examples and explanations.

## 4. Use in Your Own Code

### Simple Example

```python
from ir_widget import IRWidget
from sample_data import get_sample_data

# Use pre-loaded sample data
data = get_sample_data("H2O")
widget = IRWidget()
widget.load_data(data['frequencies'], data['intensities'], data['formula'])
widget
```

### Load Your Own Calculation

```python
from ir_widget import IRWidget

# Load from a quantum chemistry output file
widget = IRWidget(file_path="path/to/your/calculation.log")
widget
```

Supported file formats (via cclib):
- Gaussian (.log, .out, .fchk)
- ORCA (.out)
- Psi4 (.out)
- NWChem (.out)
- GAMESS (.log, .out)
- Q-Chem (.out)
- And many more!

### Customize the Display

```python
# Change broadening
widget.broadening = "gaussian"  # Options: "none", "lorentzian", "gaussian"
widget.fwhm = 20.0              # Peak width in cm⁻¹

# Adjust spectrum range
widget.x_min = 500    # Start at 500 cm⁻¹
widget.x_max = 3500   # End at 3500 cm⁻¹

# Hide/show components
widget.show_table = True   # Show frequency table
widget.show_plot = True    # Show spectrum plot
```

## 5. Explore Sample Data

See what molecules are available:

```python
from sample_data import print_molecule_info

# List all available molecules
print_molecule_info()

# Get details on a specific molecule
print_molecule_info("BENZENE")
```

Available samples:
- **H2O** - Water (3 modes)
- **CO2** - Carbon Dioxide (3 modes)
- **CH4** - Methane (4 modes)
- **NH3** - Ammonia (4 modes)
- **C2H4** - Ethylene (11 modes)
- **BENZENE** - Benzene (20 modes)
- **ACETONE** - Acetone (14 modes)

## 6. Access Data Programmatically

```python
# Get the parsed data
data = widget.data

# Access molecular formula
print(f"Formula: {data['formula']}")

# Iterate through vibrational modes
for mode in data['modes']:
    freq = mode['frequency']
    intensity = mode['intensity']
    print(f"Mode {mode['mode']}: {freq:.2f} cm⁻¹, {intensity:.4f} km/mol")
```

## Common Use Cases

### Compare Different Molecules

```python
from ir_widget import IRWidget
from sample_data import get_sample_data

# Create widgets for different molecules
molecules = ["H2O", "NH3", "CH4"]

for mol in molecules:
    data = get_sample_data(mol)
    widget = IRWidget()
    widget.load_data(data['frequencies'], data['intensities'], data['formula'])
    display(widget)  # In Jupyter
    # or just: widget  # In Marimo
```

### Adjust Spectrum for Publication

```python
# Create a clean spectrum for publication
widget = IRWidget(file_path="molecule.log")

# Use Gaussian broadening with moderate width
widget.broadening = "gaussian"
widget.fwhm = 15.0

# Focus on fingerprint region
widget.x_min = 600
widget.x_max = 1800

# Show only the plot (hide table)
widget.show_table = False
widget.show_plot = True
```

### Analyze Specific Regions

```python
# Focus on C-H stretching region
widget.x_min = 2800
widget.x_max = 3200

# Focus on carbonyl region
widget.x_min = 1600
widget.x_max = 1800
```

## Troubleshooting

### Widget doesn't display
Make sure you're in a Jupyter or Marimo notebook environment. The widget won't render in a regular Python script.

### File parsing fails
Check that:
1. cclib is installed: `pixi run python -c "import cclib; print(cclib.__version__)"`
2. The file contains vibrational frequency data
3. The file format is supported by cclib

### Spectrum looks wrong
Try adjusting:
- `broadening` type (try "lorentzian" instead of "none")
- `fwhm` value (typical range: 10-30 cm⁻¹)
- `x_min` and `x_max` to zoom into the relevant region

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
- Explore the example notebooks for more ideas
- Try loading your own quantum chemistry calculation files!

## Getting Help

If you encounter issues:
1. Check that all dependencies are installed: `pixi install`
2. Run the quick test: `pixi run python quick_test.py`
3. Try the example notebooks to see if they work
4. Check the cclib documentation for supported file formats

Happy spectroscopy! 📊🔬
