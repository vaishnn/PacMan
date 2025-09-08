from PyQt6.QtCore import QObject, QThread, pyqtSignal
import subprocess

from helpers.find_local_envs import find_virtual_envir

class InitializingEnvironment(QObject):
    process = pyqtSignal(int, str, str, list)
    initialize = pyqtSignal(str, str, str)
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.threadQ = QThread()
        self.worker = InitializingEnvironment_Worker()
        self.worker.moveToThread(self.threadQ)
        self.initialize.connect(self.worker.run)
        self.worker.process.connect(self.process.emit)
        self.threadQ.finished.connect(self.worker.deleteLater)
        self.threadQ.start()

    def start(self, python_path, virtual_env_path, virtual_env_name):
        self.initialize.emit(python_path, virtual_env_path, virtual_env_name)

    def stop(self):
        if self.threadQ.isRunning():
            self.threadQ.quit()
            self.threadQ.wait()


class InitializingEnvironment_Worker(QObject):
    process = pyqtSignal(int, str, str, list)
    def run(self, python_path, virtual_env_path, virtual_env_name):
        self.process.emit(0, "", "", [])
        is_pip_preset = subprocess.run([python_path, "-m", "pip", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

        if is_pip_preset.returncode == 1:
            # requires python>=3.4
            subprocess.run([python_path, "-m", "ensurepip", "--upgrade"])
        subprocess.run([python_path, "-m", "venv", virtual_env_name], capture_output=True, text=True, check=False, cwd=virtual_env_path)
        envs = [env.venv_name for env in find_virtual_envir(virtual_env_path)]
        self.process.emit(1, virtual_env_path, virtual_env_name, envs)
