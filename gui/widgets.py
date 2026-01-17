from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QColor


class StatusIndicator(QWidget):
    """A small widget showing a colored circle and short label.

    Use `set_status(True/False, tooltip)` to update.
    """

    def __init__(self, label_text: str = ''):
        super().__init__()
        self._dot = QLabel()
        self._dot.setFixedSize(14, 14)
        self._dot.setStyleSheet(self._dot_style('gray'))
        self._label = QLabel(label_text)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self._dot)
        lay.addWidget(self._label)

    def _dot_style(self, color: str) -> str:
        return f"background:{color}; border-radius:7px; border:1px solid #444;"

    def set_status(self, ok: bool, tooltip: str = ''):
        color = 'green' if ok else 'red'
        self._dot.setStyleSheet(self._dot_style(color))
        if tooltip:
            self.setToolTip(tooltip)
        else:
            self.setToolTip('')
