from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
import sys

def print_all_fonts():
    # Create a QApplication instance (required for Qt classes like QFontDatabase)
    app = QApplication(sys.argv)

    # Get an instance of QFontDatabase
    font_database = QFontDatabase.families()

    # Get a list of all available font families

    # Print each font family
    print("Available Font Families:")
    for family in font_database:
        print(family)

    # Exit the application (optional, but good practice if not running a full GUI)

if __name__ == '__main__':
    print_all_fonts()
