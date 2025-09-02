from PyQt6 import QtCore
from PyQt6.QtCore import QAbstractListModel, QEvent, QModelIndex, QRect, QSize, QTimer, QVariant, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QListView, QPushButton, QSizePolicy, QStyle, QStyleOptionButton, QStyledItemDelegate, QVBoxLayout, QWidget
from Installer.pypi import PyPiRunner

DataRole = Qt.ItemDataRole.UserRole + 1

class PyPIitemDelegate(QStyledItemDelegate):
    installClicked = pyqtSignal(QModelIndex)
    def __init__(self, parent = None):
        super().__init__(parent)
        self._pressedIndex = QModelIndex()
        self.colorInstall = QColor(128, 128, 128)
        self.installPixmap = QPixmap("icons/download.png")
        self.padding = 10

    def paint(self, painter, option, index):
        # Let the base class handle background colors for selection, hover, etc.
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect

        itemData = index.data(DataRole)
        if not itemData:
            painter.restore()
            return

        buttonSize = 16
        buttonRect = QRect(
            rect.right() - buttonSize - self.padding,
            rect.center().y() - buttonSize // 2,
            buttonSize,
            buttonSize
        )
        painter.drawPixmap(buttonRect, self.installPixmap)
        # self._drawColoredPixmap(painter, buttonRect, self.installPixmap, self.colorInstall)
        # isHovered = (index == self._pressedIndex)
        # if isHovered:
        #     self._drawColoredPixmap(painter, buttonRect, self.installPixmap, self.colorInstall)
        # else:
        #     self._drawColoredPixmap(painter, buttonRect, self.installPixmap, self.colorInstall)

        versionRect = QRect(rect.left() + buttonSize + 10, rect.top(), rect.width() - buttonSize - 20, rect.height())
        versionText = itemData.get('version', "")
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(versionRect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, versionText)

        libraryName = itemData.get('name', "")
        libraryRect = QRect(
            rect.left() + buttonSize + 10, rect.top(), rect.width() - buttonSize - 20, rect.height()
        )
        painter.drawText(libraryRect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, libraryName)
        painter.restore()

    def _getButtonRect(self, options) -> QRect:
        return QRect(
            options.rect.center().x() - 10,
            options.rect.center().y() - 10,
            21, 21
        )

    def updateEditorGeometry(self, editor, option, index) -> None:
        return super().updateEditorGeometry(editor, option, index)

    def editorEvent(self, event, model, option, index: QtCore.QModelIndex) -> bool:
        self._pressedIndex = QModelIndex()
        if event.type() not in ( #type: ignore
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease):
                return super().editorEvent(event, model, option, index)

        buttonRect = self._getButtonRect(option)

        if event.type() == QEvent.Type.MouseButtonPress: #type: ignore
            if buttonRect.contains(event.pos()): #type: ignore
                self._pressedIndex = index.row()
                model.dataChanged.emit(index, index, (Qt.ItemDataRole.DisplayRole,)) #type: ignore
                return True

        elif event.type() == QEvent.Type.MouseButtonRelease: #type: ignore
            if buttonRect.contains(event.pos()) and index == self._pressedIndex: #type: ignore
                self.installClicked.emit(index)

            model.dataChanged.emit(index, index, (Qt.ItemDataRole.DisplayRole,)) #type: ignore

        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        # Use of item Hint, it's more than just a hint
        return QSize(0, 55)

    def _drawColoredPixmap(self, painter, rect, pixmap, color):
        mask = pixmap.createMaskFromColor(Qt.GlobalColor.transparent, Qt.MaskMode.MaskOutColor)
        painter.save()
        painter.setPen(color)
        painter.drawPixmap(rect, mask)
        painter.restore()
    # def sizeHint(self, option, index):
    #     return QSize(0, 30)

class LibraryListModel(QAbstractListModel):
    def __init__(self, data = None, parent = None):
        super().__init__(parent)
        self._data = data if data else []

    def rowCount(self, parent = None):
        return len(self._data)

    def data(self, index, role = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return QVariant()

        row_item = self._data[index.row()]
        if role == DataRole:
            return row_item
        if role == Qt.ItemDataRole.DisplayRole:
            return row_item.get('name', '')

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setDataList(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

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
        self.libraryListView.setContentsMargins(0, 0, 0, 0)
        self.libraryListView.setObjectName("installLibraryListView")
        self.libraryListView.setSpacing(3)
        self.libraryListView.setObjectName("libraryListViewInstaller")
        self.libraryListView.setUniformItemSizes(False)


        self.sourceModel = LibraryListModel()
        self.libraryListView.setModel(self.sourceModel)
        self.delegate = PyPIitemDelegate(self.libraryListView)
        self.libraryListView.setItemDelegate(self.delegate)

        self.libraryListView.setMouseTracking(True)
        # self.sourceModel.modelReset.connect(self.openAllEditors)
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
        self.sourceModel.setDataList(initialChunk)

    def openAllEditors(self):
        for row in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(row)
            self.libraryListView.openPersistentEditor(index)

    def filterList(self):
        searchText = self.searchBar.text().lower()
        if not searchText:
            sortedMatches = self.allLibraries[:50]
        else:
            matches = [
                item for item in self.allLibraries
                if searchText in item['name'].lower()
            ]
            sortedMatches = sorted(
                matches,
                key=lambda item: item['name'].lower().find(searchText)
            )
            sortedMatches = sortedMatches[:50]
        self.sourceModel.setDataList(sortedMatches)
