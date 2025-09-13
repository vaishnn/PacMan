from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QFileDialog, QLineEdit, QMessageBox, QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QLabel, QListWidgetItem, QPushButton
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtWidgets import QSizePolicy

from library.tool_tip_library import GetLibraryDetails
from workers.delete_library import UninstallManager
from workers.fetch_list_libraries import FetchLibraryList

# Implementation to be DONE of Better Layout and After Changing virtual Path it doesn't shows the Library Details

class Worker(QThread):
    pass

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
    listLibraryRefreshed = pyqtSignal()
    show_env_box = pyqtSignal()
    libraries_emitter = pyqtSignal(list)
    current_state = pyqtSignal(str, str) # Current state of selected Project Folder and Virtual Env name selected
    python_exec = pyqtSignal(str)
    def __init__(self, config, parent=None):
        super().__init__(parent)
        if not hasattr(self, 'config'):
            self.config = config
        self.setObjectName("library")
        self._init_properties()
        self._init_managers()
        self._init_ui()
        self._connect_signals()

    def _init_properties(self):
        """Initializes non-UI properties, caches, and maps."""
        self.toolTipCache = {}
        self.itemMap = {}
        self.animate_env_box = False
        self.pythonExecPath = ""
        self.already_inside_project = False

    def _init_managers(self):
        """Initializes helper classes for fetching details and uninstalling."""
        # Tooltip Fetching Manager
        self.fetch_list_of_libraries = FetchLibraryList()
        self.getLibraryDetails = GetLibraryDetails()

        # Uninstall Manager
        uninstall_timeout = int(self.config.get("controls", {}).get("library", {}).get("uninstallManagerTimout", 10000))
        self.uninstallManager = UninstallManager(IDLE_TIMOUT=uninstall_timeout)


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
        self.change_env_in_same_directory.currentIndexChanged.connect(self._change_virtual_env)


        button_layout.addWidget(self.labelLocation, 1)
        button_layout.addWidget(self.change_env_in_same_directory, 2)
        parent_layout.addLayout(button_layout)

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

    def _change_virtual_env(self):
        current_location = self.labelLocation.text()
        current_virtual_env = self.change_env_in_same_directory.currentText().split(":")[0].strip()
        self.current_state.emit(current_location, current_virtual_env)
        self.selectLocationFromMain(current_location, current_virtual_env, "")

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

        self.libraryList = QListWidget()
        self.libraryList.setObjectName("libraryList")
        library_layout.addWidget(self.libraryList)

        parent_layout.addLayout(library_layout)

    def _connect_signals(self):
        """Connects the class's own signals to their respective slots."""
        self.fetch_list_of_libraries.libraries.connect(self.handleListLibraries)
        self.uninstallManager.uninstallFinished.connect(self.onUninstallFinished)
        self.getLibraryDetails.detailsWithName.connect(self.getLibraryDetailsThroughClass)
        self.show_env_box.connect(self._expand_change_env)
        self.listLibraryRefreshed.connect(self.getLibraryDetails.startThread)
        self.listLibraryRefreshed.connect(self.startAllTooltipFetches)

    def whenTimerForToolTipIsFinished(self):
        self.listLibraryRefreshed.emit()

    def setPythonExecPath(self, path):
        self.pythonExecPath = path
        self.python_exec.emit(path)

    def handleListLibraries(self, pythonPath: str, libraries: list, virtual_env_names: list):
        # self.contentDict['Libraries'].libraryList.clear()
        self.libraries_emitter.emit(libraries)
        if not self.already_inside_project:

            self._expand_change_env()
            self.already_inside_project = True
            self.change_env_in_same_directory.clear()
            if libraries:
                for envs in virtual_env_names:
                    self.change_env_in_same_directory.addItem(envs, 20)
        self.setPythonExecPath(pythonPath)
        self.addItems(libraries)


    def selectLocation(self, event):
        directoryPath = QFileDialog.getExistingDirectory(
            self, "Select Directory")
        if directoryPath:
            self.already_inside_project = False
            self.labelLocation.setText(f"{directoryPath}")
            self.fetch_list_of_libraries.get_details(directoryPath, "")

    def selectLocationFromMain(self, directoryPath, venv_name, virtual_envs):
            self.labelLocation.setText(f"{directoryPath}")
            self.fetch_list_of_libraries.get_details(directoryPath, venv_name)

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
        self.all_items_data = itemsList
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

    def sortItemsList(self, emit: bool = False):
        self.searchBar.show()
        query = self.searchBar.text()
        items = []
        if not query:
            items = sorted(self.all_items_data, key=lambda x: x['name'])
        else:
            items = self.rankQuery(self.all_items_data, query)

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
            nameLibraryPanel = QLabel(item["name"])
            nameLibraryPanel.setObjectName("nameLibraryPanel")

            # Version of the Library
            versionLibraryPanel = QLabel(item["version"])
            versionLibraryPanel.setObjectName("versionLibraryPanel")

            # Tag of The Library I means Installed outside and D means Downloaded from the world wide web
            sizepanel = QLabel()
            sizepanel.setText(self.human_readable_size(item["size"]))
            sizepanel.setFixedWidth(50)
            sizepanel.setObjectName("sizeLibraryPanel")

            # Changing Properties of QLabels
            uninstallButton = QPushButton()
            uninstallButton.setFixedSize(30, 30)
            uninstallButton.setObjectName("deleteButtonFromLibraryListWidget")
            uninstallButton.setIcon(QIcon(
                self.config.get("paths", {}).get("assets", {}).get("images", {}).get("uninstall"),
            ))
            uninstallButton.setIconSize(QSize(22, 22))

            # Adding Widget in proper Order
            listWidgetLayout.addWidget(sizepanel)
            listWidgetLayout.addWidget(nameLibraryPanel)
            listWidgetLayout.addWidget(versionLibraryPanel)
            listWidgetLayout.addWidget(uninstallButton)
            listItem = QListWidgetItem(self.libraryList)
            listItem.setSizeHint(QSize(0, 55))
            self.libraryList.addItem(listItem)
            self.libraryList.setItemWidget(listItem, listLibraryWidget)

            if item["name"] in self.toolTipCache:
                listLibraryWidget.setToolTip(self.toolTipCache[item["name"]])
            else:
                listLibraryWidget.setToolTip("Loading details...")
            self.itemMap[item["name"]] = (listLibraryWidget, listItem)
            uninstallButton.clicked.connect(
                lambda checked=False, packageName=item["name"]: self.startLibraryUninstaller(packageName))
        if emit:
            self.listLibraryRefreshed.emit()
        else:
            self.searchBarTypingTimer.start()

    def startLibraryUninstaller(self, packageName):
        reply = QMessageBox.warning(
            self,
            'Confirm Uninstall',
            f"Uninstalling {packageName}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if packageName in self.itemMap:
                widget = self.itemMap[packageName][0]
                widget.setToolTip("Uninstalling...")
            self.uninstallManager.requestUninstall(
                self.pythonExecPath, packageName)

    def searchItemsInTheLibrary(self):
        pass

    @pyqtSlot(str, bool)
    def onUninstallFinished(self, packageName, success):
        if success:
            listItem = self.itemMap.pop(packageName)
            if listItem:
                row = self.libraryList.row(listItem[1])
                self.libraryList.takeItem(row)

    def startAllTooltipFetches(self):
        for package_name, widget in self.itemMap.items():
            widget[0].setToolTip("Fetching details...")
            self.getLibraryDetails.fetchDetailLibraryDetails(
                self.pythonExecPath, package_name)

    @pyqtSlot(str, dict)
    def getLibraryDetailsThroughClass(self, name, libraryDetails: dict):
        listItem = self.itemMap.get(name)
        if listItem:
            summary = libraryDetails["Summary"]
            author = libraryDetails["Author"]
            requires = libraryDetails["Requires"]
            required_by = libraryDetails["Required-by"]
            tooltip = f"""
            <p style="width:400px">
            <b>Summary:</b> {summary.strip()} <br>
            <b>Author:</b> {author if author else "<em style='color:grey'>No Author Provided</em>"} <br>
            <b>Requires:</b> {requires if requires else "<em style='color:grey'>No Dependencies</em>"} <br>
            <b>Required-by:</b> {required_by if required_by else "<em style='color:grey'>No Dependencies</em>"}
            </p>"""
            listItem[0].setToolTip(tooltip)
            self.toolTipCache[name] = tooltip

    def closeEvent(self, event):  # type: ignore
        self.getLibraryDetails.stop()
        self.uninstallManager.stop()
        super().closeEvent(event)
