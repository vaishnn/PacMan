from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DependencyTree(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dependencyTree")
        self.mainLayout = QVBoxLayout()
        label = QLabel("This is the dependencyTree Page")
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        pass
