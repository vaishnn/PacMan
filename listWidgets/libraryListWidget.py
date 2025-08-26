from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot, QEvent
import subprocess
# Implementation to be DONE of Better Layout and After Changing virtual Path it doesn't shows the Library Details

class hoverOverListLibraries(QListWidget):

    # Will be Implementing but don't really know how to implement it
    itemHovered = pyqtSignal(str)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.toolTipCache = {}
        self.lastHoveredItem = None
        self.setMouseTracking(True)

    def event(self, event: QEvent): #type: ignore
        if event.type() == QEvent.Type.ToolTip:
            pos = event.pos() #type: ignore
            item = self.itemAt(pos)

            if item:
                pass


class library(QWidget):
    """
    This class is for all Library Related Widgets
    """
    listLibraryRefreshed = pyqtSignal()
    def __init__(self, colorScheme):
        super().__init__()
        self.setStyleSheet(colorScheme)
        self.getLibraryDetails = getLibraryDetails()
        self.getLibraryDetails.detailsWithName.connect(self.getLibraryDetailsThroughClass)
        self.setObjectName("library")
        self.pythonExecPath = ""
        self.libraryLayout = QVBoxLayout(self)
        self.libraryLayout.setContentsMargins(5, 2, 2, 2)
        # self.libraryLayout.setSpacing(0)
        self.listLibraryRefreshed.connect(self.startAllTooltipFetches)
        # This is for mapping Library Item names with their respective widgets
        self.itemMap = {}

        self.libraryList = QListWidget()
        self.libraryList.setObjectName("libraryList")
        # self.libraryList.setResizeMode(QListView.ResizeMode.Adjust)
        self.libraryLayout.addWidget(self.libraryList)

    def setPythonExecPath(self, path):
        self.pythonExecPath = path

    def addItems(self, items):
        self.libraryList.clear()
        self.itemMap.clear()

        for item in items:
            listLibraryWidget = QWidget()
            listLibraryWidget.setObjectName("listLibraryWidget")
            listLibraryWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            listWidgetLayout = QHBoxLayout(listLibraryWidget)

            # All the QLabels

            # Name of the Library
            nameLibraryPanel = QLabel(item["name"])
            nameLibraryPanel.setObjectName("nameLibraryPanel")

            # Version of the Library
            versionLibraryPanel = QLabel(item["version"])
            versionLibraryPanel.setObjectName("versionLibraryPanel")

            # Tag of The Library
            if item["tag"] == "installed":
                tagLibraryPanel = QLabel("I")
            else:
                tagLibraryPanel = QLabel("D")
            tagLibraryPanel.setMaximumWidth(25)
            tagLibraryPanel.setObjectName("tagLibraryPanel")


            # Changing Properties of QLabels


            # Adding Widget in proper Order
            listWidgetLayout.addWidget(tagLibraryPanel)
            listWidgetLayout.addWidget(nameLibraryPanel)
            listWidgetLayout.addWidget(versionLibraryPanel)

            listItem = QListWidgetItem(self.libraryList)
            listItem.setSizeHint(listLibraryWidget.sizeHint())
            self.libraryList.addItem(listItem)
            self.libraryList.setItemWidget(listItem, listLibraryWidget)

            # listItem.setToolTip("Loading details...")
            self.itemMap[item["name"]] = listLibraryWidget
            # self.getLibraryDetails.fetchDetailLibraryDetails(item["name"])
        self.listLibraryRefreshed.emit()


    def startAllTooltipFetches(self):
        for package_name, widget in self.itemMap.items():
            widget.setToolTip("Fetching details...")
            self.getLibraryDetails.fetchDetailLibraryDetails(self.pythonExecPath, package_name)

    @pyqtSlot(str, dict)
    def getLibraryDetailsThroughClass(self, name, libraryDetails: dict):
        listItem = self.itemMap.get(name)
        if listItem:
            tooltip = f"""
            <p>
            Summary: {libraryDetails["Summary"]} <br>
            Home-page: {libraryDetails['Home-page']} <br>
            Author: {libraryDetails['Author']} <br>
            Requires: {libraryDetails['Requires']} <br>
            Required-by: {libraryDetails['Required-by']}
            </p>"""
            listItem.setToolTip(tooltip)

    def closeEvent(self, event): #type: ignore
        self.getLibraryDetails.stop()
        super().closeEvent(event)




class getLibraryDetails(QObject):
    detailsWithName = pyqtSignal(str, dict)
    requestReady = pyqtSignal(str, str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.threadRunner = QThread()
        self.worker = runCommandThroughPython()
        self.requestReady.connect(self.worker.run)
        self.worker.moveToThread(self.threadRunner)
        self.worker.finished.connect(self.returnCommandOutput)
        self.threadRunner.start()

    def fetchDetailLibraryDetails(self, pythonExecPath, name):
        self.requestReady.emit(pythonExecPath, name)

    @pyqtSlot(str, int, bytes, bytes)
    def returnCommandOutput(self, name, returnCode, stdout, stderr):
        if returnCode == 0 and not stderr:
            # Convert byte to string
            stdout = stdout.decode('utf-8')
            infoDict = {}
            for item in stdout.split('\n'):
                if ':' in item:
                    key, value = item.split(':', 1)
                    infoDict[key.strip()] = value.strip()
            self.detailsWithName.emit(name, infoDict)

    def stop(self):
        self.threadRunner.quit()
        self.threadRunner.wait()

class runCommandThroughPython(QObject):
    finished = pyqtSignal(str, int, bytes, bytes)
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot(str, str)
    def run(self, pythonExecPath, commandRun):
        command = [pythonExecPath,"-m", "pip", "show", commandRun]
        result = subprocess.run(command, capture_output = True)
        self.finished.emit(commandRun, result.returncode, result.stdout, result.stderr)
