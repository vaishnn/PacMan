from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class About(QWidget):
    """
    About page of the application
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("about")
        self.main_layout = QVBoxLayout()
        label = QLabel("This is the about Page")
        self.main_layout.addWidget(label)
        self.setLayout(self.main_layout)
        pass
