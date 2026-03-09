import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # Import the IR widget
    from ir_widget import IRWidget
    return (IRWidget,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # IR Vibrational Spectroscopy Widget

        This widget displays IR vibrational frequencies and spectra from quantum chemistry calculations.
        It uses **cclib** to parse various output formats (Gaussian, ORCA, Psi4, etc.).

        ## Example 1: Loading data from a file

        If you have a quantum chemistry output file, you can load it directly:
        """
    )
    return


@app.cell
def _(IRWidget):
    # Example: Load from file
    # widget = IRWidget(file_path="path/to/your/calculation.log")
    
    # For demonstration, we'll use synthetic data
    import numpy as np
    
    # Simulate water molecule IR spectrum
    # Water has 3 normal modes: symmetric stretch, bend, asymmetric stretch
    frequencies = np.array([1595.0, 3657.0, 3756.0])
    intensities = np.array([75.0, 20.0, 45.0])
    
    widget_h2o = IRWidget()
    widget_h2o.load_data(frequencies, intensities, formula="H2O")
    widget_h2o
    return frequencies, intensities, np, widget_h2o


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Example 2: Benzene-like molecule

        Here's a more complex molecule with multiple vibrational modes:
        """
    )
    return


@app.cell
def _(IRWidget, np):
    # Simulate a benzene-like molecule with more modes
    np.random.seed(42)
    
    # Generate realistic IR frequencies for an organic molecule
    n_modes = 30
    frequencies_benzene = np.concatenate([
        np.random.uniform(400, 800, 8),    # Low frequency modes
        np.random.uniform(900, 1600, 12),  # Mid frequency modes
        np.random.uniform(2800, 3100, 10), # CH stretch modes
    ])
    frequencies_benzene = np.sort(frequencies_benzene)
    
    # Generate intensities with some variation
    intensities_benzene = np.random.exponential(30, n_modes)
    
    widget_benzene = IRWidget()
    widget_benzene.load_data(frequencies_benzene, intensities_benzene, formula="C6H6")
    widget_benzene.broadening = "lorentzian"
    widget_benzene.fwhm = 20.0
    widget_benzene
    return (
        frequencies_benzene,
        intensities_benzene,
        n_modes,
        widget_benzene,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Widget Controls

        You can customize the display and spectrum parameters:
        """
    )
    return


@app.cell
def _(mo):
    # Create controls for widget parameters
    broadening_select = mo.ui.dropdown(
        options=["none", "lorentzian", "gaussian"],
        value="lorentzian",
        label="Broadening type"
    )
    
    fwhm_slider = mo.ui.slider(
        start=5,
        stop=50,
        step=5,
        value=15,
        label="FWHM (cm⁻¹)"
    )
    
    show_table_toggle = mo.ui.checkbox(
        value=True,
        label="Show frequency table"
    )
    
    show_plot_toggle = mo.ui.checkbox(
        value=True,
        label="Show spectrum plot"
    )
    
    mo.hstack([
        mo.vstack([broadening_select, fwhm_slider]),
        mo.vstack([show_table_toggle, show_plot_toggle])
    ])
    return (
        broadening_select,
        fwhm_slider,
        show_plot_toggle,
        show_table_toggle,
    )


@app.cell
def _(
    IRWidget,
    broadening_select,
    fwhm_slider,
    frequencies_benzene,
    intensities_benzene,
    show_plot_toggle,
    show_table_toggle,
):
    # Create widget with controls
    widget_controlled = IRWidget()
    widget_controlled.load_data(frequencies_benzene, intensities_benzene, formula="C6H6")
    widget_controlled.broadening = broadening_select.value
    widget_controlled.fwhm = fwhm_slider.value
    widget_controlled.show_table = show_table_toggle.value
    widget_controlled.show_plot = show_plot_toggle.value
    widget_controlled
    return (widget_controlled,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Using with real calculation files

        To load a real quantum chemistry output file:

        ```python
        from ir_widget import IRWidget

        # Supported formats: Gaussian, ORCA, Psi4, NWChem, GAMESS, etc.
        widget = IRWidget(file_path="molecule.log")
        widget
        ```

        ### Adjusting the spectrum range

        ```python
        widget.x_min = 500    # Minimum wavenumber (cm⁻¹)
        widget.x_max = 4000   # Maximum wavenumber (cm⁻¹)
        widget.broadening = "lorentzian"
        widget.fwhm = 15.0    # Full-width at half-maximum
        ```

        ### Accessing the data

        ```python
        # Get the parsed data
        data = widget.data

        # Access frequencies and intensities
        for mode in data['modes']:
            print(f"Mode {mode['mode']}: {mode['frequency']:.2f} cm⁻¹, "
                  f"Intensity: {mode['intensity']:.4f} km/mol")
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()
