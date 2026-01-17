from PySide6.QtCore import QObject, Signal, Slot
from typing import List, Optional

from eve_backend.scanner import Scanner


class ScanWorker(QObject):
    """Background worker that runs a scan and emits progress/finished signals.

    Usage: move to a QThread and call its `run` slot.
    """

    started = Signal()
    progress = Signal(str)
    finished = Signal(object)  # emits ScanResult
    error = Signal(str)

    def __init__(self, extra_roots: Optional[List[str]] = None, mappings_path: Optional[str] = None):
        super().__init__()
        self.extra_roots = extra_roots
        self.mappings_path = mappings_path

    @Slot()
    def run(self):
        try:
            self.started.emit()
            scanner = Scanner()
            # Scanner.scan is synchronous; call it and emit finished
            result = scanner.scan(extra_roots=self.extra_roots, mappings_path=self.mappings_path, progress_callback=self._progress)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _progress(self, msg: str):
        # forward progress messages to Qt
        try:
            self.progress.emit(str(msg))
        except Exception:
            pass
