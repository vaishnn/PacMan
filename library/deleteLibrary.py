from PyQt6.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, QObject
import subprocess

class uninstallManager(QObject):

    uninstallFinished = pyqtSignal(str, bool)
    _executeInstaller = pyqtSignal(str, str)
    def __init__(self, parent = None):
        super().__init__(parent)

        self.IDLE_TIMOUT = 30000

        self.threadRunner = QThread()
        self.worker = uninstallLibraryManager()
        self.idleTimer = QTimer()
        self.idleTimer.setSingleShot(True)
        self.idleTimer.setInterval(self.IDLE_TIMOUT)
        self.worker.moveToThread(self.threadRunner)
        self._executeInstaller.connect(self.worker.run)
        self.worker.finished.connect(self.workerIsFinished)
        self.idleTimer.timeout.connect(self._stopIdleThread)


    @pyqtSlot(str, bool)
    def workerIsFinished(self, packageName, success):
        """Just starts the idle timer for thread detach"""
        self.uninstallFinished.emit(packageName, success)
        self.idleTimer.start()

    def requestUninstall(self, pythonExec, libraryName):
        print(pythonExec)
        self.idleTimer.stop()
        if not self.threadRunner.isRunning():
            self.threadRunner.start()
        self._executeInstaller.emit(pythonExec, libraryName)

    def _stopIdleThread(self):
        if self.threadRunner.isRunning():
            self.threadRunner.quit()
            self.threadRunner.wait()
        self.idleTimer.stop()

    def stop(self):
        self.idleTimer.stop()
        if self.threadRunner.isRunning():
            self.threadRunner.quit()
            self.threadRunner.wait()

class uninstallLibraryManager(QObject):
    """Uninstalls a library in a different thread using pip uninstall command"""
    finished = pyqtSignal(str, bool)
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot(str, str)
    def run(self, pythonExec, libraryName):
        print(10)
        command = [pythonExec, "-m", "pip", "uninstall", "-y", libraryName]
        result = subprocess.run(command, capture_output=True, text=True)
        print(command)
        self.finished.emit(libraryName, result.returncode == 0)
