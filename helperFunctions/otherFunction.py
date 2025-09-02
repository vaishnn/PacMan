from PyQt6.QtGui import QFont, QFontDatabase
import yaml
import os

def loadYaml(path: str) -> dict:
    """
    This function loads a YAML file and returns its contents as a dictionary.
    - Loads YAML file if the file exists and it isn't corrupt.
    - Returns an empty dictionary if the file doesn't exist or is corrupt.
    """
    try:
        with open(path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found at {path}")
        return {}
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}

def loadFont(fontPath: str, fontSize: int = 14) -> QFont:
    # This method is not working for relative paths, so currently using absolute paths
    try:
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        fontId = QFontDatabase.addApplicationFont(
            os.path.join(scriptDir, fontPath)
        )
        print(fontId)
        font = QFont(QFontDatabase.applicationFontFamilies(fontId)[0], fontSize)
        return font
    except Exception as e:
        print(f"Error loading font: {e}")
        return QFont("Arial", fontSize)
