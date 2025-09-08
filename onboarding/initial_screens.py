import os
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QPushButton, QSizePolicy, QVBoxLayout, QLabel, QStackedWidget, QWidget
)
from PyQt6.QtCore import  QEasingCurve, QPropertyAnimation, QSize, Qt, pyqtSignal
from ui.control_bar import ControlBar
from helpers.where_python import PythonInterpreters
from workers.initialize_new_virtual_env import InitializingEnvironment
from helpers.helper_classes import LineEdit, Toast
from workers.find_virtual_env import FindEnvironment

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

        self.installing_virtual_env = InitializingEnvironment()
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
        movie = QMovie("./assets/icons/spinner.gif")
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
        env_names = [env.split(os.path.sep)[-1] for env in self.list_of_virtual_env]
        if text == "":
            text = "venv"
        if text in env_names:
            self.commit_action("Same name environment already exist")
        else:
            self.installing_virtual_env.start(python_path, virtual_env_path, text)

    def _update_widget(self, code: int, venv_path: str, venv_name: str, all_venv_names):
        if code == 0:
            self.stacked_widget.setCurrentIndex(1)
        if code == 1:
            self.location_selected.emit(venv_path, venv_name, all_venv_names)
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
