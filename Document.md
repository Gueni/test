# PyPLECS — Setup & Environment Documentation

> **How to use this file:** Each section below corresponds to one Confluence page.
> Add these pages as children of the root `PyPLECS` Confluence space home page (sibling to the `assets` documentation).

---

---

# Page: `wheelhouse/` *(child of `PyPLECS`)*

## Overview

The `wheelhouse` folder is the **local Python package cache** for the PyPLECS project. It stores all pre-downloaded `.whl` (wheel) package files that `install.bat` uses to set up the Python environment — **without any internet connection required**.

This design is intentional: the BMW corporate network restricts direct internet access from developer machines. All packages are pre-downloaded once by the project leader from the BMW internal Nexus PyPI mirror and distributed to the team via a shared BMW Drive link.

## What it contains (when populated)

All `.whl` files listed in `Script/assets/Configuration/requirements.txt`, plus:
- `setuptools==63.2.0`
- `wheel==0.47.0`

These are the exact pinned versions required to run the simulation framework.

## Important rules

| Rule | Detail |
|---|---|
| **Do not commit wheel files to Git** | The `wheelhouse/` folder is listed in `.gitignore`. Wheel files are large binaries and must never be pushed to the repository. |
| **The folder is empty after cloning** | This is expected. You must populate it manually — see the [Onboarding Guide](#) below. |
| **Do not add or remove packages manually** | The wheel set is managed exclusively by the project leader via `download.bat`. |
| **Do not modify `requirements.txt` without coordinating with the project leader** | Adding a new dependency requires the project leader to re-run `download.bat` and update the shared BMW Drive folder. |

## How it gets populated

See the [Onboarding Guide](#) page for step-by-step instructions.

---

---

# Page: `venv/` *(child of `PyPLECS`)*

## Overview

The `venv/` folder is the **Python virtual environment** created locally on each developer's machine by `install.bat`. It is a self-contained Python installation with all project dependencies installed from the `wheelhouse/` folder.

## Important rules

| Rule | Detail |
|---|---|
| **Do not commit to Git** | `venv/` is listed in `.gitignore`. It is machine-specific and must never be pushed. |
| **The folder does not exist after cloning** | This is expected. It is created automatically when you run `install.bat`. |
| **Do not create it manually** | Always use `install.bat` to ensure the correct package versions are installed from `wheelhouse/`. |
| **If the environment breaks** | Delete the `venv/` folder and re-run `install.bat`. |

## Activating the environment manually

If you open a new terminal after the initial setup, activate the environment before running any scripts:

```bat
call venv\Scripts\activate.bat
```

You will see `(venv)` prepended to your terminal prompt when the environment is active.

## Python version requirement

Requires **Python ≥ 3.10.8** (as specified in `pyproject.toml`). Make sure the correct Python version is installed and on your system `PATH` before running `install.bat`.

---

---

# Page: `download.bat` *(child of `PyPLECS`)*

## Overview

`download.bat` is the **project leader's tool** for downloading all required Python wheel packages from the BMW internal Nexus PyPI mirror into a local folder. The resulting wheel files are then uploaded to a shared BMW Drive link for distribution to the team.

> ⚠️ **This script is intended for use by the project leader only.** Team members do not need to run it. Instead, they copy the pre-downloaded wheels from BMW Drive into their local `wheelhouse/` folder and run `install.bat`.

## Script Content

```bat
@echo off

set /P DEST="Please Enter The Path Where You Want To Download The Wheel libraries : "

echo Downloading all libraries in requirements.txt into /Wheelhouse directory...
python -m pip download --no-cache-dir -i https://nexus.bmwgroup.net/repository/pypi/simple -r Script\assets\Configuration\requirements.txt -d "%DEST%"

echo.
echo Libraries .whl packages have been downloaded to : "%DEST%"
pause
```

## What it does — step by step

| Step | Action |
|---|---|
| 1 | Prompts the project leader to enter a destination folder path |
| 2 | Uses `pip download` to fetch all packages listed in `requirements.txt` from the BMW Nexus PyPI mirror (`nexus.bmwgroup.net`) |
| 3 | Saves all `.whl` files to the specified destination folder |
| 4 | Confirms the download location |

## Parameters

| Parameter | Value | Description |
|---|---|---|
| `--no-cache-dir` | — | Bypasses pip's local cache to ensure a clean download |
| `-i` | `https://nexus.bmwgroup.net/repository/pypi/simple` | BMW internal Nexus PyPI mirror (requires BMW VPN or corporate network) |
| `-r` | `Script\assets\Configuration\requirements.txt` | Package list to download |
| `-d` | `%DEST%` (user-entered path) | Destination folder for the `.whl` files |

## Prerequisites

- Must be run on the **BMW corporate network or VPN**
- Python must be installed and on the system `PATH`
- `Script\assets\Configuration\requirements.txt` must be up to date

## After running

The project leader uploads the downloaded `.whl` files to the shared **BMW Drive** folder and updates the team with the link.

---

---

# Page: `install.bat` *(child of `PyPLECS`)*

## Overview

`install.bat` is the **one-click environment setup script** for all team members. It creates a Python virtual environment and installs all project dependencies from the local `wheelhouse/` folder — no internet connection required.

> ✅ **This is the script you run as a developer.** Run it once after cloning the repository and populating `wheelhouse/`.

## Script Content

```bat
@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Setting up setuptools...
pip install --no-index --find-links=wheelhouse setuptools==63.2.0 wheel --upgrade

echo Installing project dependencies...
pip install --no-index --find-links=wheelhouse .

echo.
echo Pyplecs is Ready to be used !
echo call venv\Scripts\activate.bat to activate venv if not done yet
pause
```

## What it does — step by step

| Step | Command | Description |
|---|---|---|
| 1 | `python -m venv venv` | Creates a new Python virtual environment in the `venv/` folder |
| 2 | `call venv\Scripts\activate.bat` | Activates the virtual environment for the current session |
| 3 | `pip install --no-index --find-links=wheelhouse setuptools==63.2.0 wheel --upgrade` | Installs build tooling from `wheelhouse/` (no internet) |
| 4 | `pip install --no-index --find-links=wheelhouse .` | Installs the full PyPLECS project and all its dependencies from `wheelhouse/` using `pyproject.toml` |
| 5 | Prints confirmation message and pauses |

## Key flags

| Flag | Meaning |
|---|---|
| `--no-index` | Disables PyPI lookup entirely — only uses local files |
| `--find-links=wheelhouse` | Tells pip to look for packages in the `wheelhouse/` folder |

## Prerequisites

- **Python ≥ 3.10.8** must be installed and on the system `PATH`
- The `wheelhouse/` folder must be populated with the `.whl` files from BMW Drive (see [Onboarding Guide](#))
- Must be run from the **root of the cloned repository** (where `install.bat` lives)

## After running

- A `venv/` folder is created in the project root
- All packages from `requirements.txt` are installed into it
- To use the environment in a new terminal: `call venv\Scripts\activate.bat`

---

---

# Page: `pyproject.toml` *(child of `PyPLECS`)*

## Overview

`pyproject.toml` is the **Python project configuration file** for PyPLECS. It defines the project metadata, all runtime dependencies, the package discovery rules, and pip's offline installation behaviour. It is the file that `install.bat` reads when running `pip install .`.

## File Content

```toml
[build-system]
requires      = ["setuptools==63.2.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name             = "PyPLECS"
version          = "0.0.1"
description      = "PLECS simulation automation toolkit"
requires-python  = ">=3.10.8"
dependencies     = [
    "numpy==1.22.4"           ,
    "scipy==1.10.1"           ,
    "pandas==2.2.2"           ,
    "sympy==1.12"             ,
    "matplotlib==3.6.2"       ,
    "plotly==5.11.0"          ,
    "json-rpc==1.13.0"        ,
    "jsonrpc-requests==0.4.0" ,
    "natsort==8.2.0"          ,
    "flatdict==4.1.0"         ,
    "unflatten==0.1.1"        ,
    "jinja2==3.1.6"           ,
    "rich==14.2.0"            ,
    "pyfiglet==0.8.post1"     ,
    "psutil==5.9.2"           ,
    "pywin32==304 ; sys_platform == 'win32'"      ,
    "flatten-dict"            ,
    "pywinauto==0.6.8 ; sys_platform == 'win32'"
]

[tool.setuptools.packages.find]
where   = ["."]
include = ["Script*"]

[tool.pip]
find-links = ["wheelhouse"]
no-index   = true
```

## Sections Explained

### `[build-system]`

Declares that the project uses `setuptools` as its build backend, pinned to `63.2.0`. This ensures reproducible builds regardless of the system's default setuptools version.

### `[project]`

| Field | Value | Description |
|---|---|---|
| `name` | `PyPLECS` | Package name |
| `version` | `0.0.1` | Current version |
| `description` | `PLECS simulation automation toolkit` | Short description |
| `requires-python` | `>=3.10.8` | Minimum Python version |
| `dependencies` | *(see table below)* | All runtime dependencies, pinned |

### Dependencies

| Package | Version | Platform | Role |
|---|---|---|---|
| `numpy` | 1.22.4 | All | Numerical arrays |
| `scipy` | 1.10.1 | All | Scientific computing |
| `pandas` | 2.2.2 | All | Data handling |
| `sympy` | 1.12 | All | Symbolic mathematics |
| `matplotlib` | 3.6.2 | All | Static plotting |
| `plotly` | 5.11.0 | All | Interactive HTML charts |
| `json-rpc` | 1.13.0 | All | RPC communication with PLECS |
| `jsonrpc-requests` | 0.4.0 | All | RPC HTTP transport |
| `natsort` | 8.2.0 | All | Natural string sorting |
| `flatdict` | 4.1.0 | All | Nested dict flattening |
| `unflatten` | 0.1.1 | All | Inverse of flatdict |
| `jinja2` | 3.1.6 | All | HTML / text templating |
| `rich` | 14.2.0 | All | Rich terminal output |
| `pyfiglet` | 0.8.post1 | All | ASCII banners |
| `psutil` | 5.9.2 | All | Process/resource monitoring |
| `pywin32` | 304 | Windows only | Windows OS integration |
| `flatten-dict` | latest | All | Additional dict utilities |
| `pywinauto` | 0.6.8 | Windows only | PLECS GUI automation |

> ⚠️ `pywin32` and `pywinauto` are **Windows-only** (`sys_platform == 'win32'`). This project is not supported on Linux or macOS.

### `[tool.setuptools.packages.find]`

Tells setuptools to discover Python packages starting from the repository root (`.`), including only directories whose names start with `Script`. This ensures only the project's source code is packaged, not `venv/`, `wheelhouse/`, etc.

### `[tool.pip]`

| Setting | Value | Effect |
|---|---|---|
| `find-links` | `["wheelhouse"]` | Tells pip to look in `wheelhouse/` for packages |
| `no-index` | `true` | Disables PyPI entirely — all packages must come from `wheelhouse/` |

This is what makes the offline installation via `install.bat` work correctly.

---

---

# Page: Onboarding Guide — Setting Up Your Development Environment *(child of `PyPLECS`)*

## Who this page is for

Every developer joining the PyPLECS project for the first time, or setting up the project on a new machine.

## Prerequisites

Before you start, make sure you have:

- [ ] **Git** installed and configured
- [ ] **Python 3.10.8 or higher** installed and available on your system `PATH`  
      Verify with: `python --version`
- [ ] Access to the **PyPLECS Git repository** (ask your team lead for access)
- [ ] The **BMW Drive link** containing the pre-downloaded wheel files (ask the project leader)
- [ ] A machine connected to the **BMW corporate network or VPN** (required to access BMW Drive)

---

## Step 1 — Clone the repository

Open a terminal (Command Prompt or PowerShell) and clone the repository:

```bat
git clone <repository_url>
cd PyPLECS
```

After cloning, your project root will look like this:

```
PyPLECS/
├── Script/
├── wheelhouse/          ← empty folder (this is expected)
├── venv/                ← does not exist yet (this is expected)
├── download.bat
├── install.bat
├── pyproject.toml
├── README.md
└── ...
```

> ✅ The `wheelhouse/` folder being empty is **normal**. Wheel files are not stored in Git.

---

## Step 2 — Get the wheel files from BMW Drive

**You do not download the wheel files yourself.** The project leader downloads them once using `download.bat` from the BMW internal Nexus mirror and uploads them to a shared folder.

1. Open the **BMW Drive link** provided by your project leader
2. Download all `.whl` files from the shared folder
3. Copy all the `.whl` files into the `wheelhouse/` folder in your cloned repository

After this step, `wheelhouse/` should contain `.whl` files for all packages listed in `Script/assets/Configuration/requirements.txt`.

> ⚠️ Do **not** add, remove, or replace wheel files manually. Use only the files provided by the project leader to ensure version consistency across the team.

---

## Step 3 — Run `install.bat`

From the root of the repository, double-click `install.bat` or run it from the terminal:

```bat
install.bat
```

The script will:

1. Create a Python virtual environment at `venv/`
2. Activate it
3. Install `setuptools` and `wheel` from `wheelhouse/`
4. Install PyPLECS and all its dependencies from `wheelhouse/`

When it finishes, you will see:

```
Pyplecs is Ready to be used !
call venv\Scripts\activate.bat to activate venv if not done yet
```

> ✅ Installation is complete. You do **not** need an internet connection for this step.

---

## Step 4 — Activate the virtual environment

Each time you open a new terminal to work on the project, activate the environment:

```bat
call venv\Scripts\activate.bat
```

You will see `(venv)` at the start of your prompt, confirming the environment is active.

---

## Step 5 — Verify the installation

```bat
python -c "import numpy, pandas, plotly, jsonrpc; print('All dependencies OK')"
```

If no errors appear, your environment is ready.

---

## Workflow summary

```
Project Leader                          Developer (You)
──────────────────                      ──────────────────────────────
runs download.bat          →            clones Git repository
  (BMW Nexus mirror)                    copies .whl files from BMW Drive
uploads .whl files                        into wheelhouse/
  to BMW Drive             →            runs install.bat
                                          → creates venv/
                                          → installs from wheelhouse/
                                        activates venv and starts working
```

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `python` not recognised | Python not on PATH | Re-install Python and check "Add to PATH" during setup |
| `pip install` fails with "No matching distribution found" | A `.whl` file is missing from `wheelhouse/` | Ask the project leader to check the BMW Drive folder for the missing package |
| `venv` already exists but environment seems broken | Partial or corrupted install | Delete the `venv/` folder and re-run `install.bat` |
| `call venv\Scripts\activate.bat` fails | `venv/` does not exist | Run `install.bat` first |
| Script runs but imports fail | Wrong Python version | Ensure Python ≥ 3.10.8 is the active version (`python --version`) |

---

## Who manages the wheel files?

The **project leader** is solely responsible for:

- Running `download.bat` to fetch packages from the BMW Nexus mirror
- Uploading the wheel files to the BMW Drive shared folder
- Updating the wheel set when `requirements.txt` changes
- Notifying the team when a new wheel set is available

If you need a new package added to the project, contact the project leader — **do not attempt to download or install packages independently**, as this breaks the reproducibility of the shared environment.