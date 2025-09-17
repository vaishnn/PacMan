from PyQt6.QtGui import QIcon, QPainter
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize, QEasingCurve, QPropertyAnimation, pyqtProperty #type: ignore


class RotatingPushButton(QPushButton):
    """
    A custom QPushButton that rotates its icon when the mouse hovers over it.

    The icon rotates from 0 degrees to 90 degrees on mouse enter,
    and rotates back to 0 degrees on mouse leave, with a smooth animation.
    """
    def __init__(self, parent=None):
        super().__init__("", parent)
        self._rotation = 0
        self.animation_prop = False
        self.setProperty('angle', 0)
        self.setFlat(True)


    def _setup_animation(self):
        """
        Sets up the QPropertyAnimation for the rotation effect.
        Initializes the animation only once when called for the first time.
        """
        if not self.animation_prop:
            self.animation = QPropertyAnimation(self, b'angle', None)
            self.animation.setDuration(300)
            self.animation.setEasingCurve(QEasingCurve.Type.InOutCirc)
            self.animation_prop = True

    @pyqtProperty(int)
    def angle(self): #type: ignore
        return self._rotation

    @angle.setter #type: ignore
    def angle(self, value):
        self._rotation = value
        self.update()

    def enterEvent(self, event):
        self._setup_animation()
        self.animation.setEndValue(90)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, a0):
        self.animation.setEndValue(0)
        self.animation.start()
        return super().leaveEvent(a0)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHints(
             QPainter.RenderHint.LosslessImageRendering
        )
        # painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform | QPainter.)
        painter.save()
        if self.animation_prop:
            center = self.rect().center()
            painter.translate(center)
            painter.rotate(self._rotation)
            painter.translate(-center)

        icon_pixmap = self.icon().pixmap(QSize(10, 10))
        icon_rect = icon_pixmap.rect()
        icon_rect.moveCenter(self.rect().center())
        painter.drawPixmap(icon_rect, icon_pixmap)
        painter.restore()


class HoverIconButton(QPushButton):
    """
    A custom QPushButton that shows an icon on hover and controls its size.
    """
    def __init__(self, icon_path, size=6, parent=None):
        super().__init__(parent)
        self._icon_path = icon_path
        self._icon = QIcon(self._icon_path)
        self._icon_size = QSize(size, size)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setIcon(self._icon)
        self.setIconSize(self._icon_size)

    def leaveEvent(self, event): # type: ignore
        super().leaveEvent(event)
        self.setIcon(QIcon()) # Set an empty icon to hide it
