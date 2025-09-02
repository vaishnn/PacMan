import sys
import random
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListView, QStyledItemDelegate, QStyle,
    QVBoxLayout, QWidget, QLineEdit, QLabel
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QPen, QFont, QPainter, QMovie
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QEvent, QAbstractListModel, QModelIndex, QVariant, QTimer, QPoint

# --- Mock PyPiRunner to make the example runnable ---
# This class simulates fetching data from the network, with lazy-loading for versions and summaries.
class PyPiRunner(QtCore.QObject):
    listOfLibraries = pyqtSignal(list)
    detailsFetched = pyqtSignal(str, dict) # Emits (library_name, details_dict)

    def __init__(self):
        super().__init__()
        # Initial data has only the name and an idle status
        self.libraries = [
            {"name": "requests", "status": "idle"},
            {"name": "numpy", "status": "idle"},
            {"name": "PyQt6", "status": "idle"},
            {"name": "pandas", "status": "idle"},
            {"name": "matplotlib", "status": "idle"},
            {"name": "scikit-learn", "status": "idle"},
            {"name": "Django", "status": "idle"},
            {"name": "Flask", "status": "idle"},
        ]
        # This data (version, summary, etc.) would come from separate, later API calls
        self.details_to_fetch = {
            "requests": {"version": "2.28.1", "summary": "Python HTTP for Humans."},
            "numpy": {"version": "1.23.3", "summary": "The fundamental package for scientific computing with Python."},
            "PyQt6": {"version": "6.7.0", "summary": "Python bindings for the Qt cross-platform application framework"},
            "pandas": {"version": "1.5.0", "summary": "Powerful data structures for data analysis, time series, and statistics"},
            "matplotlib": {"version": "3.6.0", "summary": "Python plotting package"},
            "scikit-learn": {"version": "1.1.2", "summary": "A set of python modules for machine learning and data mining"},
            "Django": {"version": "4.1.1", "summary": "A high-level Python web framework that encourages rapid development."},
            "Flask": {"version": "2.2.2", "summary": "A lightweight WSGI web application framework."},
        }

    def startFetching(self):
        # First, emit the main list with only names after a short delay
        QTimer.singleShot(1000, lambda: self.listOfLibraries.emit(self.libraries))

        # Second, start emitting detailed updates one by one to simulate lazy loading
        delay = 1500 # Start fetching after 1.5s
        for name, details in self.details_to_fetch.items():
            # Use a lambda with default arguments to capture the current name and details
            QTimer.singleShot(delay, lambda n=name, d=details: self.detailsFetched.emit(n, d))
            delay += 200 # Stagger the API responses


DataRole = Qt.ItemDataRole.UserRole + 1

# --- Custom Delegate (Combined and Corrected) ---
class PyPIitemDelegate(QStyledItemDelegate):
    installClicked = pyqtSignal(QModelIndex)
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define fonts and colors for consistent styling
        self.font_name = QFont("Inter", 14, QFont.Weight.Medium)
        self.font_version = QFont("Inter", 13)
        self.font_icon = QFont("Inter", 20)
        self.color_text = QColor("#E0E0E0")
        self.color_version = QColor("#9E9E9E")
        self.color_background_hover = QColor("#424242")

        # --- Status-specific colors and icons ---
        self.status_icons = {
            "idle": "+",
            "installing": "⟳",
            "success": "✓",
            "failed": "✗"
        }
        self.status_colors = {
            "idle": QColor("#4CAF50"), # Green
            "idle_hover": QColor("#81C784"),
            "installing": QColor("#2196F3"), # Blue
            "success": QColor("#66BB6A"), # Light Green
            "failed": QColor("#EF5350") # Red
        }

        self._hovered_index = None

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect

        # Draw background hover effect
        if option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, self.color_background_hover)
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

        # --- Item Layout ---
        padding = 15
        install_area_width = 50
        install_rect = QRect(rect.right() - install_area_width, rect.top(), install_area_width, rect.height())
        version_rect = QRect(install_rect.left() - 100, rect.top(), 100, rect.height())
        name_rect = QRect(rect.left() + padding, rect.top(), version_rect.left() - (rect.left() + padding), rect.height())

        # --- Draw Elements ---
        # 1. Draw Library Name
        painter.setFont(self.font_name)
        painter.setPen(self.color_text)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, itemData.get('name', ''))

        # 2. Draw Version
        painter.setFont(self.font_version)
        painter.setPen(self.color_version)
        version_text = itemData.get('version', '...')
        painter.drawText(version_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, version_text)

        # 3. Draw Install Icon based on status
        status = itemData.get('status', 'idle')
        icon_text = self.status_icons.get(status, '?')
        icon_color = self.status_colors.get(status, QColor("white"))

        mouse_pos = option.widget.mapFromGlobal(option.widget.cursor().pos()) if option.widget else QPoint(-1, -1)
        is_hovering_install = install_rect.contains(mouse_pos)

        painter.setFont(self.font_icon)
        if status == 'idle' and is_hovering_install:
            painter.setPen(self.status_colors["idle_hover"])
        else:
            painter.setPen(icon_color)

        if status == 'installing':
            # Simple animation for the installing icon
            painter.translate(install_rect.center())
            painter.rotate((QtCore.QTime.currentTime().msecsSinceStartOfDay() / 10) % 360)
            painter.translate(-install_rect.center())

        painter.drawText(install_rect, Qt.AlignmentFlag.AlignCenter, icon_text)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 55)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseMove:
            if option.widget:
                option.widget.update(index)

        itemData = index.data(DataRole)
        # Only allow clicks if the status is 'idle'
        if itemData and itemData.get('status') == 'idle':
            if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                install_rect = QRect(option.rect.right() - 50, option.rect.top(), 50, option.rect.height())
                if install_rect.contains(event.pos()):
                    self.installClicked.emit(index)
                    return True
        return super().editorEvent(event, model, option, index)

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
        if role == Qt.ItemDataRole.ToolTipRole:
            summary = row_item.get('summary', '')
            status = row_item.get('status', 'idle').capitalize()
            if summary:
                return f"{summary}\nStatus: {status}"
            return f"Status: {status}"

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return super().flags(index)

    def setDataList(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateLibraryData(self, name: str, data_dict: dict):
        """Finds a library by name and updates its data."""
        for i, item_data in enumerate(self._data):
            if item_data.get('name') == name:
                self._data[i].update(data_dict)
                index = self.index(i)
                self.dataChanged.emit(index, index)
                break

class Installer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.allLibraries = []
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search for libraries to install...")
        self.mainLayout.addWidget(self.searchBar)

        self.statusLabel = QLabel("Fetching library list from PyPI...")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addWidget(self.statusLabel)

        self.libraryListView = QListView()
        self.libraryListView.setMouseTracking(True)
        self.libraryListView.setSpacing(0)
        self.libraryListView.setUniformItemSizes(True)

        self.sourceModel = LibraryListModel()
        self.libraryListView.setModel(self.sourceModel)

        self.delegate = PyPIitemDelegate(self.libraryListView)
        self.libraryListView.setItemDelegate(self.delegate)
        self.mainLayout.addWidget(self.libraryListView)
        self.libraryListView.hide()

        # Timer to animate the 'installing' icon
        self.animationTimer = QTimer(self)
        self.animationTimer.timeout.connect(self.libraryListView.update)
        self.animationTimer.start(30) # Update roughly 30 times per second

        self.searchTimer = QTimer(self)
        self.searchTimer.setInterval(300)
        self.searchTimer.setSingleShot(True)

        # --- Connections ---
        self.searchTimer.timeout.connect(self.filterList)
        self.searchBar.textChanged.connect(self.searchTimer.start)
        self.delegate.installClicked.connect(self.install_library)

        self.scraperPyPI = PyPiRunner()
        self.scraperPyPI.listOfLibraries.connect(self.getAllLibraries)
        self.scraperPyPI.detailsFetched.connect(self.sourceModel.updateLibraryData)
        self.scraperPyPI.startFetching()

    def getAllLibraries(self, libraries: list):
        self.allLibraries = libraries
        self.statusLabel.hide()
        self.libraryListView.show()
        self.filterList()

    def filterList(self):
        searchText = self.searchBar.text().lower()
        matches = [item for item in self.allLibraries if not searchText or searchText in item['name'].lower()]
        self.sourceModel.setDataList(matches[:50])

    def install_library(self, index):
        lib_data = index.data(DataRole)
        name = lib_data.get('name')
        if not name: return

        print(f"Starting install for: {name}")
        # 1. Update status to 'installing'
        self.sourceModel.updateLibraryData(name, {"status": "installing"})

        # 2. Simulate installation process (2 seconds)
        def on_install_finished():
            # 3. Randomly decide success or failure
            if random.choice([True, False]):
                print(f"Success: {name}")
                self.sourceModel.updateLibraryData(name, {"status": "success"})
            else:
                print(f"Failed: {name}")
                self.sourceModel.updateLibraryData(name, {"status": "failed"})

        QTimer.singleShot(2000, on_install_finished)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Library Installer")
        self.setGeometry(100, 100, 700, 600)
        self.installer_widget = Installer()
        self.setCentralWidget(self.installer_widget)
        self.apply_stylesheet()

    def apply_stylesheet(self):
        # Stylesheet remains the same as previous version
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #212121; }
            QLineEdit { background-color: #2c2c2c; border: 1px solid #555; border-radius: 5px; padding: 10px; color: #E0E0E0; font-family: Inter; font-size: 14px; margin: 10px; }
            QLabel { color: #9E9E9E; font-family: Inter; font-size: 14px; }
            QListView { background-color: #2c2c2c; border: none; color: #E0E0E0; }
            QListView::item { border-bottom: 1px solid #3a3a3a; }
            QScrollBar:vertical { border: none; background: #2c2c2c; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #555; min-height: 20px; border-radius: 5px; }
            QToolTip { color: #E0E0E0; background-color: #333333; border: 1px solid #555; border-radius: 4px; padding: 5px; font-family: Inter; font-size: 13px; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
