from PyQt6.QtCore import QObject, QThread, pyqtSignal

from helpers.other_functions import where_python_location

class PythonInterpreters(QObject):
    release_details = pyqtSignal(dict)
    get_details = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.threadQ = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.threadQ)
        self.worker.finished.connect(self.release_interpreters)
        self.get_details.connect(self.worker.run)
        self.threadQ.finished.connect(self.worker.deleteLater)
        self.threadQ.start()

    def get_interpreters(self):
        self.get_details.emit()

    def release_interpreters(self, interpreters: dict):
        self.release_details.emit(interpreters)

    def stop(self):
        self.threadQ.quit()
        self.threadQ.wait()

class Worker(QObject):
    finished = pyqtSignal(dict)

    def run(self):
        where_python = where_python_location()
        self.finished.emit(where_python)

if __name__ == "__main__":
    pass
