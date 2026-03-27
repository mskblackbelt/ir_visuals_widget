import marimo

__generated_with = "0.21.1"
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


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import matplotlib.pyplot as plt
    # %matplotlib inline
    return Path, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # IR Vibrational Spectroscopy Widget

    This widget displays IR vibrational frequencies and spectra from quantum chemistry
    calculations. Vibrational data can come from:

    - **PsiAPI** – run Psi4 directly in the notebook (recommended for Psi4 1.10+)
    - **cclib** – parse saved output files (Gaussian, ORCA, NWChem, …)
    - **Arrays** – supply frequencies and intensities directly

    ## Example 1: Running a Psi4 calculation with PsiAPI

    The simplest workflow — set up a geometry, pick a method/basis, and let
    the widget run the frequency calculation and load the results automatically.
    """)
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
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Example 2: Using an existing Psi4 wavefunction

    If you have already run `psi4.frequency(..., return_wfn=True)` in your notebook,
    pass the wavefunction directly to `load_from_psi4_wfn`. This avoids rerunning the
    (potentially expensive) QM calculation.

    ```python
    import psi4

    mol = psi4.geometry("\""
      C
      H 1 1.089
      H 1 1.089 2 109.471
      H 1 1.089 2 109.471 3 120.0
      H 1 1.089 2 109.471 3 -120.0
    "\"")

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
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Example 3: Loading data from a saved output file (cclib)

    For non-Psi4 codes (Gaussian, ORCA, NWChem, …) or Psi4 output files from
    older versions, use `load_file`:
    """)
    return


@app.cell
def _(IRWidget, np):
    # Example: Load from file
    # widget = IRWidget(file_path="path/to/your/calculation.log")

    # For demonstration, we'll use synthetic data

    # Simulate water molecule IR spectrum
    frequencies = np.array([1595.0, 3657.0, 3756.0])
    intensities = np.array([75.0, 20.0, 45.0])

    widget_h2o = IRWidget()
    widget_h2o.load_data(frequencies, intensities, formula="H2O")
    widget_h2o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Example 4: Benzene-like molecule with controls

    A more complex molecule with interactive display controls:
    """)
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
    return frequencies_benzene, intensities_benzene


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
    return broadening_select, fwhm_slider, show_plot_toggle, show_table_toggle


@app.cell
def _(
    IRWidget,
    broadening_select,
    frequencies_benzene,
    fwhm_slider,
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
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
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
    """)
    return


@app.cell
def _(Path):
    import psi4

    # Clean up any Psi4 scratch files left from previous runs
    for file in Path().glob('psi.*.clean'):
        file.unlink()

    # psi4.set_memory('2 GB')
    # psi4.set_num_threads(2)
    psi4.core.set_output_file('h3o_freq.dat', False)
    return (psi4,)


@app.cell
def _(psi4):
    # H₃O⁺: charge = +1, singlet; start from a planar C₂ᵥ-ish geometry
    h3o = psi4.geometry("""
      1 1
      O  0.0000  0.0000  0.0000
      H  0.9200 -0.5300  0.0000
      H -0.9200 -0.5200  0.0000
      H  0.0000  1.0600  0.0000
    """)

    psi4.set_options({'reference': 'rhf'})

    # Step 1 — optimise to the C₃ᵥ minimum
    psi4.optimize('hf/6-31g(d,p)', molecule=h3o)

    # Step 2 — harmonic frequencies; return_wfn gives us the wavefunction
    energy, wfn = psi4.frequency('hf/6-31g(d,p)', molecule=h3o, return_wfn=True)
    print(f'HF/6-31G(d,p) energy: {energy:.6f} Eh')
    return (wfn,)


@app.cell
def _(IRWidget, wfn):
    # Load frequencies, IR intensities, normal-mode vectors, and atom
    # coordinates directly from the wavefunction — no file I/O needed.
    widget_h3o = IRWidget()
    widget_h3o.load_from_psi4_wfn(wfn)
    widget_h3o.broadening = 'lorentzian'
    widget_h3o.fwhm = 20.0
    widget_h3o
    return (widget_h3o,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Inspecting the Results

    All vibrational data are available in `widget_h3o.data`, including
    Cartesian displacement vectors (`displacements`) and equilibrium atom
    coordinates (`atoms`) extracted directly from the wavefunction.
    """)
    return


@app.cell
def _(widget_h3o):
    data = widget_h3o.data

    print(f"Molecule : {data['formula']}")
    print(f"Modes    : {data['n_modes']}")
    if 'atoms' in data:
        print(f"Atoms    : {len(data['atoms'])}")
    print()
    print(f"{'Mode':>4}  {'Freq (cm\u207b\u00b9)':>13}  {'Intensity (km/mol)':>18}  Displacements")
    print("─" * 58)
    for mode in data['modes']:
        has_d = 'yes' if 'displacements' in mode else 'no'
        print(f"{mode['mode']:>4}  {mode['frequency']:>13.2f}  {mode['intensity']:>18.4f}  {has_d}")
    return (data,)


@app.cell
def _(data, np, plt):
    # Static Lorentzian-broadened IR spectrum via matplotlib.
    # Useful for publication figures and saving to disk.
    freqs  = [m['frequency']  for m in data['modes']]
    intens = [m['intensity']  for m in data['modes']]

    x_range = np.linspace(200, 4200, 5000)
    fwhm_plot = 20.0
    gamma = fwhm_plot / 2

    spectrum = np.zeros_like(x_range)
    for freq, inten in zip(freqs, intens):
        spectrum += inten * gamma**2 / ((x_range - freq)**2 + gamma**2)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(x_range, spectrum / spectrum.max(), color='steelblue', linewidth=1.5)

    # Conventional IR plot: high wavenumber on the left
    ax.invert_xaxis()
    ax.set_xlim(4200, 200)
    ax.set_xlabel('Wavenumber (cm\u207b\u00b9)', fontsize=12)
    ax.set_ylabel('Relative intensity', fontsize=12)
    ax.set_title(
        f"IR Spectrum \u2014 {data['formula']}  "
        f"(HF/6-31G(d,p), Lorentzian FWHM\u2009=\u2009{fwhm_plot}\u2009cm\u207b\u00b9)",
        fontsize=12,
    )
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Other Ways to Load Data

    | Method | When to use |
    |--------|-------------|
    | `widget.load_from_psi4_wfn(wfn)` | After `psi4.frequency(..., return_wfn=True)` — recommended for Psi4 1.10+ |
    | `widget.run_psi4_frequency(geom, method_basis)` | One-shot: runs Psi4 and loads results in a single call |
    | `widget.load_file(path)` | Parses a saved output file via cclib (Gaussian, ORCA, NWChem, …) |
    | `widget.load_data(freqs, intens)` | Supply arrays directly — useful for testing or literature data |
    """)
    return


@app.cell
def _():
    # One-shot convenience runner (sets up Psi4, runs, loads automatically)
    # widget = IRWidget()
    # widget.run_psi4_frequency(
    #     geometry='\n  O\n  H 1 0.96\n  H 1 0.96 2 104.5\n',
    #     method_basis='hf/sto-3g',
    # )

    # Load from a saved Psi4 / Gaussian / ORCA output file (via cclib)
    # widget = IRWidget(file_path='sample_data/planar_h3o.log')

    # Supply arrays directly
    # widget = IRWidget()
    # widget.load_data([1000, 1640, 3530, 3640], [120, 45, 30, 80], formula='H3O+')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Molecular Visualization

    The `MolVisualizerWidget` uses [py3Dmol](https://github.com/3dmol/3Dmol.js/tree/master/py3Dmol) (backed by 3Dmol.js) to display an interactive ball-and-stick model and animate vibrational modes — no Jupyter extension needed, just a CDN script load.

    > **Note:** PsiAPI data (`load_from_psi4_wfn` / `run_psi4_frequency`) is required — these methods populate the `atoms` and `displacements` fields that the visualizer needs.
    """)
    return


@app.cell
def _(widget_h3o):
    from ir_widget import MolVisualizerWidget

    # MolVisualizerWidget takes the same .data dict produced by IRWidget
    vis = MolVisualizerWidget(widget_h3o.data)
    print(f"H3O+ has {len(vis.data['atoms'])} atoms and {len(vis.data['modes'])} vibrational modes")
    return (vis,)


@app.cell
def _(vis):
    # --- Static structure: ball-and-stick model of H3O+ ---
    vis.view_structure()
    return


@app.cell
def _(widget_h3o):
    # --- List available modes with frequencies ---
    for i, m in enumerate(widget_h3o.data['modes']):
        print(f"Mode {i:2d}: {m['frequency']:8.1f} cm\u207b\u00b9  intensity {m['intensity']:7.1f} km/mol")
    return


@app.cell
def _(vis, widget_h3o):
    # --- Animate the highest-intensity mode ---
    # Adjust mode_index, amplitude, or n_frames as desired.
    best_mode = max(range(len(widget_h3o.data['modes'])),
                    key=lambda i: widget_h3o.data['modes'][i]['intensity'])

    vis.view_mode(
        mode_index=best_mode,
        amplitude=0.6,   # Å — exaggerated for visibility
        n_frames=30,
    )
    return


@app.cell
def _(vis):
    # --- Linked spectrum + molecular animation panel ---
    vis.view_linked(amplitude=0.6, fwhm=15.0)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Molecular Orbital Visualization

    `view_orbital()` renders dual ±isosurface lobes from a Gaussian `.cube` file.
    Generate cube files with `psi4.cubeprop()` before calling this:

    ```python
    psi4.set_options({'cubeprop_tasks': ['orbitals'],
                      'cubeprop_orbitals': [4, 5, 6]})
    psi4.cubeprop(wfn)              # writes e.g. Psi_a_005_5-A1.cube
    vis.view_orbital('Psi_a_005_5-A1.cube', isovalue=0.05)
    ```

    Positive lobe: blue. Negative lobe: red. Both `isovalue`, `opacity`, and colours are adjustable.
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
