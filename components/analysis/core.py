from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Analysis(QWidget):
    """
    Analysis page of the application
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis")
        self.main_layout = QVBoxLayout()
        self.label = QLabel("This is the analysis Page")
        self.main_layout.addWidget(self.label)
        self.setLayout(self.main_layout)
        pass
