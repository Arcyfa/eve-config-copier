#!/usr/bin/env python3
"""Simple Qt6 GUI to view `mappings.json` and refresh via extractor.

Requires `PySide6` (see `requirements.txt`).
"""
import os
import json
import sys
from pathlib import Path

# Truncate backend log file at startup to avoid huge logs accumulating.
# Honor EVE_BACKEND_LOG_FILE if set, otherwise default to logs/eve_backend.log
logs_dir = Path.cwd() / 'logs'
logs_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
log_file = os.getenv('EVE_BACKEND_LOG_FILE') or (logs_dir / 'eve_backend.log')
try:
    # open in write mode to truncate
    open(log_file, 'w').close()
except Exception:
    # silent on failure
    pass

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import QThread
from PySide6.QtGui import QIcon

from eve_backend.path_detector import PathDetector
from gui.worker import ScanWorker
from gui.widgets import StatusIndicator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('EVE Config Copier (ECC)')
        self.resize(700, 500)
        
        # Set the application icon
        icon_path = Path(__file__).parent / 'icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # main central widget and layout
        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)

        # middle area: tab widget
        from PySide6.QtWidgets import QTabWidget
        from gui.all_characters import AllCharactersTab
        from gui.copy_config import CopyConfigTab
        from gui.backup_tab import BackupTab
        from gui.help_tab import HelpTab

        tabs = QTabWidget()
        self.all_chars_tab = AllCharactersTab(main_window=self)
        tabs.addTab(self.all_chars_tab, 'All Characters')
        self.copy_config_tab = CopyConfigTab()
        tabs.addTab(self.copy_config_tab, 'Copy Config')
        self.backup_tab = BackupTab()
        tabs.addTab(self.backup_tab, 'Backup')
        self.help_tab = HelpTab()
        tabs.addTab(self.help_tab, 'Help')
        layout.addWidget(tabs, 1)

        # status bar at bottom with two indicators
        status = QStatusBar()
        self.setStatusBar(status)
        self.settings_indicator = StatusIndicator('Eve Settings found:')
        self.mappings_indicator = StatusIndicator('Acc, Chars found:')
        status.addPermanentWidget(self.settings_indicator)
        status.addPermanentWidget(self.mappings_indicator)

        # default path
        self.mappings_path = Path.cwd() / 'mappings.json'
        # initialize indicators
        self.update_indicators()

    def update_indicators(self):
        # check for settings
        pd = PathDetector()
        found = pd.discover()
        has_settings = len(found) > 0
        # also check persisted config
        from eve_backend.config_store import ConfigStore
        cfg = ConfigStore().load()
        cfg_has = bool(cfg.get('logs_root') and cfg.get('dat_root'))
        final_has = has_settings or cfg_has
        self.settings_indicator.set_status(final_has, f'Found: {len(found)} root(s)')
        # check mappings.json presence
        has_mappings = self.mappings_path.exists()
        self.mappings_indicator.set_status(has_mappings, 'mappings.json present' if has_mappings else '')
        # enable/disable scan depending on whether settings are present
        if hasattr(self.all_chars_tab, 'scan_btn'):
            self.all_chars_tab.scan_btn.setEnabled(final_has)

    def open_configure(self):
        from gui.config_dialog import ConfigureDialog
        dlg = ConfigureDialog(self)
        if dlg.exec():
            # saved; refresh indicators
            self.update_indicators()

    # GUI no longer displays mappings contents; removed file open and tree view

    def run_extractor_and_reload(self):
        # run Scanner in background via ScanWorker
        if hasattr(self.all_chars_tab, 'scan_btn'):
            self.all_chars_tab.scan_btn.setEnabled(False)
            self.all_chars_tab.scan_btn.setText('Scanning...')
        self._thread = QThread()
        self._worker = ScanWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.started.connect(lambda: None)
        self._worker.progress.connect(lambda msg: None)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_worker_error(self, err: str):
        QMessageBox.critical(self, 'Extractor error', err)
        if hasattr(self.all_chars_tab, 'scan_btn'):
            self.all_chars_tab.scan_btn.setEnabled(True)
            self.all_chars_tab.scan_btn.setText('Scan')

    def _on_worker_finished(self, result):
        # result is ScanResult from backend
        if getattr(result, 'success', False):
            # update indicators and reload tabs
            self.all_chars_tab.reload()
            self.copy_config_tab.reload()
        else:
            QMessageBox.warning(self, 'Scan', f'Scan failed: {getattr(result, "errors", [])}')
        if hasattr(self.all_chars_tab, 'scan_btn'):
            self.all_chars_tab.scan_btn.setEnabled(True)
            self.all_chars_tab.scan_btn.setText('Scan')
        self.update_indicators()


def main(argv):
    app = QApplication(argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
