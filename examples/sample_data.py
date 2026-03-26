"""
Sample IR vibrational data for testing the IR widget.

This module provides realistic vibrational frequency data for common molecules
extracted from literature and computational chemistry calculations.
"""

import numpy as np

# Sample data for common molecules
SAMPLE_MOLECULES = {
    "H2O": {
        "formula": "H2O",
        "name": "Water",
        "frequencies": np.array([1595.0, 3657.0, 3756.0]),
        "intensities": np.array([75.0, 20.0, 45.0]),
        "description": "Water molecule with 3 normal modes"
    },
    
    "CO2": {
        "formula": "CO2",
        "name": "Carbon Dioxide",
        "frequencies": np.array([667.4, 1340.0, 2349.0]),
        "intensities": np.array([80.0, 0.0, 280.0]),
        "description": "CO2 with symmetric stretch, bend (2x), and asymmetric stretch"
    },
    
    "CH4": {
        "formula": "CH4",
        "name": "Methane",
        "frequencies": np.array([1306.0, 1534.0, 2917.0, 3019.0]),
        "intensities": np.array([0.0, 25.0, 0.0, 150.0]),
        "description": "Methane with 4 unique normal modes"
    },
    
    "NH3": {
        "formula": "NH3",
        "name": "Ammonia",
        "frequencies": np.array([950.0, 1627.0, 3337.0, 3444.0]),
        "intensities": np.array([150.0, 75.0, 12.0, 110.0]),
        "description": "Ammonia with 4 unique normal modes"
    },
    
    "C2H4": {
        "formula": "C2H4",
        "name": "Ethylene",
        "frequencies": np.array([
            826.0, 949.0, 1023.0, 1236.0, 1342.0, 1444.0,
            1623.0, 2989.0, 3026.0, 3103.0, 3106.0
        ]),
        "intensities": np.array([
            2.0, 110.0, 8.0, 0.5, 25.0, 5.0,
            12.0, 0.8, 22.0, 7.0, 80.0
        ]),
        "description": "Ethylene with 11 unique normal modes"
    },
    
    "BENZENE": {
        "formula": "C6H6",
        "name": "Benzene",
        "frequencies": np.array([
            410.0, 607.0, 673.0, 703.0, 849.0, 975.0, 990.0, 1010.0,
            1038.0, 1150.0, 1178.0, 1309.0, 1326.0, 1479.0, 1596.0,
            1606.0, 3047.0, 3064.0, 3073.0, 3089.0
        ]),
        "intensities": np.array([
            0.0, 1.2, 0.0, 25.0, 0.0, 2.5, 0.0, 90.0,
            0.5, 0.0, 15.0, 0.0, 22.0, 8.0, 0.0,
            12.0, 0.0, 35.0, 0.0, 85.0
        ]),
        "description": "Benzene with 20 unique normal modes"
    },
    
    "ACETONE": {
        "formula": "C3H6O",
        "name": "Acetone",
        "frequencies": np.array([
            385.0, 484.0, 530.0, 777.0, 895.0, 1068.0, 1091.0, 1215.0,
            1364.0, 1435.0, 1738.0, 2932.0, 2975.0, 3006.0
        ]),
        "intensities": np.array([
            3.0, 8.0, 12.0, 35.0, 5.0, 25.0, 80.0, 45.0,
            15.0, 22.0, 650.0, 28.0, 15.0, 35.0
        ]),
        "description": "Acetone with 14 unique normal modes (strong C=O stretch at 1738)"
    },
}


def get_sample_data(molecule_key):
    """
    Get sample IR vibrational data for a molecule.
    
    Parameters
    ----------
    molecule_key : str
        Molecule identifier (e.g., "H2O", "CO2", "BENZENE")
        
    Returns
    -------
    dict
        Dictionary containing formula, name, frequencies, intensities, and description
        
    Examples
    --------
    >>> data = get_sample_data("H2O")
    >>> print(data["formula"])
    H2O
    >>> print(data["frequencies"])
    [1595. 3657. 3756.]
    """
    if molecule_key not in SAMPLE_MOLECULES:
        available = ", ".join(SAMPLE_MOLECULES.keys())
        raise ValueError(f"Unknown molecule: {molecule_key}. Available: {available}")
    
    return SAMPLE_MOLECULES[molecule_key].copy()


def list_available_molecules():
    """
    List all available sample molecules.
    
    Returns
    -------
    list
        List of available molecule keys
    """
    return list(SAMPLE_MOLECULES.keys())


def print_molecule_info(molecule_key=None):
    """
    Print information about available sample molecules.
    
    Parameters
    ----------
    molecule_key : str, optional
        Specific molecule to print info for. If None, prints all.
    """
    if molecule_key is None:
        print("Available sample molecules:")
        print("-" * 60)
        for key in SAMPLE_MOLECULES:
            data = SAMPLE_MOLECULES[key]
            print(f"{key:10s} - {data['name']:15s} ({data['formula']})")
            print(f"           {len(data['frequencies'])} modes: {data['description']}")
            print()
    else:
        if molecule_key not in SAMPLE_MOLECULES:
            available = ", ".join(SAMPLE_MOLECULES.keys())
            print(f"Unknown molecule: {molecule_key}")
            print(f"Available: {available}")
            return
        
        data = SAMPLE_MOLECULES[molecule_key]
        print(f"Molecule: {data['name']} ({data['formula']})")
        print(f"Description: {data['description']}")
        print(f"\nVibrational modes ({len(data['frequencies'])}):")
        print("-" * 50)
        print(f"{'Mode':<6} {'Frequency (cm⁻¹)':<20} {'Intensity (km/mol)':<20}")
        print("-" * 50)
        
        for i, (freq, intensity) in enumerate(zip(data['frequencies'], data['intensities']), 1):
            print(f"{i:<6} {freq:<20.2f} {intensity:<20.4f}")


if __name__ == "__main__":
    # Demo
    print_molecule_info()
