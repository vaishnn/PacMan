import sys
from PyQt6.QtGui import QIcon, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication, QFrame, QListWidget,
    QMainWindow, QHBoxLayout, QPushButton, QVBoxLayout,
    QWidget, QLabel, QStackedWidget
)
from PyQt6.QtCore import QSize, Qt
from helperFunctions.otherFunction import loadFont
from helperFunctions.yamlProcessor import load_config
from library.library import Library
from installer.installer import Installer

class HoverIconButton(QPushButton):
    """
    A custom QPushButton that shows an icon on hover and controls its size.
    """
    def __init__(self, icon_path, size=6, parent=None):
        super().__init__(parent)
        self._icon_path = icon_path
        self._icon = QIcon(self._icon_path)
        self._icon_size = QSize(size, size)

    def enterEvent(self, event):
        """When mouse enters, show the icon."""
        super().enterEvent(event)
        self.setIcon(self._icon)
        self.setIconSize(self._icon_size)

    def leaveEvent(self, event): # type: ignore
        """When mouse leaves, hide the icon."""
        super().leaveEvent(event)
        self.setIcon(QIcon()) # Set an empty icon to hide it


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

class ControlBar(QWidget):
    """
    A Widget that contains the window controls of the application, like a custom title bar.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(20)
        self.setObjectName("controlBar")

        self._layout()

        self._mouse_press_pos = None

    def _layout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(8)

        self._setup_buttons()

        layout.addWidget(self.close_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)

        layout.addStretch()
        self.setLayout(layout)


    def _setup_buttons(self):

        # Close Button
        self.close_button = HoverIconButton(icon_path="./icons/close.svg")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(12, 12)
        self.close_button.clicked.connect(self.parent_window.close)

        # Minimize Button
        self.minimize_button = HoverIconButton(icon_path="./icons/minimize.svg")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(12, 12)
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)

        # Maximize Button
        self.maximize_button = HoverIconButton(icon_path="./icons/maximize.svg")
        self.maximize_button.setObjectName("maximizeButton")
        self.maximize_button.setFixedSize(12, 12)
        self.maximize_button.clicked.connect(self.toggle_maximize)

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent): # type: ignore
        self._mouse_press_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent): # type: ignore
        if self._mouse_press_pos is not None:
            delta = event.globalPosition().toPoint() - self._mouse_press_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self._mouse_press_pos = event.globalPosition().toPoint()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent): # type: ignore
        self._mouse_press_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None: # type: ignore
        self.toggle_maximize()
        return super().mouseDoubleClickEvent(a0)

class PacMan(QMainWindow):
    """
    Main Window of the Application
    - What someone can do with it, You can start it
    """
    def __init__(self, config: dict = {}):
        super().__init__()
        # self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self.config = config
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.container = QFrame()
        self.container.setObjectName("mainWindowContainer")

        self.appName = self.config.get("application", {}).get("appName", "")
        self.setWindowTitle(self.appName)


        # All the classes of the application
        self.contentDict = {
            "Libraries": Library(config = self.config),
            "Installer": Installer(config = self.config),
            "Analysis": Analysis(),
            "Dependency Tree": DependencyTree(),
            "Settings": Setting(),
            "About": About()
        }
        self.navLists = list(self.contentDict.keys())
        self.setGeometry(*self.config.get("application", {}).get("geometry", [100, 100, 800, 600]))
        self.locationPicked = False
        self.setMinimumSize(*self.config.get("application", {}).get("minSize", [800, 600]))
        self.setStyleSheet(self.config.get("stylesheet", {}).get("main", ""))
        # Main Layout
        mainLayout = QHBoxLayout(self.container)
        mainLayout.setContentsMargins(
            *self.config.get('application', {}).get('mainLayout', {}).get('contentsMargin', [0, 0, 0, 0])
        )

        mainLayout.setSpacing(
            self.config.get('application', {}).get('mainLayout', {}).get('spacing', 0)
        )

        # Add Side Bar
        sideBar, self.navItems = self.sideBar()
        self.contentStack = self.createContentArea()

        mainLayout.addWidget(sideBar)
        mainLayout.addWidget(self.contentStack, 1)
        self.navItems.currentRowChanged.connect(
            self.contentStack.setCurrentIndex)
        self.setCentralWidget(self.container)

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
        control_bar = ControlBar(self)
        control_bar.setObjectName("controlBar")
        sideBarLayout.addWidget(control_bar)

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
    def closeEvent(self, a0) -> None:
        self.contentDict["Installer"].getDetails.stopThread()
        return super().closeEvent(a0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Every Customization regarding color Icon and name exists here
    configFilePath = "config.yaml"
    config: dict = load_config(configFilePath)
    app.setApplicationDisplayName(
        config.get("application", {}).get("name", "")
    )
    app.setWindowIcon(QIcon(
        config.get("paths", {}).get("images", {}).get("appLogo", "")
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
    window.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
    sys.exit(app.exec())
