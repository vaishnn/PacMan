from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot
import requests
import yaml

def loadConfig(configFile: str) -> dict:
    try:
        with open(configFile, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file '{configFile}' not found.")
        return {}


def requestInfo(API_ENDPOINT) -> dict:
    response = requests.get(API_ENDPOINT)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return {}


class RequestDetails(QObject):

    fetchedDetails = pyqtSignal(dict)
    fetchDetails = pyqtSignal(str)
    def __init__(self, parent=None, config: dict = {}):
        super().__init__(parent)
        self.config = config

        # Timer for killing the thread after long inactivity
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.stopThread)

        # Thread
        self.threadR = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.threadR)
        self.fetchDetails.connect(self.getDetails)
        self.fetchDetails.connect(self.worker.run)
        self.worker.finished.connect(self.fetchedDetails)
        self.worker.finished.connect(self.restartTimer)

    def restartTimer(self):
        self.timer.start(1000)

    @pyqtSlot(str)
    def getDetails(self, libraryName: str):
        if not self.threadR.isRunning():
            self.threadR.start()

    def stopThread(self):
        self.timer.stop()
        self.threadR.quit()
        self.threadR.wait()

class Worker(QObject):
    finished = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str)
    def run(self, link: str):
        details = requestInfo(link)
        self.finished.emit(details)

if __name__ == "__main__":
    # Implement Test Class
    pass
