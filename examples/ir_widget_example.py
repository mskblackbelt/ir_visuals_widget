import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from ir_widget import IRWidget

    return (IRWidget,)


@app.cell
def _():
    from pathlib import Path
    import numpy as np
    import matplotlib.pyplot as plt

    return Path, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # IR Vibrational Spectroscopy Widget

    This widget displays IR vibrational spectra from quantum chemistry calculations.
    Data can come from **Psi4 PsiAPI**, **cclib** (Gaussian/ORCA/NWChem output files),
    or **direct arrays**.

    ## Example 1: Water Molecule (H₂O)

    Water has three IR-active normal modes: bending (~1595 cm⁻¹), symmetric O–H stretch
    (~3657 cm⁻¹), and asymmetric O–H stretch (~3756 cm⁻¹).
    """)
    return


@app.cell
def _(IRWidget, np):
    frequencies = np.array([1595.0, 3657.0, 3756.0])
    intensities = np.array([75.0, 20.0, 45.0])
    widget_h2o = IRWidget()
    widget_h2o.load_data(frequencies, intensities, formula="H₂O")
    widget_h2o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example 2: Hydronium Ion (H₃O⁺) — Psi4 Calculation

    Using PsiAPI we can run a full HF/6-31G(d,p) frequency calculation, loading
    frequencies, intensities, atom coordinates, and normal-mode displacement vectors
    directly from the wavefunction — no file I/O needed.
    """)
    return


@app.cell
def _(Path):
    import psi4
    for f in Path().glob('psi.*.clean'):
        f.unlink()
    psi4.core.set_output_file('h3o_freq.dat', False)
    return (psi4,)


@app.cell
def _(IRWidget, psi4):
    import json, pathlib

    _data_cache = pathlib.Path('h3o_data.json')
    _wfn_cache = pathlib.Path('h3o_wfn')

    if _data_cache.exists() and pathlib.Path('h3o_wfn.npy').exists():
        h3o_data = json.loads(_data_cache.read_text())
        wfn = psi4.core.Wavefunction.from_file(str(_wfn_cache))
        print(f"Restored H3O⁺ from cache ({len(h3o_data['modes'])} modes)")
    else:
        h3o = psi4.geometry("""
          1 1
          O  0.0000  0.0000  0.0000
          H  0.9200 -0.5300  0.0000
          H -0.9200 -0.5200  0.0000
          H  0.0000  1.0600  0.0000
        """)
        psi4.set_options({'reference': 'rhf'})
        psi4.optimize('hf/6-31g(d,p)', molecule=h3o)
        energy, wfn = psi4.frequency('hf/6-31g(d,p)', molecule=h3o, return_wfn=True)
        print(f'HF/6-31G(d,p) energy: {energy:.6f} Eh')

        _tmp = IRWidget()
        _tmp.load_from_psi4_wfn(wfn)
        _data_cache.write_text(json.dumps(_tmp.data))
        wfn.to_file(str(_wfn_cache))
        h3o_data = _tmp.data
    return h3o_data, json, pathlib


@app.cell
def _(IRWidget, h3o_data):
    widget_h3o = IRWidget()
    widget_h3o.data = h3o_data
    widget_h3o.broadening = 'lorentzian'
    widget_h3o.fwhm = 20.0
    widget_h3o
    return (widget_h3o,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Inspecting the Results

    All vibrational data are in `widget_h3o.data`, including Cartesian displacement
    vectors (`displacements`) and equilibrium atom coordinates (`atoms`).
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
    print(f"{'Mode':>4}  {'Freq (cm⁻¹)':>13}  {'Intensity (km/mol)':>18}")
    print("─" * 40)
    for mode in data['modes']:
        print(f"{mode['mode']:>4}  {mode['frequency']:>13.2f}  {mode['intensity']:>18.4f}")
    return (data,)


@app.cell
def _(data, np, plt):
    # Static Lorentzian-broadened spectrum — useful for publication figures
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
    ax.invert_xaxis()
    ax.set_xlim(4200, 200)
    ax.set_xlabel('Wavenumber (cm⁻¹)', fontsize=12)
    ax.set_ylabel('Relative intensity', fontsize=12)
    ax.set_title(
        f"IR Spectrum — {data['formula']}  "
        f"(HF/6-31G(d,p), Lorentzian FWHM = {fwhm_plot} cm⁻¹)",
        fontsize=12,
    )
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Molecular Visualization

    `MolVisualizerWidget` uses 3Dmol.js to display an interactive ball-and-stick model
    and animate vibrational modes. Requires data loaded via `load_from_psi4_wfn` or
    `run_psi4_frequency` (these methods populate atom coordinates and displacements).
    """)
    return


@app.cell
def _(widget_h3o):
    from ir_widget import MolVisualizerWidget
    vis = MolVisualizerWidget(widget_h3o.data)
    print(f"H3O⁺: {len(vis.data['atoms'])} atoms, {len(vis.data['modes'])} vibrational modes")
    return MolVisualizerWidget, vis


@app.cell
def _(vis):
    # Static ball-and-stick structure
    vis.view_structure()
    return


@app.cell
def _(vis):
    # Animated vibrational modes — select from dropdown
    vis.view_mode_selector(amplitude=0.6)
    return


@app.cell
def _(vis):
    # Linked panel: spectrum + animated molecule inset
    vis.view_linked(amplitude=0.6, fwhm=20.0)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example 3: Benzene (C₆H₆) — Psi4 Frequency + Molecular Orbitals

    A larger molecule with 30 vibrational modes. We also run `psi4.cubeprop()` to
    generate `.cube` files for the frontier molecular orbitals (HOMO-2 through LUMO+1),
    then display them interactively with `view_orbital_selector()`.
    """)
    return


@app.cell
def _(IRWidget, json, pathlib, psi4):
    # import json, pathlib

    _data_cache = pathlib.Path('benzene_data.json')
    _wfn_cache = pathlib.Path('benzene_wfn')

    if _data_cache.exists() and pathlib.Path('benzene_wfn.npy').exists():
        benz_data = json.loads(_data_cache.read_text())
        wfn_benz = psi4.core.Wavefunction.from_file(str(_wfn_cache))
        print(f"Restored benzene from cache ({len(benz_data['modes'])} modes)")
    else:
        psi4.core.set_output_file('benzene_freq.dat', False)
        benzene = psi4.geometry("""
          0 1
          C  0.0000  1.3970  0.0000
          C  1.2095  0.6985  0.0000
          C  1.2095 -0.6985  0.0000
          C  0.0000 -1.3970  0.0000
          C -1.2095 -0.6985  0.0000
          C -1.2095  0.6985  0.0000
          H  0.0000  2.4840  0.0000
          H  2.1510  1.2420  0.0000
          H  2.1510 -1.2420  0.0000
          H  0.0000 -2.4840  0.0000
          H -2.1510 -1.2420  0.0000
          H -2.1510  1.2420  0.0000
          symmetry c1
          units angstrom
        """)
        psi4.set_options({'reference': 'rhf', 'basis': '6-31g*', 'scf_type': 'df'})
        psi4.set_memory('4 GB')
        energy_benz, wfn_benz = psi4.frequency('hf/6-31g*', molecule=benzene, return_wfn=True)
        print(f'HF/6-31G* energy: {energy_benz:.6f} Eh')

        _tmp = IRWidget()
        _tmp.load_from_psi4_wfn(wfn_benz)
        _data_cache.write_text(json.dumps(_tmp.data))
        wfn_benz.to_file(str(_wfn_cache))
        benz_data = _tmp.data
    return benz_data, wfn_benz


@app.cell
def _(IRWidget, benz_data):
    widget_benz = IRWidget()
    widget_benz.data = benz_data
    widget_benz.broadening = 'lorentzian'
    widget_benz.fwhm = 15.0
    widget_benz
    return (widget_benz,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Spectrum Display Options

    Adjust broadening type, peak width, and wavenumber range:
    """)
    return


@app.cell
def _(mo):
    broadening_select = mo.ui.dropdown(
        options=["none", "lorentzian", "gaussian"],
        value="lorentzian",
        label="Broadening type",
    )
    fwhm_slider = mo.ui.slider(start=5, stop=50, step=5, value=15, label="FWHM (cm⁻¹)")
    mo.hstack([broadening_select, fwhm_slider])
    return broadening_select, fwhm_slider


@app.cell
def _(IRWidget, broadening_select, fwhm_slider, widget_benz):
    widget_benz_ctrl = IRWidget()
    widget_benz_ctrl.load_data(
        [m['frequency'] for m in widget_benz.data['modes']],
        [m['intensity'] for m in widget_benz.data['modes']],
        formula=widget_benz.data.get('formula', 'C6H6'),
    )
    widget_benz_ctrl.broadening = broadening_select.value
    widget_benz_ctrl.fwhm = fwhm_slider.value
    widget_benz_ctrl
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Molecular Orbital Visualization

    Generate `.cube` files with `psi4.cubeprop()`, then use `view_orbital_selector()`
    to display the orbitals with a dropdown. The HOMO is shown by default.

    For benzene, 42 electrons → 21 alpha electrons → **HOMO = orbital 21**.
    Positive lobes: blue. Negative lobes: red.
    """)
    return


@app.cell
def _(pathlib, psi4, wfn_benz):
    # import pathlib

    homo_num = wfn_benz.nalpha()   # 21 for benzene
    orb_list = list(range(homo_num - 5, homo_num + 6))   # HOMO-2 through LUMO+1
    _ndigits = len(str(max(orb_list)))
    _cube_files = [f'Psi_a_{n:0{_ndigits}d}_{n}-A.cube' for n in orb_list]

    if all(pathlib.Path(f).exists() for f in _cube_files):
        print(f"Using existing cube files for orbitals: {orb_list}")
    else:
        psi4.set_options({
            'cubeprop_tasks': ['orbitals'],
            'cubeprop_orbitals': orb_list,
            'cubic_grid_spacing': [0.2, 0.2, 0.2],
        })
        psi4.cubeprop(wfn_benz)
        print(f"Generated cube files for orbitals: {orb_list}")
    print(f"HOMO is orbital {homo_num}")
    return (orb_list,)


@app.cell
def _(MolVisualizerWidget, orb_list, widget_benz):
    vis_benz = MolVisualizerWidget(widget_benz.data)
    ndigits = len(str(max(orb_list)))
    cube_files = [f'Psi_a_{n:0{ndigits}d}_{n}-A.cube' for n in orb_list]
    print(f"Benzene: {len(vis_benz.data['atoms'])} atoms, {len(vis_benz.data['modes'])} vibrational modes")
    return cube_files, vis_benz


@app.cell
def _(vis_benz):
    vis_benz.view_structure()
    return


@app.cell
def _(cube_files, vis_benz):
    # Orbital viewer with dropdown — HOMO is shown by default
    vis_benz.view_orbital_selector(cube_files, homo_index=5, isovalue=0.02)
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
    # One-shot convenience runner
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
