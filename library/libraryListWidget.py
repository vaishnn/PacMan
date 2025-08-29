from PyQt6.QtWidgets import QLineEdit, QMessageBox, QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QLabel, QListWidgetItem, QPushButton
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtWidgets import QSizePolicy
from library.toolTipLibrary import getLibraryDetails
from library.deleteLibrary import uninstallManager
from PyQt6.QtGui import QIcon

# import qtawesome as qta
# Implementation to be DONE of Better Layout and After Changing virtual Path it doesn't shows the Library Details


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

    def __init__(self, colorScheme):
        # I am only adding comments cause this code looks ugly
        super().__init__()
        self.toolTipCache = {}
        self.setObjectName("library")
        self.setStyleSheet(colorScheme)

        # Setting up Tooltip Fetching
        self.getLibraryDetails = getLibraryDetails()
        self.getLibraryDetails.detailsWithName.connect(
            self.getLibraryDetailsThroughClass)

        # Setting up Uninstall Manager
        self.uninstallManager = uninstallManager()
        self.uninstallManager.uninstallFinished.connect(
            self.onUninstallFinished)

        self.pythonExecPath = ""
        # For Main layout of the Library
        self.libraryLayoutWithSearch = QVBoxLayout(self)
        self.libraryLayoutWithSearch.setContentsMargins(5, 2, 2, 2)
        self.libraryLayoutWithSearch.setSpacing(0)

        # Search Bar
        self.searchBar = QLineEdit()
        self.searchBar.hide()
        self.searchBar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.searchBar.setFixedHeight(30)
        self.searchBar.setPlaceholderText("Search for libraries")
        self.searchBar.setText("")
        self.searchBar.setObjectName("searchBarInLibraryListWidget")
        self.searchBar.textChanged.connect(self.sortItemsList)
        # self.searchBar.textChanged.connect(self.ifTypingIsStillGoingOn)

        # Timer for assigning a thread to tooltip
        self.searchBarTypingTimer = QTimer()

        # This require some fixing, I dont Know How but it does

        # self.searchBarTypingTimer.setInterval(300)
        # self.searchBarTypingTimer.setSingleShot(True)
        self.searchBarTypingTimer.timeout.connect(
            self.whenTimerForToolTipIsFinished)

        self.libraryLayoutWithSearch.addWidget(self.searchBar)

        # For library layout underneath search bar
        self.libraryLayout = QVBoxLayout()
        self.libraryLayoutWithSearch.addLayout(self.libraryLayout)
        self.libraryLayout.setContentsMargins(0, 10, 0, 0)
        # self.libraryLayout.setSpacing(0)
        # This is for mapping Library Item names with their respective widgets
        self.itemMap = {}

        self.libraryList = QListWidget()
        self.libraryList.setObjectName("libraryList")
        # self.libraryList.setResizeMode(QListView.ResizeMode.Adjust)
        self.libraryLayout.addWidget(self.libraryList)
        self.listLibraryRefreshed.connect(self.startAllTooltipFetches)

    def whenTimerForToolTipIsFinished(self):
        self.listLibraryRefreshed.emit()

    def setPythonExecPath(self, path):
        self.pythonExecPath = path

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
            if item["tag"] == "installed":
                tagLibraryPanel = QLabel("I")
            else:
                tagLibraryPanel = QLabel("D")
            tagLibraryPanel.setFixedWidth(25)
            tagLibraryPanel.setObjectName("tagLibraryPanel")

            # Changing Properties of QLabels
            uninstallButton = QPushButton()
            uninstallButton.setFixedSize(30, 30)
            uninstallButton.setObjectName("deleteButtonFromLibraryListWidget")
            uninstallButton.setIcon(QIcon("icons/delete.png"))

            # Adding Widget in proper Order
            listWidgetLayout.addWidget(tagLibraryPanel)
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
            # self.getLibraryDetails.fetchDetailLibraryDetails(item["name"])
        if emit:
            self.listLibraryRefreshed.emit()
        else:
            self.searchBarTypingTimer.start(100)

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
            print(packageName)
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
            tooltip = f"""
            <p>
            <b>Summary:</b> {libraryDetails["Summary"]} <br>
            <b>Author:</b> {libraryDetails['Author']} <br>
            <b>Requires:</b> {libraryDetails['Requires']} <br>
            <b>Required-by:</b> {libraryDetails['Required-by']}
            </p>"""
            listItem[0].setToolTip(tooltip)
            self.toolTipCache[name] = tooltip

    def closeEvent(self, event):  # type: ignore
        self.getLibraryDetails.stop()
        self.uninstallManager.stop()
        super().closeEvent(event)
