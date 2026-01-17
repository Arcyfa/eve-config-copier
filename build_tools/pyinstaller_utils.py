# pyinstaller_utils.py
"""Utilities for PyInstaller compatibility."""

import sys
import os
from pathlib import Path


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_app_data_dir():
    """Get application data directory for storing config/logs/cache."""
    if sys.platform.startswith('win'):
        data_dir = Path(os.environ['APPDATA']) / 'EVE Config Copier'
    elif sys.platform == 'darwin':
        data_dir = Path.home() / 'Library' / 'Application Support' / 'EVE Config Copier'
    else:  # Linux and other Unix-like
        data_dir = Path.home() / '.local' / 'share' / 'EVE Config Copier'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def setup_portable_paths():
    """Setup paths for portable (bundled) application."""
    app_dir = get_app_data_dir()
    
    # Create subdirectories
    (app_dir / 'logs').mkdir(exist_ok=True)
    (app_dir / 'cache').mkdir(exist_ok=True)
    (app_dir / 'backups').mkdir(exist_ok=True)
    (app_dir / 'cache' / 'char').mkdir(exist_ok=True)
    (app_dir / 'cache' / 'corp').mkdir(exist_ok=True)
    (app_dir / 'cache' / 'img').mkdir(exist_ok=True)
    (app_dir / 'cache' / 'img' / 'char').mkdir(exist_ok=True)
    (app_dir / 'cache' / 'img' / 'corp').mkdir(exist_ok=True)
    
    return app_dir