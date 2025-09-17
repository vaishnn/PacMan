from PyQt6.QtCore import QModelIndex, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QListView, QSizePolicy, QVBoxLayout, QWidget

# Imports from our new package structure
from .threads import GettingInstallerLibraryDetails, InstallerLibraries, PyPiRunner
from .models import LibraryListModel
from .models import DataRole
from .delegates import PyPIitemDelegate

class Installer(QWidget):
    """Installer widget for installing libraries"""
    # Current Implementation just brings 30 libraries
    # It is storing all the libraries but it is not displaying them
    populate = pyqtSignal()
    populationFinished = pyqtSignal()
    details_fetched = pyqtSignal(str, dict)
    installed = pyqtSignal()
    def __init__(self, parent=None, config: dict = {}):
        super().__init__(parent)
        self.config = config
        self.installerThread = None
        self.indexes_which_are_installed = []
        self.sortedMatches = []
        self.sortedMatches_with_install = []
        self.allLibraries = []
        self.python_exec = ""
        self.setStyleSheet(
            self.config.get('stylesheet', {}).get('tooltip','')
        )
        self.API_ENDPOINT: str = (
            self.config.get('api', {}).get('pypi', {}).get('libraryDetails', 'https://pypi.org/pypi/{package}/json')
        )
        # Setup all the UI Components
        self._setup_ui()

        # Setup timers and signals for fetching list of libraries
        self._setup_timers()
        self._setup_signals_for_fetching_libraries()
        self.get_details = None

    def _setup_ui(self):
        # Initialize the main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        self._setup_search_bar()
        self._setup_list_model()

    def set_python_exec(self, path):
        self.python_exec = path

    def _setup_search_bar(self):
        # Set a search bar for searching libraries to install
        self.search_bar = QLineEdit()
        self.search_bar.setFixedHeight(30)
        self.search_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_bar.setObjectName("searchBarInstaller")
        self.search_bar.setPlaceholderText("Search for libraries to install...")
        self.search_bar.textChanged.connect(self.filterList) # ADDED: Connect search bar to filter method
        self.mainLayout.addWidget(self.search_bar)

    def _setup_list_model(self):
        # Using Model/View Architecture
        self.libraryListView = QListView()
        self.libraryListView.setEnabled(True)

        self.libraryListView.setEditTriggers(QListView.EditTrigger.AllEditTriggers)

        self.libraryListView.setContentsMargins(0, 0, 0, 0)
        self.libraryListView.setObjectName("installLibraryListView")
        self.libraryListView.setSpacing(3)
        self.libraryListView.setObjectName("libraryListViewInstaller")
        self.libraryListView.setUniformItemSizes(False)

        # List Model which holds the data for the library list view
        self.sourceModel = LibraryListModel()
        self.libraryListView.setModel(self.sourceModel)
        self.delegate = PyPIitemDelegate(self.config, self.libraryListView)
        self.libraryListView.setItemDelegate(self.delegate)
        # self.libraryListView.setMouseTracking(True)
        # self.sourceModel.modelReset.connect(self.openAllEditors)
        self.mainLayout.addWidget(self.libraryListView)

    def _setup_timers(self):
        # Search Timer
        self.scraperPyPI = PyPiRunner()
        self.searchTimer = QTimer()
        self.searchTimer.setInterval(300)
        self.searchTimer.setSingleShot(True)
        self.searchTimer.timeout.connect(self.filterList)

        self.fetch_details_timer = QTimer()
        self.fetch_details_timer.setInterval(1000)
        self.fetch_details_timer.setSingleShot(True)
        self.fetch_details_timer.timeout.connect(self.fetchDetails)


    def set_status(self, libraries_list: list):
        for library in self.sortedMatches:
            if library in libraries_list:
                try:
                    index = self.sortedMatches.index(library)
                    self.sortedMatches_with_install[index].update({'status': 'installed'})
                    index_of_model = self.sourceModel.name_to_row.get(library, -1)
                    if index_of_model != -1:
                        idx = self.sourceModel.index(index_of_model)
                        self.sourceModel.dataChanged.emit(idx, idx)
                except ValueError:
                    continue
            else:
                index = self.sortedMatches.index(library)
                self.sortedMatches_with_install[index].update({'status': 'install'})
                index_of_model = self.sourceModel.name_to_row.get(library, -1)
                if index_of_model != -1:
                    idx = self.sourceModel.index(index_of_model)
                    self.sourceModel.dataChanged.emit(idx, idx)


    def fetchDetails(self):
        # Fetch details of libraries
        if self.sortedMatches:
            self.get_details = GettingInstallerLibraryDetails(
                self.config.get('paths', {}).get('executables', {}).get('pypiDetailFetcher', {}).get('darwin', "./pypi_detail_fetcher"),
                self.sortedMatches
            )
            self.get_details.finished.connect(self.sourceModel.updateData)
            self.get_details.start()

    def _show_installed_flag(self, return_code, model_index: QModelIndex):

        name_of_library = model_index.data(DataRole).get('name')
        self.installed.emit()
        idx = self.sortedMatches.index(name_of_library)
        if return_code == -1:
            self.sortedMatches_with_install[idx].update({'status': 'failed'})
            self.sourceModel.dataChanged.emit(model_index, model_index)
        else:
            self.sortedMatches_with_install[idx].update({'status': 'installed'})
            self.sourceModel.dataChanged.emit(model_index, model_index)
        self.installerThread = None

    def _install_library(self, model_index: QModelIndex):
        name_of_library = model_index.data(DataRole).get('name')
        idx = self.sortedMatches.index(name_of_library)
        self.sortedMatches_with_install[idx].update({'status': 'installing'})
        self.sourceModel.dataChanged.emit(model_index, model_index)
        self.installerThread = InstallerLibraries(self.python_exec, name_of_library, model_index)
        self.installerThread.finished.connect(self._show_installed_flag)
        self.installerThread.finished.connect(self.installerThread.deleteLater)
        self.installerThread.start()

    def _setup_signals_for_fetching_libraries(self):
        # Threading setup, fetching details of libraries will be in different function
        self.sourceModel.remove_item.connect(lambda item: self.allLibraries.remove(item))
        self.scraperPyPI.listOfLibraries.connect(self.getAllLibraries)
        self.scraperPyPI.startFetching()
        self.delegate.installClicked.connect(self._install_library)


    def getAllLibraries(self, libraries: list):
        self.allLibraries = libraries
        self.search_bar.setPlaceholderText("Search for libraries to install from the {:,} available libraries".format(len(self.allLibraries)))
        self.filterList()

    def openAllEditors(self):
        for row in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(row)
            self.libraryListView.openPersistentEditor(index)

    def filterList(self):
        searchText = self.search_bar.text().lower()
        if not searchText:
            self.sortedMatches = self.allLibraries[:50]
            self.sortedMatches_with_install = [{'name': name, 'status': 'install'} for name in self.sortedMatches]
        else:
            matches = [
                item for item in self.allLibraries
                if searchText in item.lower()
            ]
            self.sortedMatches = sorted(
                matches,
                key=lambda item: item.lower().find(searchText)
            )
            self.sortedMatches = self.sortedMatches[:50]
            self.sortedMatches_with_install = [{'name': name, 'status': 'install'} for name in self.sortedMatches]

        self.populationFinished.emit()
        self.fetch_details_timer.start(1000)
        self.sourceModel.setDataList(self.sortedMatches_with_install)
        self.sourceModel.set_name_to_row()
