from PyQt6.QtCore import QObject, QThread, pyqtSignal
from helpers.state import save_state
from installer.pypi import save_file


class Save(QObject):

    finished = pyqtSignal()
    quit = pyqtSignal(list, dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_quit = QThread()
        self.worker = Save_worker()
        self.worker.moveToThread(self.thread_quit)
        self.quit.connect(self.worker.run)
        self.worker.success.connect(self.finished.emit)
        self.worker.success.connect(self.close)

    def run(self, libraries, save_state):
        self.quit.emit(libraries, save_state)

    def close(self):
        if self.thread_quit.isRunning():
            self.thread_quit.quit()
            self.thread_quit.wait()

class Save_worker(QObject):
    success = pyqtSignal()
    def run(self, libraries, state_variables):

        if not state_variables.get('project_folder', "") == "":
            save_state(
                state_variables.get('project_folder'), state_variables.get('virtual_env_name')
            )
            save_file(libraries)
