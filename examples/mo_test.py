import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    """Imports and setup."""
    import json
    import pathlib
    import sys
    import anywidget
    import traitlets as tr

    # Make the ir_widget package importable when running from examples/
    _root = pathlib.Path(__file__).parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    from ir_widget import MolVisualizerWidget

    return MolVisualizerWidget, anywidget, json, pathlib, tr


@app.cell
def _(anywidget, tr):
    """
    Minimal anywidget with only a dropdown — no 3Dmol, no async.
    Tests whether anywidget dropdowns work at all in this Marimo version.
    A red-bordered box with a 3-option dropdown should appear.
    """
    _SIMPLE_JS = r"""
    function render({ model, el }) {
      const labels = model.get('_labels');
      el.style.cssText = 'font-family:sans-serif;padding:8px;border:2px solid red;display:inline-block;';

      const title = document.createElement('p');
      title.textContent = 'Dropdown test — ' + labels.length + ' options:';
      title.style.cssText = 'margin:0 0 4px;font-weight:bold;';

      const sel = document.createElement('select');
      sel.style.cssText = 'padding:4px;font-size:13px;';
      labels.forEach((lbl, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = lbl;
        sel.appendChild(opt);
      });

      el.appendChild(title);
      el.appendChild(sel);
    }
    export default { render };
    """

    class SimpleDropdown(anywidget.AnyWidget):
        _esm = _SIMPLE_JS
        _labels = tr.List(tr.Unicode()).tag(sync=True)

    SimpleDropdown(_labels=["Option A", "Option B", "Option C"])
    return


@app.cell
def _(MolVisualizerWidget, json, pathlib):
    """Load benzene data and discover cube files."""
    _data_file = pathlib.Path("benzene_data.json")
    if not _data_file.exists():
        raise FileNotFoundError("benzene_data.json not found.")

    with open(_data_file) as _f:
        benzene_data = json.load(_f)

    cube_files = sorted(pathlib.Path(".").glob("Psi_a_*_*-A.cube"))
    if not cube_files:
        raise FileNotFoundError("No Psi_a_*_*-A.cube files found.")

    orb_nums = [int(p.stem.split("_")[2]) for p in cube_files]
    vis_benz = MolVisualizerWidget(benzene_data)

    homo_num = 21  # benzene nalpha
    homo_idx = orb_nums.index(homo_num) if homo_num in orb_nums else len(orb_nums) // 2

    print(f"Loaded: {benzene_data['formula']}, {len(benzene_data['atoms'])} atoms")
    print(f"Cube files: orbitals {orb_nums}, HOMO at index {homo_idx}")
    return cube_files, homo_idx, vis_benz


@app.cell
def _(vis_benz):
    """Ball-and-stick structure — known working baseline."""
    vis_benz.view_structure()
    return


@app.cell
def _(vis_benz):
    """Mode selector — known working dropdown for comparison."""
    vis_benz.view_mode_selector(amplitude=2.0)
    return


@app.cell
def _(cube_files, homo_idx, vis_benz):
    """Orbital selector — should show a dropdown above the 3Dmol viewer."""
    vis_benz.view_orbital_selector(
        cube_files,
        homo_index=homo_idx,
        isovalue=0.02,
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
