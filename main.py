import sys
from PyQt6.QtGui import  QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QFrame, QListWidget,
    QMainWindow, QHBoxLayout, QSplashScreen,  QVBoxLayout,
    QWidget, QLabel, QStackedWidget
)
from PyQt6.QtCore import  Qt, pyqtSignal
from others.control_bar import ControlBar
from library.library import Library
from installer.installer import Installer
from helper.other_functions import loadFont
from helper.yaml_pre_processing import load_config
from onboarding.main import OnboardingPage


class Analysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis")
        self.mainLayout = QVBoxLayout()
        self.label = QLabel("This is the analysis Page")
        self.mainLayout.addWidget(self.label)
        self.setLayout(self.mainLayout)
        pass

class DependencyTree(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dependencyTree")
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the dependencyTree Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class Setting(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("setting")
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the setting Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass

class About(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("about")
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

    loaded_all_components = pyqtSignal()
    def __init__(self, config: dict = {}):
        super().__init__()
        self.setMouseTracking(True)
        self.config = config
        # self.loaded_components = IntNotifier()
        # self.loaded_components.value_changed.connect(self.show_the_ui)

        self._setting_ui_properties()
        self.container = QFrame()
        self.container.setObjectName("mainWindowContainer")
        self._setup_main_app_ui()

        self.onboarding_widget = OnboardingPage(self.config, self)
        self.onboarding_widget.location_selected.connect(self._set_existing_python_env)
        self.onboarding_widget.switch_to_main.connect(self.switchContent)

        self.main_stack = QStackedWidget(self)
        self.main_stack.addWidget(self.onboarding_widget)
        self.main_stack.addWidget(self.container)

        self.setCentralWidget(self.main_stack)
        self.main_stack.setCurrentWidget(self.onboarding_widget)

    def _save_current_state(self):
        pass

    def _set_existing_python_env(self, curr_dir, current_venv, virtual_envs):
        self.main_stack.setCurrentWidget(self.container)
        self.contentDict["Libraries"].selectLocationFromMain(curr_dir, current_venv, virtual_envs)

    def _setup_main_app_ui(self):
        self.contentDict = {
            "Libraries": Library(config = self.config),
            "Installer": Installer(config = self.config),
            "Analysis": Analysis(),
            "Dependency Tree": DependencyTree(),
            "Settings": Setting(),
            "About": About()
        }
        self.navLists = list(self.contentDict.keys())

        mainLayout = QHBoxLayout(self.container)
        mainLayout.setContentsMargins(
            *self.config.get("ui", {}).get('window', {}).get('mainLayout', {}).get('contentsMargin', [0, 0, 0, 0])
        )

        mainLayout.setSpacing(
            self.config.get("ui", {}).get('window', {}).get('mainLayout', {}).get('spacing', 0)
        )

        # Add Side Bar
        sideBar, self.navItems = self.sideBar()
        self.contentStack = self.createContentArea()

        mainLayout.addWidget(sideBar)
        mainLayout.addWidget(self.contentStack, 1)

        self.navItems.currentRowChanged.connect(
            self.contentStack.setCurrentIndex)

        # self.loaded_components.value = 6



    def switchContent(self):
        self.main_stack.setCurrentWidget(self.container)

    def _setting_ui_properties(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(*self.config.get("ui", {}).get('window', {}).get("geometry", [100, 100, 800, 600]))
        self.setMinimumSize(*self.config.get("ui", {}).get('window', {}).get("minSize", [800, 600]))
        # self.setStyleSheet(self.config.get("stylesheet", {}).get("main", ""))
        self.appName = self.config.get("application", {}).get("name", "")

    def sideBar(self):
        sideBar = QWidget()
        sideBar.setObjectName("sideBar")
        # sideBar.setFixedWidth(250)
        sideBar.setMinimumWidth(
            self.config.get("ui", {}).get('window', {}).get("sideBar", {}).get("minWidth", 100)
        )
        sideBar.setMaximumWidth(
            self.config.get("ui", {}).get('window', {}).get("sideBar", {}).get("maxWidth", 200)
        )
        sideBarLayout = QVBoxLayout(sideBar)
        sideBarLayout.setContentsMargins(
            *self.config.get("ui", {}).get('window', {}).get("sideBar", {}).get('contentMargins', [10, 10, 10, 10])
        )
        sideBarLayout.setSpacing(
            self.config.get('ui', {}).get('window', {}).get("sideBar", {}).get('spacing', 15)
        )
        self.control_bar = ControlBar(self, self.config)
        self.control_bar.setContentsMargins(2, 2, 0, 0)
        self.control_bar.setObjectName("controlBar")
        sideBarLayout.addWidget(self.control_bar)

        navList = QListWidget()
        navList.setObjectName("navList")
        for navListItems in self.navLists:
            navList.addItem(navListItems)
        navList.setContentsMargins(
            *self.config.get('ui', {}).get('window', {}).get("sideBar", {}).get('navListContentMargin', [0, 0, 0, 0])
        )
        navList.setSpacing(
            self.config.get('ui', {}).get('window', {}).get("sideBar", {}).get('navListSpacing', 3)
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

    def closeEvent(self, a0) -> None:
        if "Installer" in self.contentDict:
            self.contentDict["Installer"].getDetails.stopThread()
        super().closeEvent(a0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pixmap = QPixmap("icons/appLogo.png") # Create a simple 'loading.png' image
    splash = QSplashScreen(pixmap)
    splash.setFixedSize(200, 200)

    splash.show()
    app.processEvents()
    # Every Customization regarding color Icon and name exists here
    config: dict = load_config()
    app.setApplicationDisplayName(
        config.get("application", {}).get("name", "")
    )
    app.setWindowIcon(QIcon(
        config.get("paths", {}).get("assets", {}).get("images", "").get("appLogo", "")
    ))

    app.applicationVersion = config.get("app", {}).get("version", "")

    fontPath = config.get("paths", {}).get("assets", {}).get("fonts", {}).get("main", "")
    if fontPath:
        font = loadFont(
            fontPath,
            config.get("ui", {}).get("dimensions", {}).get('fontSize', {}).get('mainFont', 14)
        )
        app.setFont(font)
    app.setStyleSheet(config.get("stylesheet", {}).get("main", ""))
    window = PacMan(config)
    window.show()
    window.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
    splash.finish(window)
    sys.exit(app.exec())
