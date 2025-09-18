from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DependencyTree(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dependencyTree")
        self.main_layout = QVBoxLayout()
        label = QLabel("This is the dependencyTree Page")
        self.main_layout.addWidget(label)
        self.setLayout(self.main_layout)
        pass
