from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import subprocess

class getLibraryDetails(QObject):
    detailsWithName = pyqtSignal(str, dict)
    requestReady = pyqtSignal(str, str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.threadRunner = QThread()
        self.worker = runCommandThroughPython()
        self.requestReady.connect(self.worker.run)
        self.worker.moveToThread(self.threadRunner)
        self.worker.finished.connect(self.returnCommandOutput)
        self.threadRunner.start()

    def fetchDetailLibraryDetails(self, pythonExecPath, name):
        self.requestReady.emit(pythonExecPath, name)

    @pyqtSlot(str, int, bytes, bytes)
    def returnCommandOutput(self, name, returnCode, stdout, stderr):
        if returnCode == 0 and not stderr:
            # Convert byte to string
            stdout = stdout.decode('utf-8')
            infoDict = {}
            for item in stdout.split('\n'):
                if ':' in item:
                    key, value = item.split(':', 1)
                    infoDict[key.strip()] = value.strip()
            self.detailsWithName.emit(name, infoDict)

    def stop(self):
        self.threadRunner.quit()
        self.threadRunner.wait()

class runCommandThroughPython(QObject):
    finished = pyqtSignal(str, int, bytes, bytes)
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot(str, str)
    def run(self, pythonExecPath, commandRun):
        command = [pythonExecPath,"-m", "pip", "show", commandRun]
        result = subprocess.run(command, capture_output = True)
        self.finished.emit(commandRun, result.returncode, result.stdout, result.stderr)
