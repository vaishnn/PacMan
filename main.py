import os
import sys
from PyQt6.QtGui import  QIcon, QKeyEvent, QMovie
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QListWidget,
    QMainWindow, QHBoxLayout, QPushButton, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget, QLabel, QStackedWidget
)
from PyQt6.QtCore import  QEasingCurve, QPropertyAnimation, QSize, QTimer, Qt, pyqtSignal
from others.controlBar import ControlBar
from library.library import Library
from installer.installer import Installer
from helperFunctions.wherePython import PythonInterpreters
from worker.initialScreenWorker import InstallingVirtualEnv
from helperFunctions.findenv import FindEnvironment
from helperFunctions.otherFunction import loadFont
from helperFunctions.yamlProcessor import load_config

class LineEdit(QTextEdit):
    def keyPressEvent(self, event: QKeyEvent): #type: ignore
        text = event.text()
        if text.isalpha() or text.isdigit() or text == "." or event.key() in (
            0x01000003,  # Qt.Key_Backspace
                0x01000007,  # Qt.Key_Delete
                0x01000012,  # Qt.Key_Left
                0x01000013,  # Qt.Key_Up
                0x01000014,  # Qt.Key_Right
                0x01000015,  # Qt.Key_Down
                0x01000016,  # Qt.Key_Home
                0x01000017,  # Qt.Key_End
                0x01000020,  # Qt.Key_Enter
                0x01000004,  # Qt.Key_Tab
                0x01000005,  # Qt.Key_Backtab
                0x01000006,  # Qt.Key_Return
        ):
            super().keyPressEvent(event)

class Toast(QWidget):
    def __init__(self, parent, message, duration=2000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.label = QLabel(self)
        self.label.setText(message)
        self.label.setStyleSheet("""
            background: #2D2D2D;
            color: #EEEEEE;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()
        self.duration = duration

    def showEvent(self, event): #type: ignore
        # Position at bottom center of parent
        parent = self.parentWidget()
        if parent:
            pw, ph = parent.width(), parent.height()
            tw, th = self.label.width(), self.label.height()
            x = (pw - tw) // 2
            y = ph - th - 1  # 32px above bottom
            self.setGeometry(x, y, tw, th)
        QTimer.singleShot(self.duration, self.close)


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

class OnboardingPage(QWidget):

    finished = pyqtSignal()
    location_selected = pyqtSignal(str, str, list)
    find_env_in_pc = pyqtSignal()
    switch_to_main = pyqtSignal()
    def __init__(self, config, parent):
        super().__init__(parent)
        self.setObjectName("onboardingWidget")
        self.config = config
        self.setStyleSheet(config.get('stylesheet', {}).get('main',''))
        self.project_location = ""
        self.animation_running = False
        self.current_env = []

        self.installing_virtual_env = InstallingVirtualEnv()
        self.installing_virtual_env.process.connect(self._update_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame(self)
        self.frame.setObjectName("mainWindowContainer")
        main_layout.addWidget(self.frame)

        self.frame_layout = QVBoxLayout(self.frame)

        self.controlBar = ControlBar(parent, config)
        self.frame_layout.addWidget(self.controlBar)


        self.stacked_widget = QStackedWidget()
        self.frame_layout.addWidget(self.stacked_widget)

        self._setup_pages()

    def _setup_pages(self):
        # self.stacked_widget.addWidget()
        self.stacked_widget.addWidget(self._create_location_page())
        self.stacked_widget.addWidget(self._loading_virtual_env())
        self.stacked_widget.setCurrentIndex(0)


    def _create_page_container(self, name, margin = [0, 0, 0, 0]):
        container = QWidget()
        container.setObjectName(name)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(*margin)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        return container

    def _create_location_page(self):
        container = QWidget()
        self.page_layout = QVBoxLayout(container)
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Select Location
        self.location_container = QFrame(container)
        self.location_container.setFixedHeight(50)
        self.location_container.setObjectName("locationContainer")
        location_layout = QVBoxLayout(self.location_container)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_label = QLabel("Select Project Directory")
        self.browse_label.setObjectName("browseLabel")
        self.browse_label.setFixedHeight(50)
        self.browse_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # subtitle = QLabel("Choose the folder where your virtual environments will be stored.")
        self.browse_label.mousePressEvent = self._select_location #type: ignore
        location_layout.addWidget(self.browse_label)

        # Environment Selection Initially Hidden
        self.select_env = QFrame(container)
        self.select_env.setObjectName("selectEnv")
        self._populate_environment_container()

        self.page_layout.addWidget(self.location_container)
        self.page_layout.addWidget(self.select_env,1)
        # self.page_layout.addStretch()

        self.select_env.setVisible(False)
        self.select_env.setFixedHeight(0)

        return container

    def _loading_virtual_env(self):
        container = QFrame()
        layout = QVBoxLayout(container)
        spinner_label = QLabel()
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        movie = QMovie("./icons/spinner.gif")
        movie.setScaledSize(QSize(32, 32))
        spinner_label.setMovie(movie)
        layout.addWidget(spinner_label)
        movie.start()
        return container


    def _populate_environment_container(self):
        layout = QVBoxLayout(self.select_env)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.find_env = FindEnvironment()
        self.python_interpreters = PythonInterpreters()

        self.found_virtual_envs_label = QLabel("Searching for existing virtual environments...")
        self.found_virtual_envs_label.setFixedHeight(30)
        self.drop_down_for_selecting_virtual_env = QComboBox()
        self.use_selecting_virtual_env_button = QPushButton("Use this Environment")
        self.use_selecting_virtual_env_button.setObjectName("selectVirtualEnvButton")
        self.use_selecting_virtual_env_button.clicked.connect(self._set_existing_python_env)
        self.use_selecting_virtual_env_button.setObjectName("useSelectingVirtualEnvButton")

        self.create_virtual_env_information = QLabel("Searching for existing global environments...")
        self.create_virtual_env_information.setFixedHeight(30)
        self.name_of_venv = LineEdit()
        self.name_of_venv.setFixedHeight(38)
        self.name_of_venv.setContentsMargins(0, 0, 0, 0)
        self.name_of_venv.setPlaceholderText("Type name of your virtual environment, default: venv")
        self.name_of_venv.setObjectName("customVirtualName")


        self.drop_down_for_creating_python_env = QComboBox()
        self.create_virtual_env_button = QPushButton("Create New Environment")
        self.create_virtual_env_button.setObjectName("createVirtualEnv")

        self.create_virtual_env_button.clicked.connect(self._create_virtual_env)
        self.create_virtual_env_button.setObjectName("createVirtualEnvButton")

        self.find_env.finished.connect(self._display_env)
        self.python_interpreters.release_details.connect(
            self._display_python_interpreters
        )
        layout.addWidget(self.found_virtual_envs_label)
        layout.addWidget(self.drop_down_for_selecting_virtual_env)
        layout.addWidget(self.use_selecting_virtual_env_button)

        layout.addSpacing(30)

        layout.addWidget(self.create_virtual_env_information)
        layout.addWidget(self.name_of_venv)
        layout.addWidget(self.drop_down_for_creating_python_env)
        layout.addWidget(self.create_virtual_env_button)
        # layout.addStretch()

    def _set_existing_python_env(self):
        current_venv = ""
        curr_dir = "".join(self.drop_down_for_selecting_virtual_env.currentText().split(":")[1:]).strip()
        virtual_envs = []
        for env in self.env:
            virtual_envs.append(env.venv_name)
            if env.venv_path == curr_dir:
                current_venv = env.venv_name

        self.location_selected.emit(self.project_location, current_venv, virtual_envs)

    def _create_virtual_env(self):
        python_path = "".join(self.drop_down_for_creating_python_env.currentText().split(":")[1:]).strip()
        virtual_env_path = self.project_location
        text = self.name_of_venv.toPlainText()
        if text == "":
            text = "venv"

        if text in self.list_of_virtual_env:
            self.commit_action("Same name environment already exist")
        else:
            self.installing_virtual_env.start(python_path, virtual_env_path, text)

    def _update_widget(self, code: int, venv_path: str):
        if code == 0:
            self.stacked_widget.setCurrentIndex(1)
        if code == 1:
            self.location_selected.emit(self.project_location, venv_path, venv_path.split(os.path.sep)[-1].strip())
        pass

    def commit_action(self, message: str):
        toast = Toast(self, message=message)
        toast.show()


    def _select_location(self, event):
        if self.animation_running:
            return

        directory = QFileDialog.getExistingDirectory(self, "Selecting Directory")
        if directory:
            self.project_location = directory
            self.browse_label.setText(f"Selected: {directory}")

            self.find_env.emit_get_env(directory)
            self.python_interpreters.get_interpreters()
            self.find_env_in_pc.emit()

            self.animation_running = True
            self.select_env.setVisible(True)

            final_height = self.select_env.sizeHint().height()

            self.animation = QPropertyAnimation(
                self.select_env, b"maximumHeight"
            )
            self.animation.setDuration(500)
            self.animation.setStartValue(0)
            self.animation.setEndValue(final_height)
            self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
            self.animation.finished.connect(
                lambda: setattr(self, 'animation_running', False)
            )
            self.animation.start()

    def _display_env(self, env: list):
        self.env = env
        self.drop_down_for_selecting_virtual_env.clear()
        self.list_of_virtual_env = []
        if env:
            # found_env = "\n".join([f"{item['path']} : {item['version']}" for item in env])
            self.found_virtual_envs_label.setText(f"found {len(env)} virtual environments")
            for item in env:
                self.list_of_virtual_env.append(item.venv_path)
                self.drop_down_for_selecting_virtual_env.addItem(
                    f"{item.python_version}: {item.venv_path}")
            self.drop_down_for_selecting_virtual_env.setVisible(True)
            self.use_selecting_virtual_env_button.setVisible(True)
        else:
            self.found_virtual_envs_label.setText("No virtual environment found")
            self.drop_down_for_selecting_virtual_env.setVisible(False)
            self.use_selecting_virtual_env_button.setVisible(False)

    def _display_python_interpreters(self, interpreters: dict):
        self.drop_down_for_creating_python_env.clear()
        if len(interpreters) > 1:
            self.create_virtual_env_information.setText(f"found {len(interpreters)} global python interpreters")
            for item in interpreters:
                self.drop_down_for_creating_python_env.addItem(f"{item} : {interpreters[item]}")
        else:
            self.create_virtual_env_information.setText("No Python interpreter found")

    def _finished_flow(self):
        self.switch_to_main.emit()



class PacMan(QMainWindow):
    """
    Main Window of the Application
    - What someone can do with it, You can start it
    """

    def __init__(self, config: dict = {}):
        super().__init__()
        self.setMouseTracking(True)
        self.config = config




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



    def switchContent(self):
        self.main_stack.setCurrentWidget(self.container)

    def _setting_ui_properties(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(*self.config.get("ui", {}).get('window', {}).get("geometry", [100, 100, 800, 600]))
        self.setMinimumSize(*self.config.get("ui", {}).get('window', {}).get("minSize", [800, 600]))
        self.setStyleSheet(self.config.get("stylesheet", {}).get("main", ""))
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
    window = PacMan(config)
    window.show()
    window.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
    sys.exit(app.exec())
