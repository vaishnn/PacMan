import sys
import subprocess
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication, QListWidget,
    QMainWindow, QHBoxLayout, QVBoxLayout,
    QWidget, QLabel, QStackedWidget, QFileDialog
)
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



class GoWorker(QObject):
    """
    Worker class for executing GO programs
    """
    finished  = pyqtSignal(int, str, str)
    def __init__(self, executablePath):
        super().__init__()
        self.executablePath = executablePath

    def run(self):
        try:
            command = [self.executablePath]
            result = subprocess.run(command, capture_output = True, text = True, check = False)
            self.finished.emit(result.returncode, result.stdout, result.stderr)
        except FileNotFoundError:
            self.finished.emit(-1, "", "Executable Not Found")
        except Exception as e:
            self.finished.emit(-1, "", f"Some error idk {e}")

class PacMan(QMainWindow):
    """
    Complete UI Will probably be implemented in here
    """
    def __init__(self, colorScheme: dict):
        super().__init__()
        if sys.platform == "win32":
            self.goExecutable = "./go_program.exe"
        else:
            self.goExecutable = "./go_program"
        self.setGeometry(100, 100, 800, 600)
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
            pass

    def main_layout(self):
        mainWidget = QWidget()
        mainLayout = QHBoxLayout(mainWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        return mainWidget, mainLayout

    def sideBar(self):
        sideBar = QWidget()
        sideBar.setObjectName("sidebar")
        sideBar.setFixedWidth(250)
        sideBar_layout = QVBoxLayout(sideBar)
        sideBar_layout.setContentsMargins(10, 10, 10, 10)
        sideBar_layout.setSpacing(15)

        navList = QListWidget()
        navList.setObjectName("navList")
        self.nav_lists = ["Libraries", "Analysis", "Dependency Tree", "Settings", "About"]
        for navListItems in self.nav_lists:
            navList.addItem(navListItems)
        navList.setContentsMargins(0, 0, 0, 0)
        navList.setSpacing(3)

        sideBar_layout.addWidget(navList)

        return sideBar, navList

    def startGoProgram(self):
        self.thread = QThread()
        self.worker = GoWorker(self.goExecutable)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.deleteLater)

        self.thread.start()

        pass

    def handle_result(self, returnCode: int, result: str, err: str):
        print(result)

    def createContentArea(self):
        contentStack = QStackedWidget()
        contentStack.setObjectName("contentStack")

        for index, item_text in enumerate(self.nav_lists):
            page = QWidget()
            pageLayout = QVBoxLayout(page)
            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

            if index == 0:
                buttonLayout = QHBoxLayout()
                self.labelLocation = QLabel("Select Location")
                self.labelLocation.setObjectName("labelLocation")
                self.labelLocation.setFixedSize(400, 30)
                self.labelLocation.setCursor(Qt.CursorShape.PointingHandCursor)
                self.labelLocation.mousePressEvent = self.selectLocation #type: ignore
                buttonLayout.addWidget(self.labelLocation, 1)
                pageLayout.addLayout(buttonLayout)

            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            label = QLabel(f"This is the {item_text} Page")
            pageLayout.addWidget(label)
            contentStack.addWidget(page)

        return contentStack

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PacMan(loadColorScheme())
    window.show()
    sys.exit(app.exec())
