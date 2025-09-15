import json
import os
import sys
from PyQt6.QtGui import  QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QSplashScreen
)
from PyQt6.QtCore import Qt
from helpers.other_functions import loadFont
from helpers.yaml_pre_processing import load_config
from pacman import PacMan
from installer.pypi import get_app_support_directory


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
