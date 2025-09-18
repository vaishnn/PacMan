import sys
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt

from main_window import PacMan
from config.loader import load_config, load_font
from helpers.state_manager import load_state

if __name__ == "__main__":
    app = QApplication(sys.argv)

    pixmap = QPixmap("assets/icons/appLogo.png")
    pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    splash = QSplashScreen(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
    splash.show()
    app.processEvents()

    state = load_state()
    config: dict = load_config()

    app.setApplicationDisplayName(config.get("application", {}).get("name", ""))
    app.setWindowIcon(QIcon(config.get("paths", {}).get("assets", {}).get("images", {}).get("appLogo", "")))
    app.applicationVersion = config.get("app", {}).get("version", "")

    font_path = config.get("paths", {}).get("assets", {}).get("fonts", {}).get("main", "")
    if font_path:
        font_size = config.get("ui", {}).get("dimensions", {}).get('fontSize', {}).get('mainFont', 14)
        app.setFont(load_font(font_path, font_size))

    app.setStyleSheet(config.get("stylesheet", {}).get("main", ""))

    window = PacMan(state, config)
    window.show()
    splash.finish(window)

    sys.exit(app.exec())
