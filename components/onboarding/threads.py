from PyQt6.QtCore import  QThread, pyqtSignal
from .utils import where_python_location

class PythonInterpreters(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        where_python = where_python_location()
        self.finished.emit(where_python)
