from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPainter
from PyQt6.QtWidgets import QComboBox, QLabel, QStyleOptionComboBox, QStyledItemDelegate, QTextEdit, QWidget

class LineEdit(QTextEdit):
    """
    A custom QTextEdit widget that filters key press events.

    This widget only allows alphanumeric characters, periods, and a predefined
    set of control keys (Backspace, Delete, Left, Up, Right, Down, Home, End,
    Enter, Tab, Backtab, Return) to be processed. All other key presses are ignored.
    """
    def keyPressEvent(self, event: QKeyEvent): #type: ignore
        text = event.text()
        if text.isalpha() or text.isdigit() or text == "." or event.key() in (
            0x01000003,  # Qt.Key_Backspace
                0x01000007,  # Qt.Key_Delete
                0x01000012,  # Qt.Key_Left
                0x01000013,  # Qt.Key_Up
                0x01000014,  # Qt.Key_Right
                0x01000015,  # Qt.Key_Down
                0x01000016,  # Qt.Key_Home
                0x01000017,  # Qt.Key_End
                0x01000020,  # Qt.Key_Enter
                0x01000004,  # Qt.Key_Tab
                0x01000005,  # Qt.Key_Backtab
                0x01000006,  # Qt.Key_Return
        ):
            super().keyPressEvent(event)

class Toast(QWidget):
    """
    A temporary, non-blocking notification widget ("toast").

    This widget displays a message for a specified duration and then automatically
    closes. It is designed to be frameless, translucent, and appears at the
    bottom center of its parent widget.
    """
    def __init__(self, parent, message, duration=2000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.label = QLabel(self)
        self.label.setText(message)
        self.label.setStyleSheet("""
            background: #2D2D2D;
            color: #EEEEEE;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()
        self.duration = duration

    def showEvent(self, event): #type: ignore
        # Position at bottom center of parent
        parent = self.parentWidget()
        if parent:
            pw, ph = parent.width(), parent.height()
            tw, th = self.label.width(), self.label.height()
            x = (pw - tw) // 2
            y = ph - th - 1  # 32px above bottom
            self.setGeometry(x, y, tw, th)
        QTimer.singleShot(self.duration, self.close)

class IntNotifier(QObject):
    value_changed = pyqtSignal(int)
    def __init__(self, initial = 0):
        super().__init__()
        self._value = initial

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self.value_changed.emit(new_value)

    def __int__(self):
        return self._value

    def __eq__(self, other):
        if isinstance(other, IntNotifier):
            return self._value == other._value
        return self._value == other

    def __add__(self, other):
        if isinstance(other, IntNotifier):
            return self._value + other._value
        return self._value + other

    def __radd__(self, other):
        return other + self._value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return f"IntNotifier({self._value})"

class HTMLDelegate(QStyledItemDelegate):
    """They may be used later"""
    def paint(self, painter, option, index):
        text = index.data()
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(text)
        label.setFixedSize(option.rect.size())
        painter.save() # type: ignore
        painter.translate(option.rect.topLeft()) # type: ignore
        label.render(painter)
        painter.restore() # type: ignore

class HTMLComboBox(QComboBox):
    """They may be used later"""
    def __init__(self, parent=None):
        super().__init__(parent)
    def paintEvent(self, event): # type: ignore
        super().paintEvent(event)
        painter = QPainter(self)
        option = QStyleOptionComboBox()
        option.rect = self.rect()
        index = self.model().index(self.currentIndex(), self.modelColumn(), self.rootModelIndex())# type: ignore
        text = index.data()
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(text)
        label.setFixedSize(option.rect.size())
        painter.save()
        painter.translate(option.rect.topLeft())
        label.render(painter)
        painter.restore()
