import json
import os
from PyQt6.QtGui import QIcon, QMouseEvent, QMovie
from PyQt6.QtWidgets import (
    QFrame, QListWidget, QMainWindow, QHBoxLayout,
    QVBoxLayout, QWidget, QLabel, QStackedWidget,
    QComboBox, QFileDialog, QPushButton, QSizePolicy
)
from PyQt6.QtCore import  Qt, pyqtSignal, QEasingCurve, QPropertyAnimation, QSize
from components.dependency_tree.dependency_tree import DependencyTree
from components.installer.pypi import save_file, get_app_support_directory
from components.library.library import Library, LibraryThreads
from components.about.about import About
from components.installer.installer import Installer
from components.analysis.analysis import Analysis
from components.setting.setting import Setting
from helpers.find_python_interepreaters import PythonInterpreters
from Qt.helper_classes import LineEdit, Toast

def save_state(data, file_name = "state.json"):
    directory = get_app_support_directory()
    file_path = os.path.join(directory, file_name)
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except FileNotFoundError:
        pass

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

class ControlBar(QWidget):
    """
    A Widget that contains the window controls of the application, like a custom title bar.
    """

    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(20)
        self.config = config
        self.setObjectName("controlBar")

        self._layout()
        self._mouse_press_pos = None

    def _layout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(3, 0, 5, 0)
        layout.setSpacing(9)

        self._setup_buttons()

        name_label = QLabel(
            self.config.get('app', {}).get('name', 'PacMan')
        )
        name_label.setObjectName("nameLabel")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter )
        name_label.setContentsMargins(4, 0, 0, 0)
        layout.addWidget(self.close_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)

        layout.addWidget(name_label)


        layout.addStretch()
        self.setLayout(layout)

    def _setup_buttons(self):

        # Close Button
        self.close_button = HoverIconButton(icon_path="./assets/icons/close.svg")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(12, 12)
        self.close_button.clicked.connect(self.parent_window.close)

        # Minimize Button
        self.minimize_button = HoverIconButton(icon_path="./assets/icons/minimize.svg")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(12, 12)
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)

        # Maximize Button
        self.maximize_button = HoverIconButton(icon_path="./assets/icons/maximize.svg")
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

class OnboardingPage(QWidget):

    """
    A widget representing the onboarding page of the application.

    This page allows the user to select a project directory, choose an existing
    virtual environment, or create a new one. It guides the user through the
    initial setup process.

    Signals:
        location_selected (pyqtSignal(str, str, list)): Emitted when a project
            location and virtual environment are selected.  The arguments are:
                - project location (str)
                - virtual environment name (str)
                - list of all virtual environments (list of dicts)
        find_env_in_pc (pyqtSignal): Emitted to trigger the search for existing
            virtual environments on the system.
        switch_to_main (pyqtSignal): Emitted when the onboarding process is
            finished and the application should switch to the main window.
    """
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

        self.worker = LibraryThreads()
        self.worker.virtual_envs.connect(self._display_env)
        self.worker.new_virtual_env.connect(self._update_widget)

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
        """
        Sets up the individual pages that compose the onboarding flow and adds them to the stacked widget.
        """
        self.stacked_widget.addWidget(self._create_location_page())
        self.stacked_widget.addWidget(self._loading_virtual_env())
        self.stacked_widget.setCurrentIndex(0)

    def _create_location_page(self):
        """
        Creates the first page of the onboarding process, allowing the user to select
        a project directory and providing options for virtual environment setup.

        This page consists of:
        - A `browse_label` (within `location_container`) which, when clicked,
            triggers the `_select_location` method to open a file dialog.
        - A `select_env` container, initially hidden, which will display options
            to select an existing virtual environment or create a new one, once
            a project directory has been chosen.

        Returns:
            QWidget: The fully configured container widget for the location
                        and environment selection page.
        """
        container = QWidget()
        self.page_layout = QVBoxLayout(container)
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.browse_label.mousePressEvent = self._select_location #type: ignore
        location_layout.addWidget(self.browse_label)

        self.select_env = QFrame(container)
        self.select_env.setObjectName("selectEnv")
        self._populate_environment_container()

        self.page_layout.addWidget(self.location_container)
        self.page_layout.addWidget(self.select_env,1)

        self.select_env.setVisible(False)
        self.select_env.setFixedHeight(0)

        return container

    @staticmethod
    def _loading_virtual_env():
        """
        Creates a widget displaying a loading spinner.

        This static method generates a QFrame containing a QLabel with a QMovie
        (spinner GIF) to indicate a loading state. It's used to show progress
        while the application is performing an operation, such as searching
        for virtual environments.

        Returns:
            QFrame: A widget with a centered loading spinner.
        """
        container = QFrame()
        layout = QVBoxLayout(container)
        spinner_label = QLabel()
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        movie = QMovie("./assets/icons/spinner.gif")
        movie.setScaledSize(QSize(32, 32))
        spinner_label.setMovie(movie)
        layout.addWidget(spinner_label)
        movie.start()
        return container

    def _populate_environment_container(self):
        """
        Populates the `self.select_env` frame with widgets for selecting or creating
        virtual environments.

        This method sets up the UI elements that allow the user to:
        1. View and select an existing virtual environment found within the project directory.
        2. Input a name for a new virtual environment and choose a global Python
           interpreter from which to create it.

        It initializes labels, combo boxes, line edits, and buttons, connecting
        their actions to the appropriate methods for environment management.
        """
        layout = QVBoxLayout(self.select_env)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        # self.create_virtual_env_button.setObjectName("createVirtualEnv")

        self.create_virtual_env_button.clicked.connect(self._create_virtual_env)
        self.create_virtual_env_button.setObjectName("createVirtualEnvButton")

        # self.find_env.finished.connect(self._display_env)
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
        """
        Emits the selected project location and virtual environment details.
        """
        current_venv = ""
        curr_dir = "".join(self.drop_down_for_selecting_virtual_env.currentText().split(":")[1:]).strip()
        virtual_envs = []
        for env in self.env:
            virtual_envs.append(env)
            if env.get('venv_path') == curr_dir:
                current_venv = env.get('venv_name')

        self.location_selected.emit(self.project_location, current_venv, virtual_envs)

    def _create_virtual_env(self):
        """
        Initiates the creation of a new virtual environment.
        Validates the environment name and triggers environment creation via a worker.
        """
        text = self.name_of_venv.toPlainText()
        env_names = [env.split(os.path.sep)[-1] for env in self.list_of_virtual_env]

        if text == "":
            text = "venv"
        if text in env_names:
            self.commit_action("Same name environment already exist")
        else:
            self.worker.emit_create_virtual_env(
                self.project_location,
                self.drop_down_for_creating_python_env.currentText().split(":")[1].strip(),
                text,
                "./findLocalEnv"
            )

    def _update_widget(self, code: int, venv_path: str, venv_name, all_venv_names):
        """
        Updates the UI based on the result of a virtual environment creation or discovery operation.
        Switches to a loading screen or emits location_selected based on the provided code.
        """
        if code == 0:

            self.stacked_widget.setCurrentIndex(1)
        if code == 1:
            self.location_selected.emit(venv_path, venv_name, all_venv_names)
        pass

    def commit_action(self, message: str):
        """
        Displays a toast message to the user.
        """
        toast = Toast(self, message=message)
        toast.show()


    def _select_location(self, event):
        """
        Handles the mouse press event to select a project directory.
        Opens a file dialog, updates the UI with the selected directory,
        and initiates animations and data fetching for virtual environments.
        """
        if self.animation_running:
            return

        directory = QFileDialog.getExistingDirectory(self, "Selecting Directory")
        if directory:

            self.worker.emit_signal_for_virtual_envs(directory, "./findLocalEnv")
            self.project_location = directory
            self.browse_label.setText(f"Selected: {directory}")
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
                self.list_of_virtual_env.append(item.get('venv_path'))

                self.drop_down_for_selecting_virtual_env.addItem(
                    f"{item.get('python_version')}: {item.get('venv_path')}")
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

    loaded_all_components = pyqtSignal()
    load_libraries = pyqtSignal()
    def __init__(
        self,
        state_variables,
        config: dict = {}
    ):
        """
        Initializes the PacMan application window.

        Args:
            state_variables (dict): A dictionary containing the application's state.
            config (dict, optional): A dictionary containing the application's configuration. Defaults to {}.
        """
        super().__init__()

        self.setMouseTracking(True)
        self.config = config
        self._extra_content()
        # self.loaded_components = IntNotifier()
        # self.loaded_components.value_changed.connect(self.show_the_ui)

        # State variables
        self.state_variables = state_variables

        self._setting_ui_properties()
        self.container = QFrame()
        self._saving_screen()
        self.container.setObjectName("mainWindowContainer")
        self._setup_main_app_ui()
        self._onboarding_steps()
        self._saving = False

    def _extra_content(self):
        """
        Initializes extra content for the application.
        """
        self.current_libraries = []
        self._installer_populated = False

    def _onboarding_steps(self):
        """
        Initializes the onboarding steps for the application.
        """
        self.onboarding_widget = OnboardingPage(self.config, self)
        self.onboarding_widget.location_selected.connect(self._set_existing_python_env)
        self.onboarding_widget.switch_to_main.connect(self.switchContent)

        self.main_stack = QStackedWidget(self)
        self.main_stack.addWidget(self.onboarding_widget)
        self.main_stack.addWidget(self.container)
        self.main_stack.addWidget(self.saving_page)

        self.setCentralWidget(self.main_stack)
        if self.state_variables.get('project_folder', "") == "":
            self.main_stack.setCurrentWidget(self.onboarding_widget)
        else:
            self.main_stack.setCurrentWidget(self.container)
            self._set_existing_python_env(
                self.state_variables.get('project_folder', ''),
                self.state_variables.get('virtual_env_name', ''),
                self.state_variables.get('loaded_virtual_envs', [])
            )


    def _set_state_variables(self, project_folder, virtual_env_name, virtual_env_list):
        """
        Sets the state variables for the application.

        Args:
            project_folder (str): The path to the project folder.
            virtual_env_name (str): The name of the virtual environment.
        """
        self.state_variables['project_folder'] = project_folder
        self.state_variables['virtual_env_name'] = virtual_env_name
        self.state_variables['loaded_virtual_envs'] = virtual_env_list

    def _set_existing_python_env(self, curr_dir, current_venv, virtual_envs):
        """
        Sets the existing python environment for the application.

        Args:
            curr_dir (str): The current directory.
            current_venv (str): The current virtual environment.
            virtual_envs (list): A list of virtual environments.
        """
        self.main_stack.setCurrentWidget(self.container)
        self.libraries.selectLocationFromMain(curr_dir, current_venv, virtual_envs)

    def _setup_main_app_ui(self):
        """
        Sets up the main application UI.
        """
        self.libraries = Library(config = self.config)
        self.installer = Installer(config = self.config)
        self.analysis = Analysis()
        self.dependency_tree = DependencyTree()
        self.settings = Setting()
        self.about = About()

        self.contentDict = {
            "Libraries": self.libraries,
            "Installer": self.installer,
            "Analysis": self.analysis,
            "Dependency Tree": self.dependency_tree,
            "Settings": self.settings,
            "About": self.about
        }
        self.navLists = ["Libraries", "Installer", "Analysis", "Dependency Tree", "Settings", "About"]
        # self.navLists = ["Libraries", "Analysis", "Dependency Tree", "Settings", "About"]

        self.libraries.current_state.connect(self._set_state_variables)
        self.libraries.libraries_emitter.connect(self._retrieve_libraries_content)
        self.libraries.python_exec.connect(self.installer.set_python_exec)
        self.installer.populationFinished.connect(self._set_status_installer)
        self.installer.installed.connect(self.libraries.refetch_libraries)

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

    def _set_status_installer(self):
        self._installer_populated = True
        self.installer.set_status(self.current_libraries)

    def _retrieve_libraries_content(self, libraries:list):
        """
        Retrieves the content of the libraries.
        Args:
            libraries (list): A list of libraries.
        """
        self.current_libraries = [library['metadata']['name'] for library in libraries]
        if self._installer_populated:
            self._set_status_installer()


    def switchContent(self):
        """
        Switches the content of the application.
        """
        self.main_stack.setCurrentWidget(self.container)

    def _setting_ui_properties(self):
        """
        Sets the UI properties of the application.
        """
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(*self.config.get("ui", {}).get('window', {}).get("geometry", [100, 100, 800, 600]))
        self.setMinimumSize(*self.config.get("ui", {}).get('window', {}).get("minSize", [800, 600]))
        self.appName = self.config.get("application", {}).get("name", "")

    def sideBar(self):
        """
        Creates the side bar of the application.
        Returns:
            tuple: A tuple containing the side bar and the navigation items.
        """
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

    def _saving_screen(self):
        self.saving_page = QWidget()
        self.saving_page.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.saving_page.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.saving_page.setFixedSize(400, 200)
        self.saving_page.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout(self.saving_page)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Saving...")
        label.setStyleSheet("color: #fff; font-size: 48px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.saving_page.setLayout(layout)

    def createContentArea(self):
        """
        Create stack area for all the different pages (eg. libraries, installer ...)
        """
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
        """
        Saves the current state of the application when the application is closed.

        Args:
            a0 (QCloseEvent): The close event.
        """
        self.main_stack.setCurrentIndex(3)
        if not self.state_variables.get('project_folder', "") == "":
            save_state(
                self.state_variables
            )
            save_file(self.installer.allLibraries)


        # if "Installer" in self.contentDict:
        #     self.contentDict["Installer"].getDetails.stopThread()
        super().closeEvent(a0)
