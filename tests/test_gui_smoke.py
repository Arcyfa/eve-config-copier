import os
import sys
from pathlib import Path

# Ensure Qt runs headless for CI
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QEventLoop, QTimer

from gui.worker import ScanWorker
import eve_backend.scanner as scanner_mod


def test_scan_worker_signals():
    app = QApplication.instance() or QApplication(sys.argv)

    # stub out Scanner.scan to avoid filesystem work
    class DummyResult:
        def __init__(self):
            self.success = True
            self.mappings_path = str(Path.cwd() / 'mappings.json')
            self.summary = {'found_roots': 1, 'accounts': 0}
            self.errors = []

    def fake_scan(self, extra_roots=None, mappings_path=None, progress_callback=None):
        # simulate a tiny progress
        if progress_callback:
            progress_callback('starting')
            progress_callback('done')
        return DummyResult()

    # use monkeypatch-like swap and restore
    orig = scanner_mod.Scanner.scan
    scanner_mod.Scanner.scan = fake_scan

    finished_flag = {'ok': False, 'result': None}

    worker = ScanWorker()
    thread = QThread()
    worker.moveToThread(thread)

    loop = QEventLoop()

    def on_finished(res):
        finished_flag['ok'] = True
        finished_flag['result'] = res
        loop.quit()

    worker.finished.connect(on_finished)
    worker.error.connect(lambda e: loop.quit())

    thread.started.connect(worker.run)
    thread.start()

    # safety timeout
    QTimer.singleShot(3000, loop.quit)
    loop.exec()

    thread.quit()
    thread.wait()

    # restore
    scanner_mod.Scanner.scan = orig

    assert finished_flag['ok'], 'worker did not finish'
    assert getattr(finished_flag['result'], 'success', False)
