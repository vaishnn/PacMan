from PyQt6.QtCore import QEvent, QPoint, QTimer, QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget


class InteractiveToolTip(QFrame):
    """
    A Custom tooltip for interactibility, scrollability
    """
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.setWindowFlag(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setMaximumSize(800, 400)
        self.widget = QWidget(self)
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(200) # Prevents tooltip from being too tall
        self.content_label = QLabel()
        self.content_label.setContentsMargins(10, 10, 10, 10)
        self.content_label.setWordWrap(True)
        self.content_label.setTextFormat(Qt.TextFormat.RichText)
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.content_label.linkActivated.connect(self._handle_link_click)
        self.content_label.setStyleSheet("background-color: transparent;") # Inherit background
        self.scroll_area.setWidget(self.content_label)
        layout.addWidget(self.scroll_area)
        self.widget.setLayout(layout)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(200) # Hide delay in ms
        self._hide_timer.timeout.connect(self.hide)

        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.setInterval(800) # Show delay in ms
        self._show_timer.timeout.connect(self._show_at_cursor)

        self._target_widget = None

    def _handle_link_click(self, link: str):
        QDesktopServices.openUrl(QUrl(link))

    def set_object_name(self, name):
        self.scroll_area.setObjectName(f"{name}ScrollArea")

    def set_content(self, html: str):
        self.content_label.setText(html)

    def install_on(self, widget):
        """Installs an event filter on the target widget to trigger the tooltip."""
        if not widget:
            return
        widget.installEventFilter(self)
        self._target_widget = widget

    def eventFilter(self, watched_obj, event) -> bool: #type: ignore
        """Filters events from the watched widget."""
        if watched_obj == self._target_widget:
            if event.type() == QEvent.Type.Enter:
                self._hide_timer.stop()
                self._show_timer.start()
            elif event.type() == QEvent.Type.Leave:
                self._show_timer.stop()
                self._hide_timer.start()
        return super().eventFilter(watched_obj, event)

    def _show_at_cursor(self):
        """Shows the tooltip at the current cursor position."""
        if not self._target_widget:
            return

        cursor_pos = self._target_widget.cursor().pos()
        # Adjust position to be below and to the right of the cursor
        self.move(cursor_pos + QPoint(15, 15))
        self.show()
        # Ensure the tooltip resizes to its content
        self.adjustSize()

    def enterEvent(self, event) -> None:
        """When the mouse enters the tooltip itself, cancel any pending hide action."""
        self._hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, a0):
        """When the mouse leaves the tooltip, start the hide timer."""
        self._hide_timer.start()
        super().leaveEvent(a0)
