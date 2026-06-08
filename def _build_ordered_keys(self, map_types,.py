def _build_ordered_keys(self, map_types, sens_map_types, base_signal_names, has_fft, prefix=''):
    """
    Single source of truth for CSV file order AND header order.
    
    Args:
        map_types       (set)  : set of available map types (e.g. {'AVG', 'MAX', 'RMS'})
        sens_map_types  (set)  : set of available sensitivity map types
        base_signal_names(list): list of signal name strings
        has_fft         (bool) : whether FFT is enabled
        prefix          (str)  : 'Standalone_' for standalone mode, '' for normal mode
    
    Returns:
        list of (csv_key, header_name) tuples in the exact order files will be loaded
    """
    signal_order = ['AVG', 'MAX', 'MIN', 'P2P', 'RMS']
    entries = []

    # Build signal entries (type-major order matching natsort of filenames)
    for sig_type in signal_order:
        if sig_type in map_types:
            for sig_name in base_signal_names:
                entries.append((f"{prefix}{sig_type}", f"{sig_name}_{sig_type}"))
        if sig_type in sens_map_types:
            for sig_name in base_signal_names:
                entries.append((f"{prefix}{sig_type}_Sens", f"{sig_name}_{sig_type}_Sens"))

    # Build FFT entries (if enabled)
    if has_fft:
        if 'FFT' in map_types:
            for sig_name in base_signal_names:
                entries.append((f"{prefix}FFT", f"{sig_name}_FFT"))
        if 'FFT' in sens_map_types:
            for sig_name in base_signal_names:
                entries.append((f"{prefix}FFT_Sens", f"{sig_name}_FFT_Sens"))

    return entries


def get_headers(self, fileLog, csv_maps_dir, csv_time_series_dir):
    """
    Build signal and FFT headers, and store self.entries as single source
    of truth for file-to-header mapping used by load_matrices.

    Args:
        fileLog             (object) : fileLog class object
        csv_maps_dir        (str)    : path to CSV_MAPS directory
        csv_time_series_dir (str)    : path to CSV_TIME_SERIES directory

    Returns:
        signal_headers (list) : ordered list of signal header strings
        fft_headers    (list) : ordered list of FFT header strings
    """
    signal_headers = []
    fft_headers    = []
    
    # Check if FFT is enabled in JSON config
    has_fft = dp.JSON.get('FFT', False)

    # Get available map types from CSV_MAPS directory
    map_files = [f for f in dp.os.listdir(csv_maps_dir) if f.endswith('_Map.csv')]
    map_types = set()
    sens_map_types = set()

    #?------------------------------------------------
    #? Standalone case
    #?------------------------------------------------
    if dp.standalone_exist:

        for f in map_files:
            name = f.replace('_Map.csv', '').replace('Standalone_', '')
            if name.endswith('_Sens'):
                sens_map_types.add(name.replace('_Sens', ''))
            else:
                map_types.add(name)

        # Get base signal names from time series CSV (skip Time column)
        time_series_files = fileLog.natsort_files(csv_time_series_dir, standalone=True)
        if time_series_files:
            df = dp.pd.read_csv(time_series_files[0])
            base_signal_names = df.columns[1:].tolist()
            # Sanitize names for filename compatibility
            base_signal_names = [dp.re.sub(r'[^a-zA-Z0-9]', '_', n) for n in base_signal_names]
        else:
            base_signal_names = []

        # Build entries (single source of truth)
        self.entries = self._build_ordered_keys(
            map_types, sens_map_types, base_signal_names, has_fft,
            prefix='Standalone_'
        )

    #?------------------------------------------------
    #? Normal case
    #?------------------------------------------------
    else:

        for f in map_files:
            name = f.replace('_Map.csv', '')
            if name.endswith('_Sens'):
                sens_map_types.add(name.replace('_Sens', ''))
            else:
                map_types.add(name)

        # Get base signal names from JSON header files
        header_path = dp.os.getcwd().replace("\\", "/") + "/Script/assets/Headers/"
        
        mat_names = [
            "Peak_Currents", "RMS_Currents",
            "AVG_Currents", "Peak_Voltages",
            "RMS_Voltages", "AVG_Voltages",
            "Dissipations", "Elec_Stats",
            "Temps", "Thermal_Stats",
            "P2P_Currents", "P2P_Voltages"
        ]

        base_signal_names = []
        for name in mat_names:
            json_path = dp.os.path.join(header_path, f"{name}.json")
            if dp.os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    headers = dp.json.load(f)
                    if isinstance(headers, list):
                        base_signal_names.extend(headers)
                    else:
                        base_signal_names.append(headers)

        # Build entries (single source of truth)
        self.entries = self._build_ordered_keys(
            map_types, sens_map_types, base_signal_names, has_fft,
            prefix=''
        )

    # Derive signal_headers and fft_headers from self.entries
    signal_headers = [h for (key, h) in self.entries if 'FFT' not in key]
    fft_headers    = [h for (key, h) in self.entries if 'FFT' in key]

    return signal_headers, fft_headers


def load_matrices(self, csv_maps_dir, signal_headers=None, fft_headers=None):
    """
    Load CSV files and organize them by type using self.entries as the
    single source of truth for file-to-header mapping.

    CSV files have no headers - just float data.
    Filename determines type: AVG, RMS, MAX, MIN, FFT, P2P, and optional _Sens suffix.

    Args:
        csv_maps_dir   (str)  : Path to CSV_MAPS directory
        signal_headers (list) : Kept for backward compatibility (unused)
        fft_headers    (list) : Kept for backward compatibility (unused)

    Returns:
        signal_matrices : dict of {csv_key: (matrix, headers_list)}
        fft_matrices    : dict of {csv_key: (matrix, headers_list)}
    """
    from itertools import groupby

    signal_matrices = {}
    fft_matrices = {}

    # Ensure self.entries exists
    if not hasattr(self, 'entries') or not self.entries:
        raise ValueError("self.entries not set. Call get_headers() first.")

    # Group entries by csv_key (each CSV file corresponds to one csv_key)
    for csv_key, group in groupby(self.entries, key=lambda x: x[0]):
        headers = [h for (_, h) in group]
        filename = f"{csv_key}_Map.csv"
        file_path = dp.os.path.join(csv_maps_dir, filename)

        # Skip if file doesn't exist (some types may be missing)
        if not dp.os.path.exists(file_path):
            print(f"Warning: {filename} not found, skipping...")
            continue

        # Load matrix
        df = dp.pd.read_csv(file_path, header=None)
        matrix = df.values.astype(float)

        # Store based on type
        if 'FFT' in csv_key:
            fft_matrices[csv_key] = (matrix, headers)
        else:
            signal_matrices[csv_key] = (matrix, headers)

    return signal_matrices, fft_matrices


def get_sweep_vars(self, Xs):
    """
    Extract sweep variables from sweepvars list Xs.

    Args:
        Xs (list): List of sweep variable values

    Returns:
        dict: Dictionary of {sweep_name: values_list}
    """
    sweep_vars = {}

    for i, x_values in enumerate(Xs, 1):
        if x_values and x_values != [0]:
            sweep_vars[f"X{i}"] = x_values

    return sweep_vars



def graphs_scopes(self, filelog, Xs, signal_headers, fft_headers):
    """
    Generate 2D or 3D simulation plots (including FFT) from matrix and JSON data 
    and export them as interactive HTML reports.
    """
    # Setup paths
    csv_maps_dir = f"{filelog.resultfolder}/CSV_MAPS"
    html_folder = f"{filelog.resultfolder}/HTML_GRAPHS/"
    dp.os.makedirs(html_folder, exist_ok=True)

    # Get sweep configuration from JSON
    sweep_vars = self.get_sweep_vars(Xs)
    sweep_keys = list(sweep_vars.keys())
    sweep_names = dp.JSON["sweepNames"]

    # Load matrices using self.entries (already built in get_headers)
    signal_matrices, fft_matrices = self.load_matrices(csv_maps_dir)
    
    # Rest of your existing code continues...