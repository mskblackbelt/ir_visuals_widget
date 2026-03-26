#!/usr/bin/env python
"""Quick test script for the IR widget."""

import sys
from pathlib import Path

# Ensure project root and examples/ are on the path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "examples"))

from ir_widget import IRWidget
from sample_data import get_sample_data, print_molecule_info

print("=" * 60)
print("IR Vibrational Widget - Quick Test")
print("=" * 60)
print()

# Show available molecules
print_molecule_info()

print("\n" + "=" * 60)
print("Testing widget with Acetone data...")
print("=" * 60)

# Test with acetone
data = get_sample_data("ACETONE")
widget = IRWidget()
widget.load_data(data['frequencies'], data['intensities'], formula=data['formula'])

print(f"\n✓ Successfully created widget for {data['name']}")
print(f"✓ Loaded {len(widget.data['modes'])} vibrational modes")
print(f"✓ Formula: {widget.data['formula']}")
print(f"✓ Broadening: {widget.broadening} (FWHM: {widget.fwhm} cm⁻¹)")
print(f"✓ Spectrum range: {widget.x_min} - {widget.x_max} cm⁻¹")

print("\n" + "=" * 60)
print("To use in a notebook, run:")
print("  jupyter lab examples/ir_widget_example.ipynb")
print("  or")
print("  marimo edit examples/ir_widget_example.py")
print("=" * 60)
