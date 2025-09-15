from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Analysis(QWidget):
    """
    Analysis page of the application
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("analysis")
        self.mainLayout = QVBoxLayout()
        self.label = QLabel("This is the analysis Page")
        self.mainLayout.addWidget(self.label)
        self.setLayout(self.mainLayout)
        pass
