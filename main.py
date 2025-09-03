import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QListWidget,
    QMainWindow, QHBoxLayout, QVBoxLayout,
    QWidget, QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt
from helperFunctions.otherFunction import loadFont
from helperFunctions.yamlProcessor import load_config
from library.libraryListWidget import Library
from Installer.widgetToInstallLibrary import Installer

class Analysis(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        self.label = QLabel("This is the analysis Page")
        self.mainLayout.addWidget(self.label)
        self.setLayout(self.mainLayout)
        pass

class DependencyTree(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the dependencyTree Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class Setting(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the setting Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class About(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the about Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class PacMan(QMainWindow):
    """
    Main Window of the Application
    - What someone can do with it, You can start it
    """
    def __init__(self, config: dict = {}):
        super().__init__()
        self.config = config

        # Getting Data from the config file
        self.appName = self.config.get("application", {}).get("appName", "")

         # May this serve some purpose in the future
        self.setObjectName(self.config.get("objects", {}).get("mainWindow", ""))

        # This doesnot work
        self.setWindowIcon(QIcon(
            self.config.get("paths", {}).get("images", {}).get("icon", {}).get("appLogo", "")
        ))

        # All the classes of the application
        self.contentDict = {
            "Libraries": Library(config = self.config),
            "Installer": Installer(config = self.config),
            "Analysis": Analysis(),
            "Dependency Tree": DependencyTree(),
            "Settings": Setting(),
            "About": About()
        }
        self.libraries = {}
        self.navLists = list(self.contentDict.keys())
        self.setGeometry(*self.config.get("application", {}).get("geometry", [100, 100, 800, 600]))
        self.locationPicked = False
        self.setMinimumSize(*self.config.get("application", {}).get("minSize", [800, 600]))
        self.setStyleSheet(self.config.get("stylesheet", {}).get("main", ""))
        # Main Layout
        mainWidget, mainLayout = self.main_layout()

        # Add Side Bar
        sideBar, self.navItems = self.sideBar()
        self.contentStack = self.createContentArea()

        mainLayout.addWidget(sideBar)
        mainLayout.addWidget(self.contentStack, 1)
        self.navItems.currentRowChanged.connect(
            self.contentStack.setCurrentIndex)
        self.setCentralWidget(mainWidget)

    def handleListLibraries(self, pythonPath: str, libraries: list):
        # self.contentDict['Libraries'].libraryList.clear()
        self.contentDict['Libraries'].setPythonExecPath(pythonPath)
        self.contentDict['Libraries'].addItems(libraries)

    def main_layout(self):
        mainWidget = QWidget()
        mainLayout = QHBoxLayout(mainWidget)
        mainLayout.setContentsMargins(
            *self.config.get('application', {}).get('mainLayout', {}).get('contentsMargin', [0, 0, 0, 0])
        )
        mainLayout.setSpacing(
            self.config.get('application', {}).get('mainLayout', {}).get('spacing', 0)
        )
        return mainWidget, mainLayout

    def sideBar(self):
        sideBar = QWidget()
        sideBar.setObjectName("sideBar")
        # sideBar.setFixedWidth(250)
        sideBar.setMinimumWidth(
            self.config.get("application", {}).get("sideBar", {}).get("minWidth", 100)
        )
        sideBar.setMaximumWidth(
            self.config.get("application", {}).get("sideBar", {}).get("maxWidth", 200)
        )
        sideBarLayout = QVBoxLayout(sideBar)
        sideBarLayout.setContentsMargins(
            *self.config.get('application', {}).get('sideBar', {}).get('contentMargins', [10, 10, 10, 10])
        )
        sideBarLayout.setSpacing(
            self.config.get('application', {}).get('sideBar', {}).get('spacing', 15)
        )

        navList = QListWidget()
        navList.setObjectName("navList")
        for navListItems in self.navLists:
            navList.addItem(navListItems)
        navList.setContentsMargins(
            *self.config.get('application', {}).get('sideBar', {}).get('navListContentMargin', [0, 0, 0, 0])
        )
        navList.setSpacing(
            self.config.get('application', {}).get('sideBar', {}).get('navListSpacing', 3)
        )

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
            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            pageLayout.addWidget(label)
            contentStack.addWidget(page)

        return contentStack


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Every Customization regarding color Icon and name exists here
    configFilePath = "config.yaml"
    config: dict = load_config(configFilePath)

    app.setWindowIcon(QIcon(
        config.get("paths", {}).get("images", {}).get("icon", {}).get("appLogo", "")
    ))

    app.applicationVersion = config.get("application", {}).get("version", "")

    fontPath = config.get("paths", {}).get("fonts", {}).get("main", "")
    if fontPath:
        font = loadFont(
            fontPath,
            config.get("application", {}).get("fontSize", 14)
        )
        app.setFont(font)
    window = PacMan(config)
    window.show()
    sys.exit(app.exec())
