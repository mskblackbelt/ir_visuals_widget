import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import traitlets
    import anywidget
    return anywidget, traitlets


@app.cell
def _(anywidget, traitlets):
    class CounterWidget(anywidget.AnyWidget):
        _esm = "./index.js"
        _css = "./index.css"
        count = traitlets.Int(0).tag(sync=True)

    w = CounterWidget(count=42)
    w
    return (w,)


@app.cell
def _(w):
    w.count * 2
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
