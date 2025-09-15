import subprocess
from PyQt6 import QtCore
from PyQt6.QtCore import QAbstractListModel, QEvent, QModelIndex, QPoint, QRect, QSize, QThread, QTimer, QVariant, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QLineEdit, QListView,  QSizePolicy, QStyle,  QStyledItemDelegate, QVBoxLayout, QWidget
from installer.pypi import PyPiRunner
from installer.request_pypi import RequestDetails

DataRole = Qt.ItemDataRole.UserRole + 1

class InstallerLibraries(QThread):
    finished = pyqtSignal(int, QModelIndex)
    def __init__(self ,python_exec_path, library_name, model_index: QModelIndex) -> None:
        super().__init__()
        self.python_exec_path = python_exec_path
        self.library_name = library_name
        self.model_index = model_index

    def run(self):
        try:
            # subprocess.run is a blocking call, which is now safely in the background
            result = subprocess.run(
                [self.python_exec_path, "-m", "pip", "install", self.library_name],
                capture_output=True,
                text=True,
                check=False # Don't raise an exception on non-zero exit codes
            )

            print("---STDOUT---")
            print(result.stdout)
            print("---STDERR---")
            print(result.stderr)

            if result.returncode == 0:
                self.finished.emit(1, self.model_index)
            else:
                self.finished.emit(-1, self.model_index)

        except Exception as e:
            print(f"An exception occurred: {e}")
            self.finished.emit(-1, self.model_index) # Use -1 for exceptions

class PyPIitemDelegate(QStyledItemDelegate):
    installClicked = pyqtSignal(QModelIndex)
    def __init__(self, config: dict, parent = None):
        super().__init__(parent)
        self.config = config
        self._pressedIndex = QModelIndex()
        self.color_hover = QColor(self.config.get('ui', {}).get(
            "colors", {}).get("background", {}).get("hover", QColor(255, 255, 255))
        )
        self.text_color = QColor(
            self.config.get('ui', {}).get("colors", {}).get("text", {}).get("normal", QColor(0, 0, 0))
        )
        self.color_muted = QColor(
            self.config.get('ui', {}).get("colors", {}).get("text", {}).get("muted", QColor(128, 128, 128))
        )
        self.button_color = QColor(
            self.config.get('ui', {}).get("colors", {}).get("button", {}).get("install", QColor(0, 128, 255))
        )
        self.button_color_hover = QColor(
            self.config.get('ui', {}).get("colors", {}).get("button", {}).get("primaryHover", QColor(0, 128, 255))
        )
        self.installPixmap = QPixmap("icons/download.png")
        self.padding = 10
        self._hovered_index = None
        self.roundedCornersRadius = self.config.get("ui", {}).get(
            "window", {}).get("installer", {}).get('roundedCornerRadius', 8)

    def paint(self, painter: QPainter, option, index): #type: ignore
        # Let the base class handle background colors for selection, hover, etc.
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect
        path = QPainterPath()
        path.addRoundedRect(rect.toRectF(), self.roundedCornersRadius, self.roundedCornersRadius)

        # Draw the hover effect
        if option.state & QStyle.StateFlag.State_MouseOver:
            # painter.fillRect(rect, self.color_hover)
            painter.fillPath(path, self.color_hover)
            if self._hovered_index != index:
                self._hovered_index = index

                if option.widget:
                    option.widget.update()
        else:
            if self._hovered_index == index:
                self._hovered_index = None



        itemData = index.data(DataRole)
        if not itemData:
            painter.restore()
            return

        # Item layout
        padding = 15
        padding_for_button = 15
        button_width = 20
        version_height = 20
        name_height = 20


        install_rect = QRect(
            rect.right() - button_width - padding_for_button,
            rect.top() + padding_for_button,
            button_width,
            button_width
        )
        version_rect = QRect(
            rect.center().x(),
            rect.top() + padding,
            int(rect.width()/2) - install_rect.width(),
            version_height
        )
        name_rect = QRect(
            rect.left() + padding,
            rect.top() + padding,
            rect.width() - padding - version_rect.width(),
            name_height
        )
        oldfont = painter.font()
        font = painter.font()
        font.setItalic(True)
        painter.setFont(font)

        versionText = itemData.get('version', "...")
        # painter.setPen(self.color_muted)
        painter.setPen(self.color_muted)
        painter.drawText(version_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, versionText)

        painter.setFont(oldfont)
        libraryName = itemData.get('name', "")
        painter.setPen(self.text_color)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, libraryName)
        painter.restore()

        status_install = itemData.get("status", "install")
        mouse_pos = option.widget.mapFromGlobal(
            option.widget.cursor().pos()) if option.widget else QPoint(-1, -1)
        is_hovering_install = install_rect.contains(mouse_pos)

        if status_install == "install" :
            if is_hovering_install :
                self._drawColoredPixmap(painter, install_rect, QPixmap(
                    self.config.get("paths", {}).get("assets", {}).get("images", {}).get("install", "")
                ), self.button_color, "#929292")
            else:
                self._drawColoredPixmap(painter, install_rect, QPixmap(
                    self.config.get("paths", {}).get("assets", {}).get("images", {}).get("install", "")
                ), self.button_color)
        elif status_install == "installed":
            self._drawColoredPixmap(painter, install_rect, QPixmap(
                self.config.get("paths", {}).get("assets", {}).get("images", {}).get("installed", "")
            ), self.button_color)
        elif status_install == "installing":
            self._drawColoredPixmap(painter, install_rect, QPixmap(
                self.config.get("paths", {}).get("assets", {}).get("images", {}).get("installing", "")
            ), self.button_color)
        elif status_install == "failed":
            self._drawColoredPixmap(painter, install_rect, QPixmap(
                self.config.get("paths", {}).get("assets", {}).get("images", {}).get("failed", "")
            ), self.button_color)


    def updateEditorGeometry(self, editor, option, index) -> None:
        return super().updateEditorGeometry(editor, option, index)

    def editorEvent(self, event, model, option, index: QtCore.QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseMove: # type: ignore
            if option.widget:
                option.widget.update(index) # type: ignore

        itemData = index.data(DataRole)
        if itemData and itemData.get("status", "install") == "install":
            if event.type() == QEvent.Type.MouseButtonRelease: # type: ignore
                padding = 10
                button_width = 30
                install_rect = QRect(
                    option.rect.right() - button_width - padding,
                    option.rect.top() + padding,
                    button_width,
                    button_width
                )

                if install_rect.contains(event.pos()): # type: ignore

                    self.installClicked.emit(index)
                    return True
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        # Use of item Hint, it's more than just a hint
        return QSize(0, 55)

    def _drawColoredPixmap(self, painter, rect: QRect, pixmap: QPixmap, color, bg_color = "", mask_color: QColor = QColor(Qt.GlobalColor.transparent)):
        mask = pixmap.createMaskFromColor(QColor(Qt.GlobalColor.transparent))
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(
            QRect(
                rect.x() - 5,
                rect.y() - 5,
                rect.width() + 10,
                rect.height() + 10
            ).toRectF(),
            self.roundedCornersRadius, self.roundedCornersRadius
        )
        if bg_color != "":
            painter.fillPath(path, QColor(bg_color))
        painter.setPen(color)
        painter.drawPixmap(rect, mask)
        painter.restore()

class LibraryListModel(QAbstractListModel):

    remove_item = pyqtSignal(str)
    def __init__(self, data = None, parent = None):
        super().__init__(parent)
        self._data = data if data else []
        self.name_to_row = {data: i for i, data in enumerate(self._data)}

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
        if role == Qt.ItemDataRole.ToolTipRole:
            description = row_item.get('description', '').strip()
            if row_item.get('status') == "installing":
                return description + "\nInstalling..."
            return description

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return  (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled)

    def setDataList(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateData(self, name: str, data_dict: dict):
        # When the API has emitted some data related to the library
        _data = self._data.copy()
        for i, item_data in enumerate(_data):
            if item_data.get('name') == name:
                if not data_dict.get('response') == 200:
                    try:
                        self._data.remove(item_data)
                        self.remove_item.emit(item_data['name'])
                    except ValueError:
                        pass
                else:
                    summary = data_dict.get('summary', '')
                    if not summary :
                        self._data.remove(item_data)
                        self.remove_item.emit(item_data['name'])
                    else:
                        license = data_dict.get('license', '')
                        author = data_dict.get('author', '')
                        requires_python = data_dict.get('requires_python', '')

                        self._data[i].update(
                            {
                                'description': f"""
                                <p style="width:400px">
                                <b>Summary</b>: {summary} <br>
                                <b>License</b>: {license.split('\n')[0].strip() if license else '<em style="color:grey">No License Provided</em>'} <br>
                                <b>Author</b>: {author if author else '<em style="color:grey">No Author Provided</em>'} <br>
                                <b>Requires Python</b>: {requires_python if requires_python else '<em style="color:grey">No Python Version Provided</em>'}
                                </p>
                                """,
                                'version': data_dict.get('version', '')
                            }
                        )
                index = self.index(i)
                self.dataChanged.emit(index, index)
                break

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
        self.searchBar = QLineEdit()
        self.searchBar.setFixedHeight(30)
        self.searchBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.searchBar.setObjectName("searchBarInstaller")
        self.searchBar.setPlaceholderText("Search for libraries to install...")
        self.searchBar.textChanged.connect(self.filterList) # ADDED: Connect search bar to filter method
        self.mainLayout.addWidget(self.searchBar)

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

        # Fetch Details Timer
        self.getDetails = RequestDetails(
            TIMEOUT=self.config.get('controls', {}).get('installer', {}).get('detailsTimeout', 1000)
        )
        self.fetch_details_timer = QTimer()
        self.fetch_details_timer.setInterval(1000)
        self.fetch_details_timer.setSingleShot(True)
        self.fetch_details_timer.timeout.connect(self.fetchDetails)


    def set_status(self, libraries_list: list):
        for library in libraries_list:
            try:
                index = self.sortedMatches.index(library)
                self.sortedMatches_with_install[index].update({'status': 'installed'})
                index_of_model = self.sourceModel.name_to_row.get(library, -1)
                if index_of_model != -1:
                    idx = self.sourceModel.index(index_of_model)
                    self.sourceModel.dataChanged.emit(idx, idx)
            except ValueError:
                continue


    def fetchDetails(self):
        # Fetch details of libraries
        if self.sortedMatches:
            for library in self.sortedMatches:
                self.getDetails.fetch_details(API_ENDPOINT=self.API_ENDPOINT, library=library)

    def _show_installed_flag(self, return_code, model_index: QModelIndex):
        self.installerThread = None
        name_of_library = model_index.data(DataRole).get('name')
        self.installed.emit()
        idx = self.sortedMatches.index(name_of_library)
        if return_code == -1:
            self.sortedMatches_with_install[idx].update({'status': 'failed'})
            self.sourceModel.dataChanged.emit(model_index, model_index)
        else:
            self.sortedMatches_with_install[idx].update({'status': 'installed'})
            self.sourceModel.dataChanged.emit(model_index, model_index)

    def _install_library(self, model_index: QModelIndex):
        name_of_library = model_index.data(DataRole).get('name')
        idx = self.sortedMatches.index(name_of_library)
        self.sortedMatches_with_install[idx].update({'status': 'installing'})
        self.sourceModel.dataChanged.emit(model_index, model_index)
        print(self.python_exec)
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
        self.getDetails.fetchedDetails.connect(self.sourceModel.updateData)


    def getAllLibraries(self, libraries: list):
        self.allLibraries = libraries
        self.searchBar.setPlaceholderText("Search for libraries to install from the {:,} available libraries".format(len(self.allLibraries)))
        self.filterList()

    def openAllEditors(self):
        for row in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(row)
            self.libraryListView.openPersistentEditor(index)

    def filterList(self):
        searchText = self.searchBar.text().lower()
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
