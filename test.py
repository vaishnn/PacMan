from PyQt6.QtWidgets import QApplication, QPushButton, QToolTip
from PyQt6.QtGui import QFont
import sys

def main():
    app = QApplication(sys.argv)

    # Apply QSS to QToolTip
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a82da;
            border: 1px solid white;
            padding: 5px;
            border-radius: 3px;
            font-size: 12px;
        }
    """)

    button = QPushButton('Hover Me')
    button.setToolTip('This is a custom styled tooltip!')
    button.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
