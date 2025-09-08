from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
import os
from PyQt6.QtSvg import QSvgRenderer

def svg_to_icon(svg_path: str, fill_color: QColor = QColor(Qt.GlobalColor.transparent), size = QSize(64, 64)):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(fill_color)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
    painter.end()
    return QIcon(pixmap)



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
