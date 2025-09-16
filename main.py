import json
import os
import sys
from PyQt6.QtGui import  QFont, QFontDatabase, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QSplashScreen
)
from PyQt6.QtCore import Qt
import yaml
import re
from pacman import PacMan
from components.installer.pypi import get_app_support_directory

def loadFont(fontPath: str, fontSize: int = 14) -> QFont:
    # This method is not working for relative paths, so currently using absolute paths
    try:
        scriptDir = os.getcwd()
        fontId = QFontDatabase.addApplicationFont(
            os.path.join(scriptDir, fontPath)
        )

        font = QFont(QFontDatabase.applicationFontFamilies(fontId)[0], int(fontSize))
        return font
    except Exception as e:
        print(f"Error loading font: {e}")
        return QFont("Arial", fontSize)


def load_yaml(path: str) -> dict:
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

def process_yaml_templated(yaml_string: str, colors_dict):
    """
    This Processes the YAML string with templated colors.
    The Variables in the format {{ colors.<somename> }} will be replaced with the corresponding value from the colors
    """
    pattern = r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}'
    matches = re.finditer(pattern, yaml_string)

    result = yaml_string
    for match in matches:
        var_path = match.group(1)
        full_match = match.group(0)

        value = colors_dict
        try:
            for key in var_path.split('.'):
                value = value[key]

            result = result.replace(full_match, value)
        except (KeyError, TypeError):
            print("Error processing YAML template: ", full_match)

    return result

def seperate_yaml(ui, stylesheet: dict):
    """
    This will seperate the yaml file into colors and stylesheet
    (stylesheet have 2 or more different things )
    """

    _processed_stylesheets = {}

    for key, value in stylesheet.items():
        _processed_stylesheets[key] = process_yaml_templated(value, ui)

    return _processed_stylesheets

def load_config(ui_file_path="config/ui.yaml",
    controls_file_path="config/paths.yaml",
    paths_file_path="config/application.yaml",
    application_path="config/controls.yaml") -> dict:
    """Just Merges Every Function Present in the File"""
    config = {}
    config.update(load_yaml(ui_file_path))
    config.update(load_yaml(controls_file_path))
    config.update(load_yaml(paths_file_path))
    config.update(load_yaml(application_path))

    config['stylesheet'] = seperate_yaml(config, config.get('stylesheet', ''))

    return config

def load_state(file_name = "state.json"):
    directory = get_app_support_directory()
    file_path = os.path.join(directory, file_name)
    data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass
    return data



if __name__ == "__main__":
    # Entry Point of our applicaton
    app = QApplication(sys.argv)

    # Can be changed was thinking of any animation of the logo, but not that creative to create a good logo animiation
    pixmap = QPixmap("assets/icons/appLogo.png")
    pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) # Added for better scaling
    splash = QSplashScreen(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

    splash.setGeometry(*[300, 200, 800, 800])
    state = load_state()

    splash.show()
    splash.raise_()

    app.processEvents()

    config: dict = load_config()
    app.setApplicationDisplayName(
        config.get("application", {}).get("name", "")
    )
    app.setWindowIcon(QIcon(
        config.get("paths", {}).get("assets", {}).get("images", "").get("appLogo", "")
    ))

    app.applicationVersion = config.get("app", {}).get("version", "")

    fontPath = config.get("paths", {}).get("assets", {}).get("fonts", {}).get("main", "")
    if fontPath:
        font = loadFont(
            fontPath,
            config.get("ui", {}).get("dimensions", {}).get('fontSize', {}).get('mainFont', 14)
        )
        app.setFont(font)
    app.setStyleSheet(config.get("stylesheet", {}).get("main", ""))
    window = PacMan(state, config)

    window.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

    window.show()
    splash.finish(window)
    window.raise_()
    sys.exit(app.exec())
