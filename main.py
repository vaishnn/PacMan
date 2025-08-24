import sys
import subprocess
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem,
    QMainWindow, QHBoxLayout, QVBoxLayout,
    QWidget, QLabel, QStackedWidget, QFileDialog
)
import json
import yaml

def loadColorScheme(path="colorScheme.yaml"):
    try:
        with open(path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Color scheme file not found at {path}")
        raise
    except Exception as e:
        print(f"Error loading color scheme file: {e}")
        raise

class library(QWidget):
    def __init__(self):
        super().__init__()
        self.libraryLayout = QVBoxLayout(self)
        self.libraryLayout.setContentsMargins(10, 10, 10, 10)
        self.libraryLayout.setSpacing(3)
        self.libraryList = QListWidget()
        self.libraryList.setObjectName("libraryList")

        self.libraryLayout.addWidget(self.libraryList)

    def addItems(self, items):
        self.libraryList.clear()
        for item in items:
            listLibraryWidget = QWidget()
            listWidgetLayout = QHBoxLayout(listLibraryWidget)
            nameLibraryPanel = QLabel(item["name"])
            versionLibraryPanel = QLabel(item["version"])
            tagLibraryPanel = QLabel(item["tag"])
            listWidgetLayout.addWidget(nameLibraryPanel)
            listWidgetLayout.addWidget(versionLibraryPanel)
            listWidgetLayout.addWidget(tagLibraryPanel)
            listItem = QListWidgetItem(self.libraryList)
            listItem.setSizeHint(listLibraryWidget.sizeHint())
            self.libraryList.addItem(listItem)
            self.libraryList.setItemWidget(listItem, listLibraryWidget)



        pass

class analysis(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        self.label = QLabel("This is the analysis Page")
        self.mainLayout.addWidget(self.label)
        self.setLayout(self.mainLayout)
        pass

class dependencyTree(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the dependencyTree Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class setting(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the setting Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class about(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the about Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class GoWorker(QObject):
    """
    Worker class for executing GO programs
    """
    finished  = pyqtSignal(int, str, str)
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

class ProgramRunner(QObject):
    finished = pyqtSignal(list)
    def __init__(self, executablePath):
        super().__init__()
        self.executablePath = executablePath
        self.thread = None
        self.worker = None

    def startGOProgram(self, venvPath):
        self.thread = QThread()
        self.worker = GoWorker(self.executablePath, venvPath)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handleResults)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.deleteLater)
        self.thread.start()


    def _handleResults(self, returnCode, stdout, stderr):
        if returnCode == 0 and not stderr:
            self.finished.emit(json.loads(stdout))
        else:
            pass

class PacMan(QMainWindow):
    """
    Complete UI Will probably be implemented in here
    """
    def __init__(self, colorScheme: dict):
        super().__init__()
        if sys.platform == "win32":
            self.goExecutable = "./go_app.exe"
        else:
            self.goExecutable = "./go_app"
        self.programRunner = ProgramRunner(self.goExecutable)
        self.programRunner.finished.connect(self.handleListLibraries)
        self.contentDict = {
            "Libraries": library(),
            "Analysis": analysis(),
            "Dependency Tree": dependencyTree(),
            "Settings": setting(),
            "About": about()
        }
        self.libraries = {}
        self.navLists = list(self.contentDict.keys())
        self.setGeometry(100, 100, 800, 600)
        self.locationPicked = False
        self.setMinimumSize(800, 600)
        self.setStyleSheet(colorScheme['main'])
        # Main Layout
        mainWidget, mainLayout = self.main_layout()

        # Add Side Bar
        sideBar, self.navItems = self.sideBar()
        self.contentStack = self.createContentArea()

        mainLayout.addWidget(sideBar)
        mainLayout.addWidget(self.contentStack, 1)
        self.navItems.currentRowChanged.connect(self.contentStack.setCurrentIndex)
        self.setCentralWidget(mainWidget)

    def selectLocation(self, event):
        directoryPath = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directoryPath:
            self.labelLocation.setText(f"{directoryPath}")
            self.programRunner.startGOProgram(directoryPath)


    def handleListLibraries(self, libraries: list):
        print(10)
        self.contentDict['Libraries'].libraryList.clear()
        self.contentDict['Libraries'].addItems(libraries)

    def main_layout(self):
        mainWidget = QWidget()
        mainLayout = QHBoxLayout(mainWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        return mainWidget, mainLayout

    def sideBar(self):
        sideBar = QWidget()
        sideBar.setObjectName("sidebar")
        # sideBar.setFixedWidth(250)
        sideBar.setMinimumWidth(100)
        sideBar.setMaximumWidth(200)
        sideBarLayout = QVBoxLayout(sideBar)
        sideBarLayout.setContentsMargins(10, 10, 10, 10)
        sideBarLayout.setSpacing(15)

        navList = QListWidget()
        navList.setObjectName("navList")
        for navListItems in self.navLists:
            navList.addItem(navListItems)
        navList.setContentsMargins(0, 0, 0, 0)
        navList.setSpacing(3)

        sideBarLayout.addWidget(navList)

        return sideBar, navList

    def updateLibraries(self):
        pass

    def createContentArea(self):
        contentStack = QStackedWidget()
        contentStack.setObjectName("contentStack")

        for index, item_text in enumerate(self.navLists):
            page = QWidget()
            pageLayout = QVBoxLayout(page)
            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            label = self.contentDict[item_text]
            if index == 0:
                buttonLayout = QHBoxLayout()
                self.labelLocation = QLabel("Select Path")
                self.labelLocation.setObjectName("labelLocation")
                self.labelLocationFinal = QLabel("Virtual Env:")
                self.labelLocationFinal.setObjectName("labelLocationFinal")
                # self.labelLocation.setFixedSize(400, 30)
                self.labelLocation.setFixedHeight(30)
                self.labelLocation.setCursor(Qt.CursorShape.PointingHandCursor)
                self.labelLocation.mousePressEvent = self.selectLocation #type: ignore
                buttonLayout.addWidget(self.labelLocationFinal)
                buttonLayout.addWidget(self.labelLocation, 1)
                pageLayout.addLayout(buttonLayout)

            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # label = QLabel(f"This is the {item_text} Page")

            pageLayout.addWidget(label)
            contentStack.addWidget(page)

        return contentStack

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PacMan(loadColorScheme())
    window.show()
    sys.exit(app.exec())
