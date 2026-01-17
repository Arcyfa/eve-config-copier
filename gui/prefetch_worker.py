from PySide6.QtCore import QObject, Signal, Slot
from typing import Optional, List

from eve_backend.prefetcher import Prefetcher, CancelToken


class PrefetchWorker(QObject):
    started = Signal()
    progress = Signal(str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, mappings_path: Optional[str] = None):
        super().__init__()
        self.mappings_path = mappings_path
        self._cancel = CancelToken()

    @Slot()
    def run(self):
        try:
            self.started.emit()
            pre = Prefetcher(mappings_path=self.mappings_path)
            res = pre.run(progress_callback=self._on_progress, cancel_token=self._cancel)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancel.cancel()

    def _on_progress(self, msg: str):
        try:
            self.progress.emit(str(msg))
        except Exception:
            pass
