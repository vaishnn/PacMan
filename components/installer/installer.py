import json
import subprocess
from PyQt6 import QtCore
from PyQt6.QtCore import QAbstractListModel, QEvent, QModelIndex, QPoint, QRect, QSize, QThread, QTimer, QVariant, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QLineEdit, QListView,  QSizePolicy, QStyle,  QStyledItemDelegate, QVBoxLayout, QWidget
from Qt.CustomToolTip import InteractiveToolTip
from components.installer.pypi import PyPiRunner

import datetime
DataRole = Qt.ItemDataRole.UserRole + 1

def format_pypi_tooltip_html(pypi_data, font_family_name):
    """
    Takes a dictionary with PyPI info and formats it into a styled HTML string.
    """
    info = pypi_data.get('info', {})
    if not info:
        return ""

    table_rows = []

    # Core Info
    if info.get('name'):
        table_rows.append(f'<tr><td class="tooltip-label">Name</td><td class="tooltip-value">{info["name"]}</td></tr>')
    if info.get('version'):
        table_rows.append(f'<tr><td class="tooltip-label">Version</td><td class="tooltip-value">{info["version"]}</td></tr>')
    if info.get('summary'):
        table_rows.append(f'<tr><td class="tooltip-label">Summary</td><td class="tooltip-value">{info["summary"].strip()}</td></tr>')

    # People (Author & Maintainer)
    author = info.get('author')
    author_email = info.get('author_email')
    author_str = ""
    if author:
        author_str = author
        if author_email:
            author_str += f" &lt;{author_email}&gt;" # Use HTML entities for < >
        table_rows.append(f'<tr><td class="tooltip-label">Author</td><td class="tooltip-value">{author_str}</td></tr>')

    maintainer = info.get('maintainer')
    maintainer_email = info.get('maintainer_email')
    maintainer_str = ""
    if maintainer:
        maintainer_str = maintainer
        if maintainer_email:
            maintainer_str += f" &lt;{maintainer_email}&gt;"
        # Only show maintainer if they are different from the author
        if maintainer_str and maintainer_str != author_str:
            table_rows.append(f'<tr><td class="tooltip-label">Maintainer</td><td class="tooltip-value">{maintainer_str}</td></tr>')

    # Requirements
    if info.get('requires_python'):
        table_rows.append(f'<tr><td class="tooltip-label">Requires Python</td><td class="tooltip-value">{info["requires_python"]}</td></tr>')
    if info.get('requires_dist'):
        deps_html = "<br>".join(info['requires_dist'])
        table_rows.append(f'<tr><td class="tooltip-label">Dependencies</td><td class="tooltip-value">{deps_html}</td></tr>')

    # License Info (Always shows License field)
    license_val = info.get('license') if info.get('license') else "<span class='tooltip-placeholder'>Not Provided</span>"
    table_rows.append(f'<tr><td class="tooltip-label">License</td><td class="tooltip-value">{license_val}</td></tr>')
    if info.get('license_file'):
        table_rows.append(f'<tr><td class="tooltip-label">License File</td><td class="tooltip-value">{info["license_file"]}</td></tr>')

    # Links, Keywords, and Details
    if info.get('project_url'):
        url = info['project_url']
        link_html = f'<a href="{url}" style="color: #8ab4f8;">{url}</a>'
        table_rows.append(f'<tr><td class="tooltip-label">Project URL</td><td class="tooltip-value">{link_html}</td></tr>')
    if info.get('keywords'):
        table_rows.append(f'<tr><td class="tooltip-label">Keywords</td><td class="tooltip-value">{info["keywords"]}</td></tr>')
    if info.get('provides_extra'):
        provides_html = "<br>".join(info['provides_extra'])
        table_rows.append(f'<tr><td class="tooltip-label">Provides</td><td class="tooltip-value">{provides_html}</td></tr>')
    if info.get('classifiers'):
        classifiers_html = "<br>".join(info['classifiers'])
        table_rows.append(f'<tr><td class="tooltip-label">Classifiers</td><td class="tooltip-value">{classifiers_html}</td></tr>')

    all_rows_html = "\n".join(table_rows)

    # --- Handle special top/bottom sections ---

    # Create a prominent warning if the package is yanked
    yanked_html = ""
    if info.get('yanked'):
        reason = info.get('yanked_reason') or "No reason provided."
        yanked_html = f"""
        <div class="yanked-warning">
            <strong>Warning: This version has been yanked.</strong>
            <br><span class="yanked-reason">Reason: {reason}</span>
        </div>
        """

    # Create a footer for the fetch timestamp
    footer_html = ""
    if pypi_data.get('fetched_at'):
        try:
            # Parse ISO 8601 timestamp and format it nicely
            dt_obj = datetime.datetime.fromisoformat(pypi_data['fetched_at'].replace('Z', '+00:00'))
            # Format to something like "16 Sep 2025, 03:07 PM IST"
            dt_obj = dt_obj.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=30))) # Convert to IST
            fetched_at_str = dt_obj.strftime('%d %b %Y, %I:%M %p %Z')
            footer_html = f'<div class="tooltip-footer">Cached: {fetched_at_str}</div>'
        except (ValueError, TypeError):
            pass # Ignore if timestamp is invalid

    # --- Assemble final HTML ---
    return f"""
    <style>
        .tooltip-container {{ font-family: '{font_family_name}', sans-serif; font-size: 14px; max-width: 550px; line-height: 1.5; }}
        .tooltip-table {{ border-spacing: 0; width: 100%; }}
        .tooltip-table td {{ padding: 2px 8px; vertical-align: top; }}
        .tooltip-label {{ font-weight: 600; white-space: nowrap; text-align: left; padding-right: 12px; color: #999999; }}
        .tooltip-value {{ color: #FFFFFF; word-break: break-word; }}
        .tooltip-placeholder {{ color: #777777; font-style: italic; }}
        a {{ text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .yanked-warning {{ background-color: #5c1b16; color: #f8d7da; padding: 8px; border-radius: 4px; margin-bottom: 10px; border: 1px solid #c93a3a; }}
        .yanked-reason {{ color: #f5c6cb; }}
        .tooltip-footer {{ font-size: 11px; color: #777777; text-align: right; padding-top: 8px; border-top: 1px solid #333333; margin-top: 8px; }}
    </style>
    <div class="tooltip-container">
        {yanked_html}
        <table class="tooltip-table">
            {all_rows_html}
        </table>
        {footer_html}
    </div>
    """

class GettingInstallerLibraryDetails(QThread):
    """
    A QThread subclass that fetches details for a list of Python libraries
    using an external Go executable.

    It executes the Go program with the provided list of libraries, captures
    its JSON output, and emits the parsed dictionary result via the
    `finished` signal.
    """
    finished = pyqtSignal(dict)
    def __init__(self, go_executable, list_of_libraries, parent=None):
        super().__init__(parent)
        self.go_executable = go_executable
        self.list_of_libraries = list_of_libraries

    def run(self):
        if self.list_of_libraries:
            result = subprocess.run([self.go_executable, *self.list_of_libraries], capture_output=True, text=True)
            if result.stderr:
                print(result.stderr)
                self.finished.emit({})
            else:
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        self.finished.emit(data)
                except Exception as e:
                    self.finished.emit({})
                    print(e)
                    print(result.stdout)
        else:
            self.finished.emit({})



class InstallerLibraries(QThread):
    """
    A QThread subclass for installing a single Python library using pip
    in a separate background thread.

    It executes the 'pip install' command with the specified Python executable
    and library name, capturing the output and emitting a signal upon completion
    indicating success or failure.
    """
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
    """
    A custom QStyledItemDelegate for rendering PyPI package items in a QListView.

    This delegate provides a rich, interactive user interface for each library
    item. It customizes the painting to display the library's name, version,
    and an install status icon. It also handles mouse events to provide hover
    effects, show detailed tooltips with package information, and detect clicks
    on the install icon to trigger an installation process.

    Signals:
        installClicked (QModelIndex): Emitted when the user clicks the install icon for an item.
    """
    installClicked = pyqtSignal(QModelIndex)
    def __init__(self, config: dict, parent = None):
        super().__init__(parent)
        self.config = config


        self.tooltip = InteractiveToolTip(parent)
        self.tooltip.set_object_name("PyPIitemDelegateTooltip")
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

    def helpEvent(self, event, view, option, index) -> bool:

        if event.type() == QEvent.Type.ToolTip: #type: ignore
            # Get the full data dictionary from the model
            item_data = index.data(DataRole)
            print(item_data)
            if not item_data or 'description' not in item_data:
                self.tooltip.hide()
                return True

            if item_data:
                target = view.viewport() #type: ignore
                self.tooltip.set_content(item_data['description'])
                self.tooltip.adjustSize()
                self.tooltip.schedule_show(item_data['description'], event.globalPos() + QPoint(15, 15), target) #type: ignore
                # Position tooltip slightly offset from cursor
                # self.tooltip.move(event.globalPos() + QPoint(15, 15)) #type: ignore
                # self.tooltip.show()
                return True

        self.tooltip.hide()

        return super().helpEvent(event, view, option, index)

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
        """
        Draws a pixmap tinted with a specified color, optionally with a background.
        It uses the pixmap's mask to apply the color, making it appear as a colored icon.
        """
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
    """
    A custom QAbstractListModel for managing and presenting PyPI library data
    to a QListView.

    This model stores a list of dictionaries, where each dictionary represents
    a PyPI package and can include details like 'name', 'version', 'status'
    (e.g., 'install', 'installed', 'installing', 'failed'), and a 'description'
    (which is pre-formatted HTML for a tooltip).

    It provides data for display and custom roles, handles updates to library
    details fetched from an external source, and signals when items are removed.

    Signals:
        remove_item (str): Emitted with the name of the library that has been removed from the model (e.g., if its version is "UNKNOWN").
    """
    remove_item = pyqtSignal(str)

    def __init__(self, data = None, parent = None):
        super().__init__(parent)
        self._data = data if data else []

    def set_name_to_row(self):
        self.name_to_row = {data['name']: i for i, data in enumerate(self._data)}

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
        # if role == Qt.ItemDataRole.ToolTipRole:
        #     description = row_item.get('description', '').strip()
        #     if row_item.get('status') == "installing":
        #         return description + "\nInstalling..."
        #     return description

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return  (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled)

    def setDataList(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateData(self, data_dict: dict):
        # When the API has emitted some data related to the library
        _data = self._data.copy()
        for _, (item, item_data) in enumerate(data_dict.items()):
            index_number = self.name_to_row[item]
            tootlip = format_pypi_tooltip_html(item_data, 'figtree')
            if item_data.get('info').get('version', "UNKNOWW") == "UNKNOWN":
                self._data.pop(index_number)
                self.remove_item.emit(item)
                continue
            self._data[index_number].update({'description': tootlip})
            self._data[index_number].update({'version': item_data['info']['version']})
            idx = self.index(index_number, 0, QModelIndex())
            self.dataChanged.emit(idx, idx)


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
            self.get_details = GettingInstallerLibraryDetails('./library_details', self.sortedMatches)
            self.get_details.finished.connect(self.sourceModel.updateData)
            self.get_details.start()

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
        self.sourceModel.set_name_to_row()
