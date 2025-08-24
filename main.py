import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QListWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QStackedWidget
import yaml

def load_color_scheme(path="colorScheme.yaml"):
    try:
        with open(path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Color scheme file not found at {path}")
        raise
    except Exception as e:
        print(f"Error loading color scheme file: {e}")
        raise


class PacMan(QMainWindow):
    """
    Complete UI Will probably be implemented in here
    """
    def __init__(self, color_scheme: dict):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(color_scheme['main'])
        # Main Layout
        main_widget, main_layout = self.main_layout()

        # Add Side Bar
        side_bar, self.nav_items = self.sideBar()
        self.content_stack = self.createContentArea()

        main_layout.addWidget(side_bar)
        main_layout.addWidget(self.content_stack, 1)
        self.nav_items.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.setCentralWidget(main_widget)

    def main_layout(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_widget, main_layout

    def sideBar(self):
        side_bar = QWidget()
        side_bar.setObjectName("sidebar")
        side_bar.setFixedWidth(250)
        side_bar_layout = QVBoxLayout(side_bar)
        side_bar_layout.setContentsMargins(10, 10, 10, 10)
        side_bar_layout.setSpacing(15)

        nav_list = QListWidget()
        nav_list.setObjectName("navList")
        self.nav_lists = ["Libraries", "Analysis", "Dependency Tree", "Settings", "About"]
        for nav_list_items in self.nav_lists:
            nav_list.addItem(nav_list_items)
        nav_list.setContentsMargins(0, 0, 0, 0)
        nav_list.setSpacing(3)

        side_bar_layout.addWidget(nav_list)

        return side_bar, nav_list

    def createContentArea(self):
        content_stack = QStackedWidget()
        content_stack.setObjectName("contentStack")
        for item_text in self.nav_lists:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            label = QLabel(f"This is the {item_text} Page")
            page_layout.addWidget(label)
            content_stack.addWidget(page)

        return content_stack
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PacMan(load_color_scheme())
    window.show()
    sys.exit(app.exec())
