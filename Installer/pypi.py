from PyQt6.QtCore import QObject, QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import os

# This code is specifically for mac
# Note to self: add some if else statements for windows execution

def getAppSupportDirectory(appName: str = "PacMan") -> str:
    # Just creates the directory if it doesn't exist
    appSupportDir = os.path.expanduser(f"~/Library/Application Support/{appName}")
    os.makedirs(appSupportDir, exist_ok=True)

    return appSupportDir

def savesData(data: list, appName: str = "PacMan", fileName: str = "libraryList.txt"):
    # Saves Data in a pre-defined directory
    appSupportDir = getAppSupportDirectory(appName)
    filePath = os.path.join(appSupportDir, fileName)
    with open(filePath, "w") as file:
        file.write("\n".join(data))

def downloadDataFromPyPi(appName: str = "PacMan", fileName: str = "libraryList.txt") -> list:
    # Downloads Data from PyPi.org
    url = "https://pypi.org/simple/"
    headers = {"User-Agent": "insomnia/11.4.0"}
    response = requests.request("GET", url, data="", headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    librarylist = [tag.get_text() for tag in soup.find_all('a')]
    savesData(librarylist, appName, fileName)
    return librarylist

def loadData(appName = "PacMan", fileName = "libraryList.txt") -> list:
    # Loads Data from a pre-defined directory
    try:
        appSupportDir = getAppSupportDirectory(appName)
        filePath = os.path.join(appSupportDir, fileName)

        if os.path.exists(filePath):
            with open(filePath, "r") as file:
                data = file.read().splitlines()
        else:
            data = downloadDataFromPyPi(appName, fileName)
    except Exception as e:
        data = []
        print(f"Error loading data: {e}")
    return data

class PyPiRunner(QObject):
    listOfLibraries = pyqtSignal(list)
    def __init__(self, appName: str = "PacMan", fileName: str = "libraryList.txt"):
        super().__init__()
        self.threadRunner = QThread()
        self.worker = PyPiWorker(appName, fileName)
        self.worker.moveToThread(self.threadRunner)

        self.worker.finished.connect(self.threadRunner.quit)
        self.threadRunner.started.connect(self.worker.run)
        self.worker.listOfLibraries.connect(self.listOfLibraries)

        self.worker.finished.connect(self.worker.deleteLater)
        self.threadRunner.finished.connect(self.threadRunner.deleteLater)


    def startFetching(self):
        self.threadRunner.start()

class PyPiWorker(QObject):
    listOfLibraries = pyqtSignal(list)
    finished = pyqtSignal()
    def __init__(self, appName: str = "PacMan", fileName: str = "libraryList.txt"):
        super().__init__()
        self.appName = appName
        self.fileName = fileName

    def run(self):
        self.libraryList = loadData(self.appName, self.fileName)
        librarylist = self.libraryList
        self.listOfLibraries.emit(librarylist)
        self.finished.emit()

if __name__ == "__main__":
    print(loadData())
