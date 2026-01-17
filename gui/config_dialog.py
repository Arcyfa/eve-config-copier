from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from pathlib import Path

from eve_backend.config_store import ConfigStore
from eve_backend.path_detector import PathDetector


class ConfigureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ECC - Configure EVE paths')
        self.resize(600, 150)

        layout = QVBoxLayout(self)

        # Load existing config or discovered defaults
        self.config = ConfigStore().load() or {}
        discovered = PathDetector().discover()
        default_logs = ''
        default_dat = ''
        if discovered:
            default_logs = discovered[0].get('logs', '')
            default_dat = discovered[0].get('dat_root', '') or ''

        # logs path
        hl = QHBoxLayout()
        hl.addWidget(QLabel('Launcher logs root:'))
        self.logs_edit = QLineEdit(self.config.get('logs_root', default_logs))
        hl.addWidget(self.logs_edit)
        b = QPushButton('Browse')
        b.clicked.connect(lambda: self._choose(self.logs_edit))
        hl.addWidget(b)
        layout.addLayout(hl)

        # dat root
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel('DAT root:'))
        self.dat_edit = QLineEdit(self.config.get('dat_root', default_dat))
        hl2.addWidget(self.dat_edit)
        b2 = QPushButton('Browse')
        b2.clicked.connect(lambda: self._choose(self.dat_edit))
        hl2.addWidget(b2)
        layout.addLayout(hl2)

        # buttons: Test | Save | Cancel
        bl = QHBoxLayout()
        self.test_btn = QPushButton('Test')
        self.test_btn.clicked.connect(self._on_test)
        bl.addWidget(self.test_btn)
        bl.addStretch()
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self._on_save)
        bl.addWidget(save_btn)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        bl.addWidget(cancel_btn)
        layout.addLayout(bl)

    def _choose(self, edit: QLineEdit):
        p = QFileDialog.getExistingDirectory(self, 'Select folder', str(Path.home()))
        if p:
            edit.setText(p)

    def _on_test(self):
        logs = self.logs_edit.text().strip()
        dat = self.dat_edit.text().strip()
        msgs = []
        if logs and Path(logs).is_dir():
            msgs.append('Logs path OK')
        else:
            msgs.append('Logs path missing or invalid')
        if dat and Path(dat).is_dir():
            msgs.append('DAT path OK')
        else:
            msgs.append('DAT path missing or invalid')
        QMessageBox.information(self, 'Test result', '\n'.join(msgs))

    def _on_save(self):
        logs = self.logs_edit.text().strip()
        dat = self.dat_edit.text().strip()
        if not logs or not Path(logs).is_dir():
            QMessageBox.critical(self, 'Error', 'Launcher logs path is invalid or missing')
            return
        if not dat or not Path(dat).is_dir():
            QMessageBox.critical(self, 'Error', 'DAT root path is invalid or missing')
            return
        cfg = {'logs_root': logs, 'dat_root': dat}
        ConfigStore().save(cfg)
        self.accept()
