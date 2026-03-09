import pathlib
import anywidget
import traitlets
import numpy as np


class IRWidget(anywidget.AnyWidget):
    """
    A widget for displaying IR vibrational frequencies and spectra from
    quantum chemistry calculation output files.
    
    Uses cclib to parse various quantum chemistry output formats
    (Gaussian, ORCA, Psi4, NWChem, etc.) and extract vibrational data.
    """
    
    _esm = pathlib.Path(__file__).parent / "ir_widget.js"
    _css = pathlib.Path(__file__).parent / "ir_widget.css"
    
    # Input/Output traits
    file_path = traitlets.Unicode("").tag(sync=True)
    data = traitlets.Dict({}).tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    
    # Display options
    show_table = traitlets.Bool(True).tag(sync=True)
    show_plot = traitlets.Bool(True).tag(sync=True)
    
    # Spectrum options
    broadening = traitlets.Enum(
        ["none", "lorentzian", "gaussian"],
        default_value="lorentzian"
    ).tag(sync=True)
    fwhm = traitlets.Float(15.0).tag(sync=True)  # Full-width at half-maximum in cm⁻¹
    x_min = traitlets.Float(400.0).tag(sync=True)  # Minimum wavenumber
    x_max = traitlets.Float(4000.0).tag(sync=True)  # Maximum wavenumber
    resolution = traitlets.Float(1.0).tag(sync=True)  # Points per cm⁻¹
    
    def __init__(self, file_path=None, **kwargs):
        super().__init__(**kwargs)
        if file_path:
            self.file_path = file_path
            self.load_file(file_path)
    
    @traitlets.observe("file_path")
    def _on_file_path_change(self, change):
        """Automatically load data when file_path changes."""
        new_path = change["new"]
        if new_path:
            self.load_file(new_path)
    
    def load_file(self, file_path):
        """
        Load and parse a quantum chemistry output file using cclib.
        
        Parameters
        ----------
        file_path : str or Path
            Path to the calculation output file
        """
        try:
            import cclib
            
            self.error_message = ""
            
            # Parse the file
            parser = cclib.io.ccread(str(file_path))
            
            if parser is None:
                self.error_message = f"Unable to parse file: {file_path}"
                self.data = {}
                return
            
            # Extract vibrational data
            if not hasattr(parser, "vibfreqs"):
                self.error_message = "No vibrational frequency data found in file"
                self.data = {}
                return
            
            frequencies = parser.vibfreqs
            
            # IR intensities (may not always be present)
            intensities = None
            if hasattr(parser, "vibirs"):
                intensities = parser.vibirs
            
            # Extract molecular formula if available
            formula = ""
            if hasattr(parser, "atomnos"):
                formula = self._generate_formula(parser.atomnos)
            
            # Prepare data dictionary
            self.data = self._prepare_data(frequencies, intensities, formula)
            
        except ImportError:
            self.error_message = "cclib not installed. Install with: pip install cclib"
            self.data = {}
        except Exception as e:
            self.error_message = f"Error loading file: {str(e)}"
            self.data = {}
    
    def load_data(self, frequencies, intensities=None, formula=""):
        """
        Load vibrational data directly (without parsing a file).
        
        Parameters
        ----------
        frequencies : array-like
            Vibrational frequencies in cm⁻¹
        intensities : array-like, optional
            IR intensities in km/mol
        formula : str, optional
            Molecular formula
        """
        self.error_message = ""
        self.data = self._prepare_data(
            np.array(frequencies),
            np.array(intensities) if intensities is not None else None,
            formula
        )
    
    def _prepare_data(self, frequencies, intensities, formula):
        """
        Prepare vibrational data for transfer to frontend.
        
        Parameters
        ----------
        frequencies : ndarray
            Vibrational frequencies in cm⁻¹
        intensities : ndarray or None
            IR intensities in km/mol
        formula : str
            Molecular formula
            
        Returns
        -------
        dict
            Data dictionary with frequencies, intensities, and metadata
        """
        n_modes = len(frequencies)
        
        # If no intensities provided, use uniform values
        if intensities is None:
            intensities = np.ones(n_modes)
        
        # Ensure arrays are the same length
        if len(intensities) != n_modes:
            # Pad or truncate intensities to match frequencies
            if len(intensities) < n_modes:
                intensities = np.pad(
                    intensities,
                    (0, n_modes - len(intensities)),
                    constant_values=0
                )
            else:
                intensities = intensities[:n_modes]
        
        # Create mode data
        modes = []
        for i, (freq, intensity) in enumerate(zip(frequencies, intensities)):
            modes.append({
                "mode": i + 1,
                "frequency": float(freq),
                "intensity": float(intensity)
            })
        
        return {
            "modes": modes,
            "formula": formula,
            "n_modes": n_modes
        }
    
    def _generate_formula(self, atomnos):
        """
        Generate molecular formula from atomic numbers.
        
        Parameters
        ----------
        atomnos : array-like
            Atomic numbers
            
        Returns
        -------
        str
            Molecular formula (e.g., "C6H6")
        """
        from collections import Counter
        
        # Element symbols by atomic number
        elements = [
            "", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
            "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
            "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
            "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
            "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
            "Sb", "Te", "I", "Xe"
        ]
        
        # Count atoms
        atom_counts = Counter(atomnos)
        
        # Common ordering: C, H, then alphabetical
        formula_parts = []
        
        # Carbon first
        if 6 in atom_counts:
            count = atom_counts[6]
            formula_parts.append(f"C{count if count > 1 else ''}")
            del atom_counts[6]
        
        # Hydrogen second
        if 1 in atom_counts:
            count = atom_counts[1]
            formula_parts.append(f"H{count if count > 1 else ''}")
            del atom_counts[1]
        
        # Rest alphabetically
        for atomno in sorted(atom_counts.keys()):
            if atomno < len(elements):
                symbol = elements[atomno]
                count = atom_counts[atomno]
                formula_parts.append(f"{symbol}{count if count > 1 else ''}")
        
        return "".join(formula_parts)
