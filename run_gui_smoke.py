import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from gui.all_characters import AllCharactersTab

app = QApplication([])
try:
    tab = AllCharactersTab()
    tab.reload()
    print('AllCharactersTab reload OK')
except Exception as e:
    print('ERROR', e)
    raise
finally:
    app.quit()
