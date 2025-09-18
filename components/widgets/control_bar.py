from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .buttons import HoverIconButton  # Import from the same package

class ControlBar(QWidget):
    """
    A Widget that contains the window controls of the application, like a custom title bar.
    """

    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(20)
        self.config = config
        self.setObjectName("controlBar")

        self._layout()
        self._mouse_press_pos = None

    def _layout(self):
        """
        Sets up the layout for the ControlBar widget.

        This method initializes the horizontal layout, configures its alignment,
        margins, and spacing, sets up the control buttons (close, minimize, maximize),
        and adds the application name label.
        """
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(3, 0, 5, 0)
        layout.setSpacing(9)

        self._setup_buttons()

        name_label = QLabel(
            self.config.get('app', {}).get('name', 'PacMan')
        )
        name_label.setObjectName("nameLabel")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter )
        name_label.setContentsMargins(4, 0, 0, 0)
        layout.addWidget(self.close_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)

        layout.addWidget(name_label)


        layout.addStretch()
        self.setLayout(layout)

    def _setup_buttons(self):
        """
        Initializes and configures the control buttons (close, minimize, maximize)
        for the ControlBar widget.
        """
        # Close Button
        self.close_button = HoverIconButton(icon_path="./assets/icons/close.svg")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(12, 12)
        self.close_button.clicked.connect(self.parent_window.close)

        # Minimize Button
        self.minimize_button = HoverIconButton(icon_path="./assets/icons/minimize.svg")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFixedSize(12, 12)
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)

        # Maximize Button
        self.maximize_button = HoverIconButton(icon_path="./assets/icons/maximize.svg")
        self.maximize_button.setObjectName("maximizeButton")
        self.maximize_button.setFixedSize(12, 12)
        self.maximize_button.clicked.connect(self.toggle_maximize)

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent): # type: ignore
        self._mouse_press_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent): # type: ignore
        if self._mouse_press_pos is not None:
            delta = event.globalPosition().toPoint() - self._mouse_press_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self._mouse_press_pos = event.globalPosition().toPoint()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent): # type: ignore
        self._mouse_press_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None: # type: ignore
        self.toggle_maximize()
        return super().mouseDoubleClickEvent(a0)
