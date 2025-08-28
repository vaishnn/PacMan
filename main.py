import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QListWidget,
    QMainWindow, QHBoxLayout, QVBoxLayout,
    QWidget, QLabel, QStackedWidget, QFileDialog
)
from listWidgets.libraryListWidget import library
from PyQt6.QtCore import pyqtSignal, Qt
from doingSomethingGO.goBrigde import ProgramRunner
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


class clickableLabel(QLabel):
    # Needs to be Implemented Later
    clicked = pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event): #type: ignore
        pass
        self.clicked.emit()


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


class PacMan(QMainWindow):
    """
    Complete UI Will probably be implemented in here
    """
    def __init__(self, colorScheme: dict):
        super().__init__()
        # Idk what even is this for
        self.setObjectName("PacMan")

        # This doesnot work
        self.setWindowIcon(QIcon("icons/delete.png"))

        # I am on mac and never tested on windows Yet
        if sys.platform == "win32":
            self.goExecutable = "./go_app.exe"
        else:
            self.goExecutable = "./go_app"

        # Runner classes for GO Program, only made because I wanted to learn GO
        # This just fetched libraries present in the virtual env
        # Have to implement something where pip is not used (very few cases)
        self.programRunner = ProgramRunner(self.goExecutable)
        self.programRunner.finished.connect(self.handleListLibraries)

        self.contentDict = {
            "Libraries": library(colorScheme['libraryListToolTip']),
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


    def handleListLibraries(self, pythonPath: str, libraries: list):
        # self.contentDict['Libraries'].libraryList.clear()
        self.contentDict['Libraries'].setPythonExecPath(pythonPath)
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
                self.labelLocation.setFixedHeight(30)
                self.labelLocation.setCursor(Qt.CursorShape.PointingHandCursor)
                self.labelLocation.mousePressEvent = self.selectLocation #type: ignore
                buttonLayout.addWidget(self.labelLocationFinal)
                buttonLayout.addWidget(self.labelLocation, 1)
                pageLayout.addLayout(buttonLayout)

            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            pageLayout.addWidget(label)
            contentStack.addWidget(page)

        return contentStack

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PacMan(loadColorScheme())
    window.show()
    sys.exit(app.exec())
