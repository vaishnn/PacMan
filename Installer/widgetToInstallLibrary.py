from PyQt6.QtCore import QAbstractListModel, QSortFilterProxyModel, QStringListModel, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QLineEdit, QListView, QSizePolicy, QVBoxLayout, QWidget
from Installer.pypi import PyPiRunner

class LibraryListModel(QAbstractListModel):
    def __init__(self, data = None, parent = None):
        super().__init__(parent)
        self._data = data if data else []

    def rowCount(self, parent = None):
        return len(self._data)

    def data(self, index, role = Qt.ItemDataRole.DisplayRole):
        pass

class Installer(QWidget):
    """Installer widget for installing libraries"""
    # Current Implementation just brings 30 libraries
    # It is storing all the libraries but it is not displaying them
    populate = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

        # Where the libraries are stored but not all are displayed at same time
        self.allLibraries = []

        # Initialize the main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        # Set a search bar for searching libraries to install
        self.searchBar = QLineEdit()
        self.searchBar.setFixedHeight(30)
        self.searchBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.searchBar.setObjectName("searchBarInstaller")
        self.searchBar.setPlaceholderText("Search for libraries to install...")
        self.searchBar.textChanged.connect(self.filterList) # ADDED: Connect search bar to filter method
        self.mainLayout.addWidget(self.searchBar)

        # Just a label to show loading status, may be a GIF can be better
        self.statusLabel = QLabel("Fetching library list from PyPI...")
        self.mainLayout.addWidget(self.statusLabel)
        self.statusLabel.setObjectName("statusLabelInstaller")

        # Using Model/View Architecture
        self.libraryListView = QListView()
        self.libraryListView.setSpacing(3)
        self.libraryListView.setObjectName("libraryListViewInstaller")
        self.libraryListView.setUniformItemSizes(True)


        self.sourceModel = QStringListModel()

        # Proxy Model
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.sourceModel)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity(False))

        self.libraryListView.setModel(self.proxyModel)
        self.mainLayout.addWidget(self.libraryListView)

        # Search Timer
        self.searchTimer = QTimer()
        self.searchTimer.setInterval(300)
        self.searchTimer.setSingleShot(True)
        self.searchTimer.timeout.connect(self.filterList)

        self.searchBar.textChanged.connect(self.filterList)

        # Threading setup
        self.scraperPyPI = PyPiRunner()
        self.scraperPyPI.listOfLibraries.connect(self.getAllLibraries)
        self.scraperPyPI.startFetching()

    def getAllLibraries(self, libraries: list):
        self.allLibraries = libraries
        self.statusLabel.setText(f"Loaded {len(libraries)} libraries.")
        self.statusLabel.setObjectName("statusLabelInstaller")
        initialChunk = self.allLibraries[:50]
        self.sourceModel.setStringList(initialChunk)

    def filterList(self):
        searchText = self.searchBar.text().lower()
        if not searchText:
            sortedMatches = self.allLibraries[:50]
        else:
            matches = [
                item for item in self.allLibraries
                if searchText in item.lower()
            ]
            sortedMatches = sorted(
                matches,
                key=lambda item: item.lower().find(searchText)
            )
            sortedMatches = sortedMatches[:50]
        self.sourceModel.setStringList(sortedMatches)
