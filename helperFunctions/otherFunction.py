from PyQt6.QtGui import QFont, QFontDatabase
import os

def loadFont(fontPath: str, fontSize: int = 14) -> QFont:
    # This method is not working for relative paths, so currently using absolute paths
    try:
        scriptDir = os.getcwd()
        fontId = QFontDatabase.addApplicationFont(
            s:=os.path.join(scriptDir, fontPath)
        )
        print(s)
        font = QFont(QFontDatabase.applicationFontFamilies(fontId)[0], fontSize)
        return font
    except Exception as e:
        print(f"Error loading font: {e}")
        return QFont("Arial", fontSize)
