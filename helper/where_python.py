import re
import os
from pathlib import Path
import subprocess

from PyQt6.QtCore import QObject, QThread, pyqtSignal

def where_python_location(searching_paths: list[str] = [
    "/Library/Frameworks/Python.framework/Versions",
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin"
]) -> dict[str, str]:
    """
    This function searches for python interpreters in the given paths.
    """
    found_interpreters = {}
    python_executable_pattern = re.compile(r"^python(2|3)(\.\d+)?$")

    for folder in searching_paths:
        if not Path(folder).is_dir() and os.access(folder, os.X_OK):
            continue

        # Case for framework Path
        if "Framework" in folder:
            for files in Path(folder).iterdir():
                bin_dir = files / "bin" # / is an operator in Path class
                if bin_dir.exists():
                    for file in bin_dir.iterdir():
                        if python_executable_pattern.match(file.name) and os.access(file, os.X_OK):
                            just_path = file
                            try:
                                abs_path = just_path.resolve()

                                if abs_path in found_interpreters:
                                    version = subprocess.check_output([str(abs_path), "--version"], stderr = subprocess.STDOUT)
                                    found_interpreters[str(abs_path)] = version.decode().strip()
                            except Exception:
                                continue # This is for python named but doesn't have version and any other errors
        else:
            # For all the others paths
            for item in Path(folder).iterdir():
                if python_executable_pattern.match(item.name) and os.access(item, os.X_OK):
                    just_path = item
                    try:
                        abs_path = just_path.resolve()
                        if str(abs_path) not in found_interpreters:
                            version = subprocess.check_output([str(abs_path), "--version"], stderr = subprocess.STDOUT)
                            found_interpreters[version.decode().strip()] = str(abs_path)
                    except Exception:
                        continue
    return found_interpreters

class PythonInterpreters(QObject):
    release_details = pyqtSignal(dict)
    get_details = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.threadQ = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.threadQ)
        self.worker.finished.connect(self.release_interpreters)
        self.get_details.connect(self.worker.run)
        self.threadQ.finished.connect(self.worker.deleteLater)
        self.threadQ.start()

    def get_interpreters(self):
        self.get_details.emit()

    def release_interpreters(self, interpreters: dict):
        self.release_details.emit(interpreters)

    def stop(self):
        self.threadQ.quit()
        self.threadQ.wait()

class Worker(QObject):
    finished = pyqtSignal(dict)

    def run(self):
        where_python = where_python_location()
        self.finished.emit(where_python)

if __name__ == "__main__":
    pass
