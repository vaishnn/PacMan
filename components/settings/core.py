from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Setting(QWidget):
    """
    Setting page of the application
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("setting")
        self.main_layout = QVBoxLayout()
        label = QLabel("This is the setting Page")
        self.main_layout.addWidget(label)
        self.setLayout(self.main_layout)
        pass
