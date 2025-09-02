import os
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import subprocess

class InstallingVirtualEnv(QObject):


    process = pyqtSignal(int, str)
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.threadQ = QThread()
        self.worker = WorkerInstall()
        self.worker.moveToThread(self.threadQ)
        self.worker.process.connect(self.process.emit)
        self.threadQ.finished.connect(self.worker.deleteLater)
        self.threadQ.start()

    def start(self, python_path, virtual_env_path, virtual_env_name):
        self.worker.run(python_path, virtual_env_path, virtual_env_name)


class WorkerInstall(QObject):

    process = pyqtSignal(int, str)
    def run(self, python_path, virtual_env_path, virtual_env_name):
        self.process.emit(0, "")
        is_pip_preset = subprocess.run([python_path, "-m", "pip", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

        if is_pip_preset.returncode == 1:
            # requires python>=3.4
            subprocess.run([python_path, "-m", "ensurepip", "--upgrade"])
        subprocess.run([python_path, "-m", "venv", virtual_env_name], capture_output=True, text=True, check=False, cwd=virtual_env_path)
        self.process.emit(1, os.path.abspath(os.path.join(virtual_env_path, virtual_env_name)))
