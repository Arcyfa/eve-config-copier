# EVE Config Copier (ECC)

A GUI application for copying EVE Online character settings between profiles and characters.

## Features

- Scan EVE installation to discover characters and accounts
- Copy character-specific settings between characters
- Copy account settings with fine-grained control
- Create new profiles with template files
- Support for both Tranquility (main) and Singularity (test) servers
- Character portrait and corporation logo caching

## Quick Start

Quick instructions to run the Qt6 GUI (creates a virtualenv and installs dependencies):

```bash
# create venv and install
./venv_setup.sh

# activate
source .venv/bin/activate

# run GUI
python main.py
```

The GUI will attempt to load `mappings.json` from the current working directory by default and provides a "Scan" button which runs the project's `Scanner` to regenerate `mappings.json` (you can also run it manually with `python -m eve_backend.scanner`).
