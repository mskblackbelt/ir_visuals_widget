# Changelog

All notable changes to the IR Vibrational Widget project.

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

### Planned Features
- Peak picking and annotation
- Export spectrum as image (PNG, SVG)
- Export data as CSV
- Multiple spectrum overlay for comparison
- Vibrational mode animation
- Integration with 3D molecular structure viewers (e.g., NGLView)
- Experimental spectrum overlay
- Automatic peak assignment suggestions
- Zoom and pan controls for plot
- Isotope effects visualization

### Under Consideration
- Raman spectroscopy support
- Normal mode displacement vector visualization
- Interactive peak labeling
- Spectrum fitting tools
- Database integration for reference spectra

---

## Version History

- **v1.0.0** (2026-02-12) - Initial release with core functionality
