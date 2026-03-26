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

        This widget displays IR vibrational frequencies and spectra from quantum chemistry
        calculations. Vibrational data can come from:

        - **PsiAPI** – run Psi4 directly in the notebook (recommended for Psi4 1.10+)
        - **cclib** – parse saved output files (Gaussian, ORCA, NWChem, …)
        - **Arrays** – supply frequencies and intensities directly

        ## Example 1: Running a Psi4 calculation with PsiAPI

        The simplest workflow — set up a geometry, pick a method/basis, and let
        the widget run the frequency calculation and load the results automatically.
        """
    )
    return


@app.cell
def _(IRWidget):
    # Run a Psi4 HF/STO-3G frequency calculation on water and display results.
    # The widget handles psi4.geometry(), psi4.frequency(), and data extraction.
    widget_psi4_direct = IRWidget()
    widget_psi4_direct.run_psi4_frequency(
        geometry="""
          O
          H 1 0.96
          H 1 0.96 2 104.5
        """,
        method_basis="hf/sto-3g",
        memory="2 GB",
        num_threads=2,
    )
    widget_psi4_direct
    return (widget_psi4_direct,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Example 2: Using an existing Psi4 wavefunction

        If you have already run `psi4.frequency(..., return_wfn=True)` in your notebook,
        pass the wavefunction directly to `load_from_psi4_wfn`. This avoids rerunning the
        (potentially expensive) QM calculation.

        ```python
        import psi4

        mol = psi4.geometry(\"\"\"
          C
          H 1 1.089
          H 1 1.089 2 109.471
          H 1 1.089 2 109.471 3 120.0
          H 1 1.089 2 109.471 3 -120.0
        \"\"\")

        psi4.set_memory("4 GB")
        psi4.set_num_threads(4)
        psi4.core.set_output_file("ch4_freq.dat", False)

        energy, wfn = psi4.frequency("b3lyp/6-31g*", molecule=mol, return_wfn=True)

        widget = IRWidget()
        widget.load_from_psi4_wfn(wfn)
        widget
        ```

        The widget extracts directly from the wavefunction:
        - **Frequencies** (cm⁻¹, negative values indicate imaginary/transition-state modes)
        - **IR intensities** (km/mol, from dipole derivatives — `None` if unavailable)
        - **Normal mode displacement vectors** (Å, stored per mode as `displacements` in `widget.data`)
        - **Atom coordinates** (Å, stored as `atoms` in `widget.data` for 3-D visualisation)
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Example 3: Loading data from a saved output file (cclib)

        For non-Psi4 codes (Gaussian, ORCA, NWChem, …) or Psi4 output files from
        older versions, use `load_file`:
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
        ## Example 4: Benzene-like molecule with controls

        A more complex molecule with interactive display controls:
        """
    )
    return


@app.cell
def _(IRWidget, np):
    # Simulate a benzene-like molecule with more modes
    np.random.seed(42)

    n_modes = 30
    frequencies_benzene = np.concatenate([
        np.random.uniform(400, 800, 8),
        np.random.uniform(900, 1600, 12),
        np.random.uniform(2800, 3100, 10),
    ])
    frequencies_benzene = np.sort(frequencies_benzene)
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
        ## Accessing vibrational mode data from Python

        After loading from PsiAPI, mode displacement vectors and atom coordinates are
        available in `widget.data`:

        ```python
        data = widget.data

        # Frequencies and intensities
        for mode in data['modes']:
            freq = mode['frequency']   # cm⁻¹
            inten = mode['intensity']  # km/mol
            disps = mode.get('displacements')  # list of [dx, dy, dz] per atom (Å)
            print(f"Mode {mode['mode']}: {freq:.2f} cm⁻¹  {inten:.2f} km/mol")

        # Equilibrium atom positions (Å)
        for atom in data.get('atoms', []):
            print(f"{atom['symbol']}  {atom['x']:.4f}  {atom['y']:.4f}  {atom['z']:.4f}")
        ```

        ### Spectrum display options

        ```python
        widget.x_min = 500       # Minimum wavenumber (cm⁻¹)
        widget.x_max = 4000      # Maximum wavenumber (cm⁻¹)
        widget.broadening = "lorentzian"  # "none", "lorentzian", or "gaussian"
        widget.fwhm = 15.0       # Full-width at half-maximum (cm⁻¹)
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()

