from PyQt6.QtCore import QObject, QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import os

# This code is specifically for mac
# Note to self: add some if else statements for windows execution




def get_app_support_directory(appName: str = "PacMan") -> str:
    # Just creates the directory if it doesn't exist
    app_support_dir = os.path.expanduser(f"~/Library/Application Support/{appName}")
    os.makedirs(app_support_dir, exist_ok=True)

    return app_support_dir

def save_file(data: list, app_name: str = "PacMan", file_name: str = "libraryList.txt"):
    # Saves Data in a pre-defined directory
    app_support_dir = get_app_support_directory(app_name)
    file_path = os.path.join(app_support_dir, file_name)
    with open(file_path, "w") as file:
        file.write("\n".join(data))

def download_data_from_pypi(app_name: str = "PacMan", file_name: str = "libraryList.txt") -> list:
    # Downloads Data from PyPi.org
    url = "https://pypi.org/simple/"
    headers = {"User-Agent": "insomnia/11.4.0"}
    response = requests.request("GET", url, data="", headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    librarylist = [tag.get_text() for tag in soup.find_all('a')]
    save_file(librarylist, app_name, file_name)
    return librarylist

def load_data(app_name = "PacMan", file_name = "libraryList.txt") -> list:
    # Loads Data from a pre-defined directory
    try:
        appSupportDir = get_app_support_directory(app_name)
        filePath = os.path.join(appSupportDir, file_name)

        if os.path.exists(filePath):
            with open(filePath, "r") as file:
                data = file.read().splitlines()

        else:
            data = download_data_from_pypi(app_name, file_name)
    except Exception as e:
        data = []
        print(f"Error loading data: {e}")
    if data:
        data = [{"name": name} for name in data]
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
        self.libraryList = load_data(self.appName, self.fileName)
        librarylist = self.libraryList
        self.listOfLibraries.emit(librarylist)
        self.finished.emit()

if __name__ == "__main__":
    print(load_data())
