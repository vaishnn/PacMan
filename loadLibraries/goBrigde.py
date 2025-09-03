import json
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class ProgramRunner(QObject):
    finished = pyqtSignal(str, list)
    def __init__(self, executablePath):
        super().__init__()
        self.executablePath = executablePath

    def startGOProgram(self, venvPath):
        self.threadRunner = QThread()
        self.worker = GoWorker(self.executablePath, venvPath)
        self.worker.moveToThread(self.threadRunner)
        self.threadRunner.started.connect(self.worker.run)
        self.worker.finished.connect(self._handleResults)
        self.worker.finished.connect(self.threadRunner.quit)
        self.worker.finished.connect(self.stop)
        self.threadRunner.start()

    def stop(self):
        if self.threadRunner.isRunning():
            self.threadRunner.quit()
            self.threadRunner.wait()

    def _handleResults(self, returnCode, stdout, stderr):
        if returnCode == 0 and not stderr:
            output = stdout.split("--|--")
            self.finished.emit(output[0], json.loads(output[1]))
        else:
            pass


class GoWorker(QObject):
    """
    Worker class for executing GO programs
    """
    finished  = pyqtSignal( int, str, str)
    def __init__(self, executablePath, venvPath):
        super().__init__()
        self.executablePath = executablePath
        self.venvPath = venvPath
    def run(self):
        try:
            command = [self.executablePath, self.venvPath]
            result = subprocess.run(command, capture_output = True, text = True, check = False)
            self.finished.emit(result.returncode, result.stdout, result.stderr)
        except FileNotFoundError:
            self.finished.emit(-1, "", "Executable Not Found")
        except Exception as e:
            self.finished.emit(-1, "", f"Some error idk {e}")
