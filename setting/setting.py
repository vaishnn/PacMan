from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Setting(QWidget):
    """
    Setting page of the application
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("setting")
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the setting Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass
