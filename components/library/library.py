import json
import os
import subprocess
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QFileDialog, QLineEdit, QMessageBox, QStackedWidget, QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QLabel, QListWidgetItem, QPushButton
from PyQt6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QThread, QTimer, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtWidgets import QSizePolicy
from Qt.CustomToolTip import InteractiveToolTip
from copy import deepcopy
import pacman

# Implementation to be DONE of Better Layout and After Changing virtual Path it doesn't shows the Library Details

class LibraryWorker(QObject):
    details_with_virtual_envs = pyqtSignal(str, list, list)
    new_virtual_env = pyqtSignal(int, str, str, list)
    virtual_envs = pyqtSignal(list)
    details = pyqtSignal(list)
    @pyqtSlot(str, str, str)
    def fetch_only_details(self, directory, load_library_exe, venv_name):
        """only fetches details of the library by running the compiled Go Code"""
        if directory == "" or venv_name == "":
            self.details.emit([])
            return

        result_details = subprocess.run(
            [load_library_exe, os.path.join(directory, venv_name)],
            capture_output=True,
            text=True,
        )
        print(result_details.stderr)
        if result_details.stdout.strip() == "":
            self.details.emit([])
            return

        try:
            details = json.loads(result_details.stdout).get('installed', [])
            self.details.emit(details)
        except json.JSONDecodeError:
            self.details.emit([])
            return

    @pyqtSlot(str, str)
    def fetch_virtual_envs(self, directory, find_env_exe):
        """fetches virtual environments by running the compiled Go Code"""
        if not directory or not find_env_exe:
            self.virtual_envs.emit([])
            return

        result_venvs = subprocess.run(
            [find_env_exe, directory],
            capture_output=True,
            text=True,
        )
        venvs = json.loads(result_venvs.stdout)
        if not venvs:
            self.virtual_envs.emit([])
            return
        try:
            venvs = json.loads(result_venvs.stdout)
            self.virtual_envs.emit(venvs)
            return
        except json.JSONDecodeError:
            self.virtual_envs.emit([])
            return

    @pyqtSlot(str, str, str, str)
    def initialize_new_virtual_env(self, directory, python_path, virtual_env_name, find_env_exe):
        if not (directory or python_path or virtual_env_name, find_env_exe):
            self.new_virtual_env.emit(1, "", "", "")
        self.new_virtual_env.emit(0, "", "", [])
        is_pip_preset = subprocess.run([python_path, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
        )
        if is_pip_preset.returncode == 1:
            # requires python>=3.4
            subprocess.run([python_path, "-m", "ensurepip", "--upgrade"])
        subprocess.run([python_path, "-m", "venv", virtual_env_name], capture_output=True, text=True, check=False, cwd=directory)
        result_venvs = subprocess.run(
            [find_env_exe, directory],
            capture_output=True,
            text=True
        )
        try:
            venvs = json.loads(result_venvs.stdout)
        except json.JSONDecodeError:
            venvs = []
        self.new_virtual_env.emit(1, directory, virtual_env_name, venvs)

class Uninstall(QThread):
    finished = pyqtSignal(int, str, str, QPushButton) # (success_code, library_name, python_path, button)

    def __init__(self, python_path, library, uninstall_button):
        super().__init__()
        self.python_path = python_path
        self.library = library
        self.uninstall_button = uninstall_button

    def run(self):
        result = subprocess.run(
            [self.python_path, "-m", "pip", "uninstall", "-y", self.library],
            text=True,
        )

        if result.returncode == 0:
            self.finished.emit(1, self.library, self.python_path, self.uninstall_button)
        else:
            self.finished.emit(-1, self.library, self.python_path, self.uninstall_button)

class LibraryThreads(QObject):
    new_virtual_env = pyqtSignal(int, str, str, list)
    details_with_virtual_envs = pyqtSignal(str, list, list)
    virtual_envs = pyqtSignal(list)
    details = pyqtSignal(list)
    get_details = pyqtSignal(str, str, str)
    get_virtual_envs = pyqtSignal(str, str)
    get_details_with_virtual_envs = pyqtSignal(str, str, str)
    create_virtual_env = pyqtSignal(str, str, str, str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.thread_library = QThread()
        self.worker = LibraryWorker()
        self.worker.moveToThread(self.thread_library)
        self.worker.details_with_virtual_envs.connect(self.details_with_virtual_envs.emit)
        self.worker.virtual_envs.connect(self.virtual_envs.emit)
        self.worker.details.connect(self.details.emit)
        self.worker.new_virtual_env.connect(self.new_virtual_env.emit)
        self.thread_library.start()
        self.get_details.connect(self.worker.fetch_only_details)
        self.get_virtual_envs.connect(self.worker.fetch_virtual_envs)
        self.create_virtual_env.connect(self.worker.initialize_new_virtual_env)

    def emit_signal_for_details(self, directory, load_library_exe, venv_name):
        self.get_details.emit(directory, load_library_exe, venv_name)

    def emit_signal_for_virtual_envs(self, directory, load_library_exe):
        self.get_virtual_envs.emit(directory, load_library_exe)

    def emit_signal_for_details_with_virtual_envs(self, directory, load_library_exe, venv_name):
        self.get_details_with_virtual_envs.emit(directory, load_library_exe, venv_name)

    def emit_create_virtual_env(self, directory, python_path, venv_name, find_env_exe):
        self.create_virtual_env.emit(directory, python_path, venv_name, find_env_exe)

    def quit(self):
        if self.thread_library.isRunning():
            self.thread_library.quit()
            self.thread_library.wait()

class Library(QWidget):
    """
    This class is for all Library Related Widgets

    What it does:
    - Provide a list of installed libraries
    - Allow user to search for libraries
    - Display details of selected library
    - Allow user to uninstall selected library
    - And more if we want
    """
    venv_loaded = pyqtSignal(str, str, list)
    listLibraryRefreshed = pyqtSignal()
    show_env_box = pyqtSignal()
    libraries_emitter = pyqtSignal(list)
    current_state = pyqtSignal(str, str, list) # Current state of selected Project Folder and Virtual Env name selected
    python_exec = pyqtSignal(str)
    def __init__(self, config, parent=None):
        super().__init__(parent)
        if not hasattr(self, 'config'):
            self.config = config
        self.setObjectName("library")
        self._init_properties()
        self._worker_thread()
        self._init_ui()
        self._connect_signals()

    def _init_properties(self):
        """Initializes non-UI properties, caches, and maps."""
        self.toolTipCache = {}
        self.itemMap = {}
        self.animate_env_box = False
        self.current_loaded_virtual_envs_list = []
        self.current_virtual_env = ""
        self.pythonExecPath = ""
        self.already_inside_project = False
        self.current_dir = ""
        self.uninstallManager = None

    def _worker_thread(self):
        self.worker = LibraryThreads()
        self.worker.details.connect(self.handleListLibraries)
        self.worker.virtual_envs.connect(self.venv_loaded_connected)

    def _init_ui(self):
        """Initializes the main user interface layout and components."""
        self.setObjectName("library")
        self.setStyleSheet(self.config.get("stylesheet", {}).get("tooltip", ""))

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self._setup_path_selection_bar(page_layout)

        # Create a container for the search bar and list
        library_section_layout = QVBoxLayout()
        library_section_layout.setContentsMargins(0, 2, 0, 0)
        library_section_layout.setSpacing(0)

        self._setup_search_bar(library_section_layout)
        self._setup_library_list(library_section_layout)

        page_layout.addLayout(library_section_layout)

    def _setup_path_selection_bar(self, parent_layout):
        """Creates the top bar for selecting the virtual environment path."""
        button_layout = QHBoxLayout()
        margin = self.config.get("ui", {}).get("window", {}).get('library', {}).get("labelLocation", {}).get("contentMargin", [0, 0, 0, 0])
        button_layout.setContentsMargins(*margin)

        # Label for selecting path
        self.labelLocation = QLabel("Select Path")
        self.labelLocation.setObjectName("labelLocation")
        self.labelLocation.setFixedHeight(30)
        self.labelLocation.setCursor(Qt.CursorShape.PointingHandCursor)
        self.labelLocation.mousePressEvent = self.selectLocation  # type: ignore

        # for changing the virtual env in the same directory
        self.change_env_in_same_directory = QComboBox()
        self.change_env_in_same_directory.setFixedHeight(30)
        self.change_env_in_same_directory.setFixedWidth(0)
        self.change_env_in_same_directory.setVisible(False)
        self.change_env_in_same_directory.currentIndexChanged.connect(self._on_env_inventory_in_same_directory)
        self.change_env_in_same_directory.setObjectName("change_env_in_same_directory")


        button_layout.addWidget(self.labelLocation, 1)
        button_layout.addWidget(self.change_env_in_same_directory, 2)
        parent_layout.addLayout(button_layout)

    def _on_env_inventory_in_same_directory(self):
        self.stacked_library_with_loading_screen.setCurrentIndex(1)
        current_location = self.current_dir
        current_virtual_env = self.change_env_in_same_directory.currentText()
        self._change_virtual_env(current_location, current_virtual_env)

    def _expand_change_env(self):
        """Animtes the virtual env selector"""
        if self.animate_env_box:
            return

        self.animate_env_box = True
        self.change_env_in_same_directory.setVisible(True)
        # final_width = self.change_env_in_same_directory.sizeHint().height()
        final_width = 200
        self.animation = QPropertyAnimation(
            self.change_env_in_same_directory, b'maximumWidth'
        )
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(final_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self.animation.finished.connect(
            lambda: setattr(self, 'animate_env_box', False)
        )
        self.animation.start()

    def _change_virtual_env(self, directory, venv_name):

        if not directory or not venv_name:
            return
        self.current_state.emit(directory, venv_name, self.current_loaded_virtual_envs_list)
        self.current_virtual_env = venv_name
        self.worker.emit_signal_for_details(self.current_dir, './load_library', self.current_virtual_env)

    def _setup_search_bar(self, parent_layout):
        """Creates the search bar and its associated typing timer."""
        self.searchBar = QLineEdit()
        self.searchBar.hide()
        self.searchBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.searchBar.setFixedHeight(30)
        self.searchBar.setPlaceholderText("Search for libraries")
        self.searchBar.setObjectName("searchBarInLibraryListWidget")
        self.searchBar.textChanged.connect(self.sortItemsList)
        parent_layout.addWidget(self.searchBar)

        # Timer to delay actions after user stops typing in the search bar
        self.searchBarTypingTimer = QTimer()
        self.searchBarTypingTimer.setSingleShot(True)
        self.searchBarTypingTimer.setInterval(500)
        self.searchBarTypingTimer.timeout.connect(self.whenTimerForToolTipIsFinished)

    def _setup_library_list(self, parent_layout):
        """Creates the main QListWidget for displaying the libraries."""
        library_layout = QVBoxLayout()
        library_layout.setContentsMargins(0, 10, 0, 0)
        self.stacked_library_with_loading_screen = QStackedWidget()
        self.libraryList = QListWidget()
        self.stacked_library_with_loading_screen.addWidget(self.libraryList)
        self.loading_page = pacman.OnboardingPage._loading_virtual_env()
        self.stacked_library_with_loading_screen.addWidget(self.loading_page)

        self.libraryList.setObjectName("libraryList")
        library_layout.addWidget(self.stacked_library_with_loading_screen)

        parent_layout.addLayout(library_layout)

    def _connect_signals(self):
        """Connects the class's own signals to their respective slots."""
        self.show_env_box.connect(self._expand_change_env)
        self.venv_loaded.connect(self.on_venvs_loaded)

    def whenTimerForToolTipIsFinished(self):
        self.listLibraryRefreshed.emit()

    def setPythonExecPath(self, path):
        self.pythonExecPath = path
        self.python_exec.emit(path)

    def handleListLibraries(self, libraries: list):
        self.addItems(libraries)

    def on_venvs_loaded(self, directory_path, current_venv, virtual_env_names):
        # Block signals to prevent the signal loop
        self.change_env_in_same_directory.clear()
        self.change_env_in_same_directory.blockSignals(True)

        self.setPythonExecPath([env['python_path'] for env in virtual_env_names if env['venv_name'] == current_venv][0])
        if virtual_env_names:


            for env in deepcopy(virtual_env_names):
                if os.path.exists(env["venv_path"]):
                    self.change_env_in_same_directory.addItem(env['venv_name'])
                else:
                    virtual_env_names.remove(env)
                    if current_venv == env['venv_name']:
                        current_venv = self.change_env_in_same_directory.currentText()

            self.stacked_library_with_loading_screen.setCurrentIndex(1)
            self.current_loaded_virtual_envs_list = virtual_env_names
            self._expand_change_env() # Animate the box
            self.change_env_in_same_directory.setCurrentText(self.current_virtual_env)
            # Unblock signals now that we are done modifying
            self.change_env_in_same_directory.blockSignals(False)

            # Manually trigger the load for the first item
            self._change_virtual_env(self.current_dir, self.current_virtual_env)
        else:
            self.libraryList.clear() # No venvs found
            QMessageBox.information(self, "No Environments", "No virtual environments found in this directory.")
            self.change_env_in_same_directory.blockSignals(False)


    def selectLocation(self, event):
        directoryPath = QFileDialog.getExistingDirectory(
            self, "Select Directory")
        if directoryPath:
            self.current_dir = directoryPath
            self.already_inside_project = False
            self.labelLocation.setText(f"{directoryPath}")
            self.worker.emit_signal_for_virtual_envs(directoryPath, "./findLocalEnv")

    def venv_loaded_connected(self, venv_list):
        self.current_virtual_env = venv_list[0].get('venv_name')
        self.venv_loaded.emit( self.current_dir, venv_list[0].get('venv_name'), venv_list)

    def selectLocationFromMain(self, directoryPath, venv_name, virtual_envs):
        self.current_dir = directoryPath
        self.labelLocation.setText(f"{directoryPath}")
        self.current_virtual_env = venv_name
        self.venv_loaded.emit(directoryPath, venv_name, virtual_envs)

    def rankQuery(self, dataList, query):
        lowerQuery = query.lower()
        matches = [
            item for item in dataList
            if lowerQuery in item['name'].lower()
        ]
        sortedMatches = sorted(
            matches,
            key=lambda item: item['name'].lower().find(lowerQuery)
        )
        return sortedMatches

    def addItems(self, itemsList):
        self.toolTipCache = {}
        self.searchBar.show()
        self.all_items_data = [items['metadata'] for items in itemsList]
        self.sortItemsList(True)

    def human_readable_size(self, size: int) -> str:
        if size/(1024*1024*1024)<0.1:
            if size/(1024*1024)<0.1:
                if size/(1024)<0.1:
                    if size < 0.1:
                        return f"{size*8} <span style='font-size:8pt'>b</span>"
                    else:
                        return f"{size:.2f} <span style='font-size:8pt'>B</span>"
                else:
                    return f"{size / 1024:.2f} <span style='font-size:8pt'>KB</span>"
            else:
                return f"{size / (1024 * 1024):.2f} <span style='font-size:8pt'>MB</span>"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} <span style='font-size:8pt'>GB</span>"

    @staticmethod
    def format_project_urls(urls):
        """Formats a list of project URLs into clickable <a> tags."""
        if not urls:
            return ""
        links = []
        for url_str in urls:
            # Handles formats like "Homepage, https://..."
            parts = [part.strip() for part in url_str.split(',', 1)]
            if len(parts) == 2:
                name, url = parts
                links.append(f'<a href="{url}" style="color: #8ab4f8;">{name}</a>')
            else: # Fallback for plain URLs
                links.append(f'<a href="{url_str}" style="color: #8ab4f8;">{url_str}</a>')
        return "<br>".join(links)

    @staticmethod
    def format_tooltip_html(item, font_family_name):
        """
        Takes a dictionary of package metadata and formats it into a styled HTML string.
        """
        table_rows = []

        # --- Core Info ---
        if item.get('name'):
            table_rows.append(f'<tr><td class="tooltip-label">Name</td><td class="tooltip-value">{item["name"]}</td></tr>')
        if item.get('version'):
            table_rows.append(f'<tr><td class="tooltip-label">Version</td><td class="tooltip-value">{item["version"]}</td></tr>')
        if item.get('summary'):
            table_rows.append(f'<tr><td class="tooltip-label">Summary</td><td class="tooltip-value">{item["summary"].strip()}</td></tr>')
        if item.get('author'):
            table_rows.append(f'<tr><td class="tooltip-label">Author</td><td class="tooltip-value">{item["author"]}</td></tr>')

        # --- Requirements ---
        if item.get('requires_python'):
            table_rows.append(f'<tr><td class="tooltip-label">Requires Python</td><td class="tooltip-value">{item["requires_python"]}</td></tr>')
        if item.get('requires_dist'):
            deps_html = "<br>".join(item['requires_dist'])
            table_rows.append(f'<tr><td class="tooltip-label">Dependencies</td><td class="tooltip-value">{deps_html}</td></tr>')

        # --- License Info (Always shows License field) ---
        license_val = item.get('license') if item.get('license') else "<span class='tooltip-placeholder'>Not Provided</span>"
        table_rows.append(f'<tr><td class="tooltip-label">License</td><td class="tooltip-value">{license_val}</td></tr>')
        if item.get('license_expression'):
            table_rows.append(f'<tr><td class="tooltip-label">License Expression</td><td class="tooltip-value">{item["license_expression"]}</td></tr>')
        if item.get('license_file'):
            files_html = "<br>".join(item['license_file'])
            table_rows.append(f'<tr><td class="tooltip-label">License Files</td><td class="tooltip-value">{files_html}</td></tr>')

        # --- Links & Details ---
        if item.get('project_url'):
            urls_html = Library.format_project_urls(item['project_url'])
            table_rows.append(f'<tr><td class="tooltip-label">Project URLs</td><td class="tooltip-value">{urls_html}</td></tr>')
        if item.get('provides_extra'):
            provides_html = "<br>".join(item['provides_extra'])
            table_rows.append(f'<tr><td class="tooltip-label">Provides</td><td class="tooltip-value">{provides_html}</td></tr>')
        if item.get('classifier'):
            classifiers_html = "<br>".join(item['classifier'])
            table_rows.append(f'<tr><td class="tooltip-label">Classifiers</td><td class="tooltip-value">{classifiers_html}</td></tr>')

        all_rows_html = "\n".join(table_rows)

        return f"""
        <style>
            .tooltip-container {{ font-family: '{font_family_name}', sans-serif; font-size: 14px; max-width: 500px; line-height: 1.5; }}
            .tooltip-table {{ border-spacing: 0; width: 100%; }}
            .tooltip-table td {{ padding: 2px 8px; vertical-align: top; }}
            .tooltip-label {{ font-weight: 600; white-space: nowrap; text-align: left; padding-right: 12px; color: #999999; }}
            .tooltip-value {{ color: #FFFFFF; }}
            .tooltip-placeholder {{ color: #777777; font-style: italic; }}
            a {{ text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
        <div class="tooltip-container">
            <table class="tooltip-table">
                {all_rows_html}
            </table>
        </div>
        """


    def sortItemsList(self, emit: bool = False):
        """
        Updates the library list with the provided items, applying search and sorting.

        Args:
            itemsList (list): A list of dictionaries, where each dictionary contains
                              metadata about an installed library.
            emit (bool, optional): Whether to emit the listLibraryRefreshed signal after
                                   updating the list. Defaults to False, which starts a timer
                                   to delay the signal emission.
        """
        self.searchBar.show()
        query = self.searchBar.text()
        items = []
        if not query:
            items = sorted(self.all_items_data, key=lambda x: x['name'])
        else:
            items = self.rankQuery([item_data for item_data in self.all_items_data], query)

        # Clear the UI and re-populate it with the sorted list
        self.libraryList.clear()
        self.itemMap.clear()
        for item in items:
            listLibraryWidget = QWidget()
            listLibraryWidget.setObjectName("listLibraryWidget")
            listLibraryWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            listWidgetLayout = QHBoxLayout(listLibraryWidget)
            # All the QLabels

            # Name of the Library
            nameLibraryPanel = QLabel(item['name'])
            nameLibraryPanel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            nameLibraryPanel.setObjectName("nameLibraryPanel")

            # Version of the Library
            versionLibraryPanel = QLabel(item['version'])
            versionLibraryPanel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            versionLibraryPanel.setObjectName("versionLibraryPanel")

            # Tag of The Library I means Installed outside and D means Downloaded from the world wide web
            sizepanel = QLabel()
            sizepanel.setText(self.human_readable_size(item['size']))
            sizepanel.setFixedWidth(60)
            sizepanel.setObjectName("sizeLibraryPanel")

            # Changing Properties of QLabels
            uninstallButton = QPushButton()
            uninstallButton.setFixedSize(30, 30)
            uninstallButton.setObjectName("deleteButtonFromLibraryListWidget")
            uninstallButton.setIcon(QIcon(
                self.config.get("paths", {}).get("assets", {}).get("images", {}).get("uninstall"),
            ))
            uninstallButton.setIconSize(QSize(22, 22))

            classifiers = item.get('classifier', [])
            classifiers = classifiers if classifiers else []
            license = ""
            if item.get('license_expression', "") != "":
                license = item['license_expression'].strip()
            for classifier in classifiers:
                if "License :: OSI Approved" in classifier:
                    license = classifier.split("::")[-1].strip()
            if license == "":
                for classifier in classifiers:
                    if "License :: OSI Approved" in classifier:
                        license = classifier.split("::")[-1].strip()
                if item.get('license', "") != "":
                    license = item['license'].strip()

            license_panel = QLabel()
            license_panel.setText(license.replace("License", "").strip())
            license_panel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # license_panel.setFixedWidth(100)
            license_panel.setObjectName("licenseLibraryPanel")
            license_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


            # Adding Widget in proper Order
            listWidgetLayout.addWidget(sizepanel)
            listWidgetLayout.addWidget(nameLibraryPanel)
            listWidgetLayout.addWidget(license_panel)
            listWidgetLayout.addWidget(versionLibraryPanel)
            listWidgetLayout.addSpacing(100)
            listWidgetLayout.addWidget(uninstallButton)
            listItem = QListWidgetItem(self.libraryList)
            listItem.setSizeHint(QSize(0, 55))
            self.libraryList.addItem(listItem)
            self.libraryList.setItemWidget(listItem, listLibraryWidget)

            interactiveToolTip = InteractiveToolTip(self)
            interactiveToolTip.install_on(listLibraryWidget)
            interactiveToolTip.set_object_name("listLibraryWidgetToolTip")
            interactiveToolTip.set_content(self.format_tooltip_html(item, 'figtree'))

            self.itemMap[item['name']] = (listLibraryWidget, listItem)
            uninstallButton.clicked.connect(
                lambda checked=False, packageName=item['name'], uninstall_button=uninstallButton: self.startLibraryUninstaller(packageName, uninstallButton))
        if emit:
            self.listLibraryRefreshed.emit()
        else:
            self.searchBarTypingTimer.start()
        self.stacked_library_with_loading_screen.setCurrentIndex(0)

    def startLibraryUninstaller(self, packageName, uninstall_button: QPushButton):
        reply = QMessageBox.warning(
            self,
            'Confirm Uninstall',
            f"Uninstalling {packageName}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if packageName in self.itemMap:
                uninstall_button.setIcon(
                    QIcon(self.config.get('paths', {}).get('assets', {}).get('images', {}).get('uninstalling', ''))
                )
            self.uninstallManager = Uninstall(self.pythonExecPath, packageName, uninstall_button)
            self.uninstallManager.finished.connect(self.onUninstallFinished)
            self.uninstallManager.finished.connect(self.uninstallManager.deleteLater)
            self.uninstallManager.start()

    def refetch_libraries(self):
        self._change_virtual_env(self.current_dir, self.current_virtual_env)

    @pyqtSlot(int, str, str, QPushButton)
    def onUninstallFinished(self, success, packageName, python_path, uninstall_button: QPushButton):

        def _pop_item_in_sometime(self):
            listItem = self.itemMap.pop(packageName)
            if listItem:
                row = self.libraryList.row(listItem[1])
                self.libraryList.takeItem(row)
        if success:
            uninstall_button.setIcon(
                QIcon(self.config.get('paths', {}).get('assets', {}).get('images', {}).get('uninstalled', ''))
            )
            QTimer.singleShot(2000, lambda: _pop_item_in_sometime(self))
        else:
            uninstall_button.setIcon(
                QIcon(self.config.get('paths', {}).get('assets', {}).get('images', {}).get('failed', ''))
            )
            uninstall_button.setEnabled(False)
        self.uninstallManager = None
