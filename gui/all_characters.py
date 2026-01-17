from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap, QPainter, QFontMetrics
from PySide6.QtCore import Qt, QThread, QTimer
from pathlib import Path
from typing import Optional
import json

from eve_backend.cache import CacheManager
from eve_backend import Prefetcher
from .prefetch_worker import PrefetchWorker


class CharacterWidget(QWidget):
    def __init__(self, char_id: int, cache: CacheManager, parent=None):
        super().__init__(parent)
        self.char_id = char_id
        self.cache = cache
        self.layout = QVBoxLayout(self)
        self.portrait_label = QLabel()
        self.portrait_label.setFixedSize(80, 80)
        self.portrait_label.setScaledContents(True)
        self.name_label = QLabel(str(char_id))
        # keep name width equal to portrait so it doesn't overflow
        self.name_label.setFixedWidth(self.portrait_label.width())
        self.name_label.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.portrait_label, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.name_label, alignment=Qt.AlignHCenter)
        # keep widget compact so multiple widgets float/pack left instead of stretching
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.refresh()

    def refresh(self):
        # load name from cache if available
        data = self.cache.load_json(str(self.char_id), 'char')
        if data and 'name' in data:
            name = data['name']
            fm = QFontMetrics(self.name_label.font())
            elided = fm.elidedText(name, Qt.ElideRight, self.name_label.width())
            self.name_label.setText(elided)
        else:
            fm = QFontMetrics(self.name_label.font())
            elided = fm.elidedText(str(self.char_id), Qt.ElideRight, self.name_label.width())
            self.name_label.setText(elided)

        pic = self.cache.load_image(str(self.char_id), 'char')
        if pic:
            pix = QPixmap(str(pic))
        else:
            pix = QPixmap(80, 80)
            pix.fill(Qt.lightGray)

        # overlay corp logo if possible
        corp_id = data.get('corporation_id') if data else None
        if corp_id:
            corp_img = self.cache.load_image(str(corp_id), 'corp')
            if corp_img:
                corp_pix = QPixmap(str(corp_img)).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # composite
                composed = QPixmap(pix.size())
                composed.fill(Qt.transparent)
                painter = QPainter(composed)
                painter.drawPixmap(0, 0, pix)
                # draw corp in bottom-right
                x = pix.width() - corp_pix.width() - 4
                y = pix.height() - corp_pix.height() - 4
                painter.drawPixmap(x, y, corp_pix)
                painter.end()
                pix = composed

        self.portrait_label.setPixmap(pix)


class TitleWrap(QWidget):
    """A title row with styled background and a floating delete button.

    The delete button is a child widget positioned in resizeEvent so it visually
    floats over the right edge of the styled background.
    """

    def __init__(self, text: str, on_delete, acc_key: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet('background:#eee; padding:2px;')
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 8, 2)
        self.label = QLabel(text, self)
        self.label.setStyleSheet('font-weight: bold; color:#222;')
        lay.addWidget(self.label)
        lay.addStretch()

        self.del_btn = QPushButton('Delete', self)
        self.del_btn.setToolTip('Delete this account')
        self.del_btn.setFixedWidth(80)
        # make the delete button slightly shorter so the title row is less tall
        self.del_btn.setFixedHeight(20)
        self.del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.del_btn.setStyleSheet('background:#d9534f; color:white; border:none; padding:4px;')
        # wire up callback; capture acc_key
        self.del_btn.clicked.connect(lambda: on_delete(acc_key))
        self.del_btn.raise_()

    def resizeEvent(self, ev):
        # position delete button on the right, vertically centered
        margin = 6
        x = self.width() - self.del_btn.width() - margin
        y = (self.height() - self.del_btn.height()) // 2
        self.del_btn.move(x, y)
        super().resizeEvent(ev)


class AllCharactersTab(QWidget):
    def __init__(self, mappings_path: Optional[str] = None, main_window=None, parent=None):
        super().__init__(parent)
        self.cache = CacheManager()
        self.main_window = main_window
        self.mappings_path = Path(mappings_path) if mappings_path else Path.cwd() / 'mappings.json'
        self.layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        # Left-aligned buttons: Configure, Scan, Prefetch cache
        self.configure_btn = QPushButton('Configure')
        self.configure_btn.clicked.connect(self._on_configure)
        top_bar.addWidget(self.configure_btn)
        
        self.scan_btn = QPushButton('Scan')
        self.scan_btn.clicked.connect(self._on_scan)
        top_bar.addWidget(self.scan_btn)
        
        self.prefetch_btn = QPushButton('Prefetch cache')
        self.prefetch_btn.clicked.connect(self._on_prefetch)
        top_bar.addWidget(self.prefetch_btn)
        
        # Right-aligned elements
        self.delete_all_btn = QPushButton('Delete All')
        self.delete_all_btn.setToolTip('Delete ALL accounts')
        # match height to prefetch button and style red
        dh = self.prefetch_btn.sizeHint().height() or 24
        self.delete_all_btn.setFixedHeight(dh)
        self.delete_all_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.delete_all_btn.setStyleSheet('background:#d9534f; color:white; border:none; padding:4px;')
        self.delete_all_btn.clicked.connect(self._delete_all_accounts)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_label = QLabel('')
        self.progress_label.setVisible(False)
        top_bar.addStretch()
        top_bar.addWidget(self.progress_label)
        top_bar.addWidget(self.progress_bar)
        top_bar.addWidget(self.delete_all_btn)
        self.layout.addLayout(top_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self._thread = None
        self._worker = None
        self._prefetch_total = 0
        self._prefetch_done = 0

        self.reload()

    def reload(self):
        self.container_layout.setAlignment(Qt.AlignTop)
        # clear
        while self.container_layout.count():
            it = self.container_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        if not self.mappings_path.exists():
            self.container_layout.addWidget(QLabel('No mappings.json found'))
            return

        data = None
        try:
            data = json.loads(self.mappings_path.read_text())
        except Exception:
            self.container_layout.addWidget(QLabel('Failed to read mappings.json'))
            return

        mappings = data.get('mappings', {})
        # for each account, create a horizontal row with title and character widgets
        for acc, info in sorted(mappings.items(), key=lambda x: int(x[0])):
            # use TitleWrap which handles background and floating delete button
            title_wrap = TitleWrap(f'Account {acc}', self._delete_account, acc)
            self.container_layout.addWidget(title_wrap)

            chars_row = QHBoxLayout()
            chars_row.setAlignment(Qt.AlignLeft)
            chars_row.setSpacing(8)
            for c in info.get('chars', []):
                cw = CharacterWidget(int(c), self.cache)
                chars_row.addWidget(cw)
            # keep widgets packed to the left by adding a stretch at the end
            chars_row.addStretch()
            wrapper = QWidget()
            wrapper.setLayout(chars_row)
            wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.container_layout.addWidget(wrapper)

    def _on_configure(self):
        """Handle Configure button click by calling main window's configure method."""
        if self.main_window:
            self.main_window.open_configure()
    
    def _on_scan(self):
        """Handle Scan button click by calling main window's scan method."""
        if self.main_window:
            self.main_window.run_extractor_and_reload()
    
    def _on_prefetch(self):
        # start PrefetchWorker in background
        if self._thread and self._thread.isRunning():
            return
        self._thread = QThread()
        self._worker = PrefetchWorker(mappings_path=str(self.mappings_path))
        self._worker.moveToThread(self._thread)
        self._worker.started.connect(self._on_prefetch_started)
        self._worker.progress.connect(self._on_prefetch_progress)
        self._worker.finished.connect(self._on_prefetch_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_prefetch_started(self):
        self.prefetch_btn.setText('Prefetching...')
        self.prefetch_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText('Starting...')

    def _on_prefetch_progress(self, msg: str):
        # update label and progress when possible
        self.progress_label.setText(msg)
        # parse pattern like '(i/total)'
        try:
            if '(' in msg and '/' in msg and ')' in msg:
                part = msg.split('(')[-1].split(')')[0]
                if '/' in part:
                    done, total = part.split('/')
                    done = int(done)
                    total = int(total)
                    self._prefetch_total = total
                    self._prefetch_done = done
                    self.progress_bar.setMaximum(total)
                    self.progress_bar.setValue(done)
            elif msg.startswith('prefetch complete') or msg.startswith('cancelled'):
                self.progress_bar.setValue(self.progress_bar.maximum())
        except Exception:
            pass

    def _on_prefetch_finished(self, result):
        self.prefetch_btn.setText('Prefetch cache')
        self.prefetch_btn.setEnabled(True)
        self.progress_label.setText('Done')
        # leave progress visible briefly; then reload UI to show cached names/images
        self.reload()
        # hide progress UI after a short delay
        try:
            QTimer.singleShot(2000, lambda: (self.progress_bar.setVisible(False), self.progress_label.setVisible(False)))
        except Exception:
            pass

    def _delete_account(self, acc_key: str):
        """Remove the given account key from mappings.json but leave cache files untouched."""
        try:
            if not self.mappings_path.exists():
                return
            text = self.mappings_path.read_text()
            data = json.loads(text)
            mappings = data.get('mappings', {})
            if acc_key in mappings:
                del mappings[acc_key]
                data['mappings'] = mappings
                # write back with indentation for readability
                self.mappings_path.write_text(json.dumps(data, indent=2))
                # refresh UI
                self.reload()
        except Exception:
            # on error, do not crash UI; silently ignore (could be improved)
            return

    def _delete_all_accounts(self):
        """Remove all accounts from mappings.json but leave cache files untouched."""
        try:
            if not self.mappings_path.exists():
                return
            text = self.mappings_path.read_text()
            data = json.loads(text)
            # clear mappings dict
            data['mappings'] = {}
            self.mappings_path.write_text(json.dumps(data, indent=2))
            self.reload()
        except Exception:
            return
