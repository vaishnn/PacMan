import os
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from helpers.find_local_envs import find_virtual_envir
from library.load_library import get_installed_libraries_with_size

class FetchLibraryList(QObject):
    """Seperate Thread for Get's list of library with version and space it's sharing using record and some naming convention"""
    finished = pyqtSignal(int, list)
    fetch = pyqtSignal(str, str)
    libraries = pyqtSignal(str, list, list)
    def __init__(self):
        super().__init__()
        self.threadRunner = QThread()
        self.worker = GoWorker()
        self.worker.moveToThread(self.threadRunner)
        self.fetch.connect(self.worker.run)
        self.worker.finished.connect(self.libraries.emit)
        self.threadRunner.finished.connect(self.worker.deleteLater)
        self.threadRunner.start()

    def get_details(self, project_path, virtual_env = ""):
        self.fetch.emit(project_path, virtual_env)

    def stop(self):
        if self.threadRunner.isRunning():
            self.threadRunner.quit()
            self.threadRunner.wait()

class GoWorker(QObject):
    """
    Worker class for getting list of libraries
    """
    finished  = pyqtSignal( str, list, list)
    def run(self, project_path, virtual_env_name = ""):

        try:
            virtual_env_paired_with_python_version = []
            virtual_envs = find_virtual_envir(project_path)
            for virtual_environment in virtual_envs:
                virtual_env_paired_with_python_version.append(virtual_environment.venv_name+ ":   " +
                    f"{virtual_environment.python_version}")
            if virtual_env_name == "":
                virtual_env_name = virtual_env_paired_with_python_version[0].split(":")[0].strip()

            venv_path = os.path.abspath(os.path.join(project_path, virtual_env_name))
            python_exec, details = get_installed_libraries_with_size(venv_path)

            self.finished.emit(python_exec, details, virtual_env_paired_with_python_version)
        except FileNotFoundError:
            self.finished.emit("", "", [], "Executable Not Found")
        except Exception as e:
            self.finished.emit("", "", [], f"Some error idk {e}")
