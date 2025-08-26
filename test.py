import sys
import time
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QWidget, QVBoxLayout,
    QPushButton, QLabel, QHBoxLayout, QListWidgetItem
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

# --- WORKER AND CONTROLLER (UNCHANGED, FOR REFERENCE) ---

class Worker(QObject):
    """Simulated worker that takes time to run."""
    finished = pyqtSignal(str, dict)

    @pyqtSlot(str)
    def run(self, package_name):
        print(f"THREAD: Starting fetch for '{package_name}'...")
        # Simulate a slow network/subprocess call
        time.sleep(random.uniform(0.5, 2.0))
        result_data = {
            "Name": package_name.capitalize(),
            "Version": f"{random.randint(1, 5)}.{random.randint(0, 10)}",
            "Timestamp": time.strftime("%H:%M:%S")
        }
        print(f"THREAD: Finished fetch for '{package_name}'.")
        self.finished.emit(package_name, result_data)

class DetailsFetcher(QObject):
    """Controller that manages the worker thread."""
    detailsReady = pyqtSignal(str, dict)
    requestDetails = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.requestDetails.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.thread.start()
        print("--- Worker Thread Started ---")

    @pyqtSlot(str, dict)
    def on_worker_finished(self, name, data):
        self.detailsReady.emit(name, data)

    def fetch(self, name):
        self.requestDetails.emit(name)

    def stop(self):
        print("--- Stopping Worker Thread ---")
        self.thread.quit()
        self.thread.wait()

# --- THE CORRECTED LIBRARY WIDGET ---

class LibraryWidget(QWidget):
    listRefreshed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. CREATE THE FETCHER AND MAP **ONCE**
        self.details_fetcher = DetailsFetcher()
        self.widget_map = {}

        # --- CONNECTIONS ---
        self.details_fetcher.detailsReady.connect(self.update_tooltip)
        self.listRefreshed.connect(self.start_all_tooltip_fetches)

        # --- UI SETUP ---
        self.list_widget = QListWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

    def add_items(self, items):
        # This method ONLY manages the UI list and data map
        print("\nUI: Clearing and repopulating list.")
        self.list_widget.clear()
        self.widget_map.clear()

        for item_data in items:
            package_name = item_data["name"]

            custom_widget = QWidget()
            layout = QHBoxLayout(custom_widget)
            layout.addWidget(QLabel(package_name))
            custom_widget.setToolTip("Awaiting details...")

            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(custom_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, custom_widget)

            self.widget_map[package_name] = custom_widget

        self.listRefreshed.emit()

    @pyqtSlot()
    def start_all_tooltip_fetches(self):
        print(f"UI: Refresh signal received. Starting {len(self.widget_map)} fetches.")
        for name, widget in self.widget_map.items():
            widget.setToolTip("Fetching details...")
            self.details_fetcher.fetch(name)

    @pyqtSlot(str, dict)
    def update_tooltip(self, name, data):
        widget = self.widget_map.get(name)
        if widget:
            tooltip_text = "\n".join(f"{k}: {v}" for k, v in data.items())
            widget.setToolTip(tooltip_text)
            print(f"UI: Updated tooltip for '{name}'.")

    def stop_worker(self):
        self.details_fetcher.stop()

# --- MAIN WINDOW FOR TESTING ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.library_widget = LibraryWidget()
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.do_refresh)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.library_widget)
        layout.addWidget(self.refresh_button)
        self.setCentralWidget(container)

        self.do_refresh() # Initial population

    def do_refresh(self):
        # Simulate getting a new list of packages
        packages = ["requests", "numpy", "pandas", "pyqt6", "scipy"]
        random.shuffle(packages)
        new_items = [{"name": p} for p in packages[:random.randint(3, 5)]]
        self.library_widget.add_items(new_items)

    def closeEvent(self, event):
        self.library_widget.stop_worker()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
