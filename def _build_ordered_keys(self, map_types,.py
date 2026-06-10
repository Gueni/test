def _build_ordered_keys(self, map_types, sens_map_types, base_signal_names,
                         has_fft, prefix='', mat_name_headers=None):
    """
    Single source of truth for CSV file order AND header order.
    Called by get_headers (to build self.entries) and used by load_matrices.

    Args:
        map_types         (set)  : available map type stems
        sens_map_types    (set)  : available sensitivity map type stems
        base_signal_names (list) : signal names — standalone mode only
        has_fft           (bool) : whether FFT is enabled
        prefix            (str)  : 'Standalone_' for standalone, '' for normal
        mat_name_headers  (dict) : normal mode only — ordered {mat_name: [headers]}
                                   key order must match natsort of actual files

    Returns:
        list of (csv_key, header_name) tuples in exact file-load order
    """
    entries = []

    #?------------------------------------------------
    #? Standalone mode
    #? type-major order, signal names from time series CSV
    #?------------------------------------------------
    if prefix == 'Standalone_':
        signal_order = ['AVG', 'FIRST', 'LAST', 'MAX', 'MIN', 'P2P', 'RMS']

        for sig_type in signal_order:
            if sig_type in map_types:
                for sig_name in base_signal_names:
                    entries.append((f"Standalone_{sig_type}", f"{sig_name}_{sig_type}"))
            if sig_type in sens_map_types:
                for sig_name in base_signal_names:
                    entries.append((f"Standalone_{sig_type}_Sens", f"{sig_name}_{sig_type}_Sens"))

        if has_fft:
            if 'FFT' in map_types:
                for sig_name in base_signal_names:
                    entries.append(('Standalone_FFT', f"{sig_name}_FFT"))
            if 'FFT' in sens_map_types:
                for sig_name in base_signal_names:
                    entries.append(('Standalone_FFT_Sens', f"{sig_name}_FFT_Sens"))

    #?------------------------------------------------
    #? Normal mode
    #? one file per matrix name, headers from JSON
    #? mat_name_headers key order = natsort of actual files
    #?------------------------------------------------
    else:
        for mat_name, headers in mat_name_headers.items():
            is_fft = 'FFT' in mat_name.upper()

            if is_fft:
                continue  # FFT handled separately below

            if mat_name in map_types:
                for h in headers:
                    entries.append((mat_name, h))

            if f"{mat_name}_Sens" in map_types:
                for h in headers:
                    entries.append((f"{mat_name}_Sens", f"{h}_Sens"))

        # FFT entries at the end
        if has_fft and mat_name_headers:
            for fft_name in ['FFT_Current', 'FFT_Voltage']:
                if fft_name in map_types and fft_name in mat_name_headers:
                    for h in mat_name_headers[fft_name]:
                        entries.append((fft_name, h))

            if 'FFT_Sens' in map_types and 'FFT_Sens' in mat_name_headers:
                for h in mat_name_headers['FFT_Sens']:
                    entries.append(('FFT_Sens', h))

    return entries


def get_headers(self, fileLog, csv_maps_dir, csv_time_series_dir):
    """
    Build signal and FFT header lists and store self.entries as the single
    source of truth for file-to-header mapping used by load_matrices.

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
    has_fft        = dp.JSON['FFT']

    # Get all map files and derive mat_order from natsort — this IS the load order
    map_files = [f for f in dp.os.listdir(csv_maps_dir) if f.endswith('_Map.csv')]
    map_files = dp.natsort.natsorted(map_files)
    mat_order = [f.replace('_Map.csv', '') for f in map_files]

    map_types      = set()
    sens_map_types = set()

    #?------------------------------------------------
    #? Standalone mode
    #?------------------------------------------------
    if dp.standalone_exist:

        for name in mat_order:
            clean = name.replace('Standalone_', '')
            if clean.endswith('_Sens'):
                sens_map_types.add(clean.replace('_Sens', ''))
            else:
                map_types.add(clean)

        # Get base signal names from time series CSV, skip first column (Time)
        df                = dp.pd.read_csv(fileLog.natsort_files(csv_time_series_dir, standalone=True)[0])
        base_signal_names = df.columns[1:].tolist()
        base_signal_names = [dp.re.sub(r'[^a-zA-Z0-9]', '_', n) for n in base_signal_names]

        self.entries = self._build_ordered_keys(
            map_types, sens_map_types, base_signal_names,
            has_fft, prefix='Standalone_'
        )

    #?------------------------------------------------
    #? Normal mode
    #?------------------------------------------------
    else:

        for name in mat_order:
            if name.endswith('_Sens'):
                sens_map_types.add(name.replace('_Sens', ''))
            else:
                map_types.add(name)

        # Load headers from JSON files in natsort file order
        header_path = (dp.os.getcwd()).replace("\\", "/") + "/Script/assets/Headers/"

        mat_name_headers = {}
        for name in mat_order:
            json_path = dp.os.path.join(header_path, f"{name}.json")
            if dp.os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    headers = dp.json.load(f)
                    mat_name_headers[name] = headers if isinstance(headers, list) else [headers]

        # Add sensitivity FFT headers if they exist
        if has_fft and dp.JSON["perturbation"] != 0 and dp.JSON["nvars"] is None:
            sens_fft_path = dp.os.path.join(header_path, "FFT_Sens.json")
            if dp.os.path.exists(sens_fft_path):
                with open(sens_fft_path, 'r') as f:
                    headers = dp.json.load(f)
                    mat_name_headers['FFT_Sens'] = headers if isinstance(headers, list) else [headers]

        self.entries = self._build_ordered_keys(
            map_types, sens_map_types, base_signal_names=[],
            has_fft=has_fft, prefix='',
            mat_name_headers=mat_name_headers
        )

    # Derive final header lists from self.entries
    signal_headers = [h for (key, h) in self.entries if 'FFT' not in key]
    fft_headers    = [h for (key, h) in self.entries if 'FFT'     in key]

    return signal_headers, fft_headers


def load_matrices(self, csv_maps_dir, signal_headers, fft_headers):
    """
    Load CSV map files and organize by type using self.entries as the
    single source of truth for file-to-header mapping.

    CSV files have no headers — just float data.
    Filename determines type: AVG, RMS, MAX, MIN, FFT, P2P, and optional _Sens suffix.

    Args:
        csv_maps_dir   (str)  : path to CSV_MAPS directory
        signal_headers (list) : kept for call-site compatibility, not used internally
        fft_headers    (list) : kept for call-site compatibility, not used internally

    Returns:
        signal_matrices : dict of {csv_key: (matrix, headers_list)}
        fft_matrices    : dict of {csv_key: (matrix, headers_list)}
    """
    from itertools import groupby

    signal_matrices = {}
    fft_matrices    = {}

    # Print for debug — can be removed later
    csv_files = dp.natsort.natsorted(
        [f for f in dp.os.listdir(csv_maps_dir) if f.endswith('_Map.csv')]
    )
    print("csvmaps = ", csv_files)

    for csv_key, group in groupby(self.entries, key=lambda x: x[0]):
        headers   = [h for (_, h) in group]
        filename  = f"{csv_key}_Map.csv"
        file_path = dp.os.path.join(csv_maps_dir, filename)

        if not dp.os.path.exists(file_path):
            continue

        df     = dp.pd.read_csv(file_path, header=None)
        matrix = df.values.astype(float)

        if 'FFT' in csv_key:
            fft_matrices[csv_key] = (matrix, headers)
        else:
            signal_matrices[csv_key] = (matrix, headers)

    return signal_matrices, fft_matrices