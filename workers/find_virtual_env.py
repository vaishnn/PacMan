from PyQt6.QtCore import QObject, QThread, pyqtSignal
from helpers.find_local_envs import find_virtual_envir


class FindEnvironment(QObject):

    finished = pyqtSignal(list)
    get_env = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.threadQ = QThread()
        self.worker = FindEnvironment_Worker()
        self.worker.moveToThread(self.threadQ)
        self.worker.finished.connect(self.emit_finished)
        self.get_env.connect(self.worker.run)
        self.threadQ.finished.connect(self.worker.deleteLater)
        self.threadQ.start()

    def emit_finished(self, env: list):
        self.finished.emit(env)

    def emit_get_env(self, path_env: str):
        self.get_env.emit(path_env)


class FindEnvironment_Worker(QObject):
    finished = pyqtSignal(list)
    def run(self, path_of_env: str):
        env = find_virtual_envir(path_of_env)
        self.finished.emit(env)
