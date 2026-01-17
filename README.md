# EVE Config Copier (ECC)

A GUI application for copying EVE Online character settings between profiles and characters.

## Features

- Scan EVE installation to discover characters and accounts
- Copy character-specific settings between characters
- Copy account settings with fine-grained control
- Create new profiles with template files
- Support for both Tranquility (main) and Singularity (test) servers
- Character portrait and corporation logo caching

## 📦 Download Pre-Built Executables

**🚀 Get the latest release here:** **[Releases Page](https://github.com/Arcyfa/eve-config-copier/releases/latest)**

Choose the appropriate file for your platform:
- **Windows**: `*windows*.zip` 
- **Linux**: `*linux*.tar.gz` or `*linux*.zip`
- **macOS**: `*macos*.tar.gz` or `*macos*.zip`

✅ **No Python installation required** - these are standalone executables!

### Installation from Release:
1. Download the appropriate file for your platform
2. Extract the archive to your desired location
3. Run the executable directly:
   - **Windows**: Double-click `EVE-Config-Copier.exe`
   - **Linux/macOS**: Run `./EVE-Config-Copier` from terminal or file manager

## 🛠️ Development Setup

For developers who want to run from source:

### Quick Start

```bash
# create venv and install
./venv_setup.sh

# activate
source .venv/bin/activate

# run GUI
python main.py
```

The GUI will attempt to load `mappings.json` from the current working directory by default and provides a "Scan" button which runs the project's `Scanner` to regenerate `mappings.json` (you can also run it manually with `python -m eve_backend.scanner`).
