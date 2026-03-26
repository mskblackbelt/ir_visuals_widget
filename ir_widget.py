import pathlib
import anywidget
import traitlets
import numpy as np

_BOHR_TO_ANGSTROM = 0.52917721067


class IRWidget(anywidget.AnyWidget):
    """
    A widget for displaying IR vibrational frequencies and spectra from
    quantum chemistry calculations.

    Vibrational data can be loaded in three ways:
    - From a Psi4 wavefunction object via PsiAPI (recommended for Psi4 1.10+)
    - By running a Psi4 frequency calculation directly from the widget
    - From quantum chemistry output files via cclib (Gaussian, ORCA, NWChem, etc.)
    - Directly from arrays via load_data()
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

    def load_from_psi4_wfn(self, wfn):
        """
        Load vibrational data from a Psi4 wavefunction after a frequency calculation.

        This is the recommended method for Psi4 1.10+ users. It extracts frequencies,
        IR intensities, normal mode displacement vectors, and atom coordinates directly
        from the wavefunction object returned by ``psi4.frequency(..., return_wfn=True)``.

        Parameters
        ----------
        wfn : psi4.core.Wavefunction
            Wavefunction returned by ``energy, wfn = psi4.frequency(method, return_wfn=True)``

        Examples
        --------
        >>> import psi4
        >>> mol = psi4.geometry(\"\"\"
        ...   O
        ...   H 1 0.96
        ...   H 1 0.96 2 104.5
        ... \"\"\")
        >>> energy, wfn = psi4.frequency('hf/sto-3g', molecule=mol, return_wfn=True)
        >>> widget = IRWidget()
        >>> widget.load_from_psi4_wfn(wfn)
        """
        try:
            import psi4
            from psi4.driver import qcdb

            self.error_message = ""

            mol = wfn.molecule()
            mol.update_geometry()

            n_atoms = mol.natom()
            symbols = [mol.symbol(i) for i in range(n_atoms)]
            masses = np.array([mol.mass(i) for i in range(n_atoms)])
            geom = np.asarray(mol.geometry())           # shape (nat, 3) in Bohr
            hess = np.asarray(wfn.hessian())            # (3*nat, 3*nat) non-mass-weighted, Eh/a0²
            irrep_labels = mol.irrep_labels()

            # Dipole gradient drives IR intensities; may be absent for methods without
            # analytic dipole derivatives (e.g., MP2 finite-difference hessian).
            dipder_raw = wfn.variables().get("CURRENT DIPOLE GRADIENT", None)
            dipder = np.asarray(dipder_raw).T if dipder_raw is not None else None

            # Compute harmonic analysis without triggering Psi4's print routines
            vibinfo, _ = qcdb.vib.harmonic_analysis(
                hess, geom, masses, wfn.basisset(), irrep_labels,
                dipder=dipder, project_trans=True, project_rot=True
            )

            # Keep only vibrational modes (discard translations/rotations)
            vibonly = qcdb.vib.filter_nonvib(vibinfo)

            # Frequencies: complex → signed real (negative = imaginary/TS mode)
            freqs = qcdb.vib.filter_omega_to_real(vibonly["omega"].data)

            # IR intensities (km/mol); None when dipole derivatives unavailable
            intensities = None
            if "IR_intensity" in vibonly and vibonly["IR_intensity"].data is not None:
                ir_data = vibonly["IR_intensity"].data
                if ir_data.size > 0:
                    intensities = ir_data.astype(float)

            # Normal mode Cartesian displacements: (3*nat, n_vib) in Bohr → Angstrom,
            # reshaped to (n_vib, nat, 3) for per-atom indexing in the frontend.
            normal_modes = None
            if "x" in vibonly and vibonly["x"].data is not None:
                x = vibonly["x"].data * _BOHR_TO_ANGSTROM   # (3*nat, n_vib)
                n_vib = x.shape[1]
                normal_modes = x.T.reshape(n_vib, n_atoms, 3).tolist()

            # Atom equilibrium coordinates in Angstrom for 3-D visualisation
            atoms = [
                {
                    "symbol": symbols[i],
                    "x": float(geom[i, 0] * _BOHR_TO_ANGSTROM),
                    "y": float(geom[i, 1] * _BOHR_TO_ANGSTROM),
                    "z": float(geom[i, 2] * _BOHR_TO_ANGSTROM),
                }
                for i in range(n_atoms)
            ]

            formula = self._generate_formula_from_symbols(symbols)
            self.data = self._prepare_data(freqs, intensities, formula, normal_modes, atoms)

        except ImportError:
            self.error_message = (
                "psi4 not available. Activate the psi4 environment before calling this method."
            )
        except Exception as e:
            self.error_message = f"Error loading Psi4 wavefunction: {e}"

    def run_psi4_frequency(self, geometry, method_basis, memory="2 GB", num_threads=1,
                           psi4_options=None, psi4_output_file="psi4_output.dat"):
        """
        Run a Psi4 harmonic frequency calculation and load the results into the widget.

        Parameters
        ----------
        geometry : str
            Psi4 geometry specification (Z-matrix or Cartesian, same syntax as
            ``psi4.geometry()``).
        method_basis : str
            Method and basis set string, e.g. ``'b3lyp/6-31g*'`` or ``'hf/sto-3g'``.
        memory : str, optional
            Memory allocation for Psi4, e.g. ``'4 GB'``.
        num_threads : int, optional
            Number of OpenMP threads for the calculation.
        psi4_options : dict, optional
            Extra Psi4 keyword options passed to ``psi4.set_options()``.
        psi4_output_file : str, optional
            File path for Psi4's text output. Set to ``None`` to suppress output.

        Examples
        --------
        >>> widget = IRWidget()
        >>> widget.run_psi4_frequency(
        ...     geometry=\"\"\"
        ...       O
        ...       H 1 0.96
        ...       H 1 0.96 2 104.5
        ...     \"\"\",
        ...     method_basis='hf/sto-3g',
        ...     memory='2 GB',
        ... )
        """
        try:
            import psi4

            self.error_message = ""

            psi4.set_memory(memory)
            psi4.set_num_threads(num_threads)
            if psi4_output_file:
                psi4.core.set_output_file(psi4_output_file, False)
            if psi4_options:
                psi4.set_options(psi4_options)

            mol = psi4.geometry(geometry)
            _, wfn = psi4.frequency(method_basis, molecule=mol, return_wfn=True)
            self.load_from_psi4_wfn(wfn)

        except ImportError:
            self.error_message = (
                "psi4 not available. Activate the psi4 environment before calling this method."
            )
        except Exception as e:
            self.error_message = f"Psi4 frequency calculation failed: {e}"

    def _prepare_data(self, frequencies, intensities, formula,
                      normal_modes=None, atoms=None):
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
        normal_modes : list of list, optional
            Normal mode Cartesian displacements, shape (n_modes, n_atoms, 3) in Angstrom
        atoms : list of dict, optional
            Atom equilibrium positions: [{"symbol": str, "x": float, "y": float, "z": float}]
            
        Returns
        -------
        dict
            Data dictionary with frequencies, intensities, modes, and optional geometry
        """
        n_modes = len(frequencies)
        
        # If no intensities provided, use uniform values
        if intensities is None:
            intensities = np.ones(n_modes)
        
        # Ensure arrays are the same length
        if len(intensities) != n_modes:
            if len(intensities) < n_modes:
                intensities = np.pad(
                    intensities,
                    (0, n_modes - len(intensities)),
                    constant_values=0
                )
            else:
                intensities = intensities[:n_modes]
        
        modes = []
        for i, (freq, intensity) in enumerate(zip(frequencies, intensities)):
            mode = {
                "mode": i + 1,
                "frequency": float(freq),
                "intensity": float(intensity),
            }
            if normal_modes is not None and i < len(normal_modes):
                mode["displacements"] = normal_modes[i]
            modes.append(mode)
        
        result = {
            "modes": modes,
            "formula": formula,
            "n_modes": n_modes,
        }
        if atoms is not None:
            result["atoms"] = atoms

        return result

    def _generate_formula_from_symbols(self, symbols):
        """
        Generate a molecular formula string from a list of element symbols.

        Parameters
        ----------
        symbols : list of str
            Element symbols, e.g. ['C', 'H', 'H', 'H', 'H']

        Returns
        -------
        str
            Hill-order formula, e.g. 'CH4'
        """
        from collections import Counter
        counts = Counter(symbols)
        parts = []
        for elem in ['C', 'H']:
            if elem in counts:
                n = counts.pop(elem)
                parts.append(f"{elem}{n if n > 1 else ''}")
        for elem in sorted(counts):
            n = counts[elem]
            parts.append(f"{elem}{n if n > 1 else ''}")
        return "".join(parts)

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
        _elements = [
            "", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
            "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
            "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
            "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
            "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
            "Sb", "Te", "I", "Xe",
        ]
        symbols = [_elements[n] for n in atomnos if 0 < n < len(_elements)]
        return self._generate_formula_from_symbols(symbols)
