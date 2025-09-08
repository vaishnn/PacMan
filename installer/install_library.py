import subprocess

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QModelIndex

class LibraryInstallerWorker(QObject):
    finished_signal = pyqtSignal(int, QModelIndex)

    def do_install(self, python_exec_path, library_name, model_index: QModelIndex):
        """This method executes the pip install command."""
        print(f"Worker thread ({QThread.currentThreadId()}): Starting installation of {library_name}...")
        try:
            # subprocess.run is a blocking call, which is now safely in the background
            result = subprocess.run(
                [python_exec_path, "-m", "pip", "install", library_name],
                capture_output=True,
                text=True,
                check=False # Don't raise an exception on non-zero exit codes
            )

            print("---STDOUT---")
            print(result.stdout)
            print("---STDERR---")
            print(result.stderr)

            self.finished_signal.emit(result.returncode, model_index)

        except Exception as e:
            print(f"An exception occurred: {e}")
            self.finished_signal.emit(-1, model_index) # Use -1 for exceptions

class LibraryInstaller(QObject):
    start_install_signal = pyqtSignal(str, str, QModelIndex)

    finished_signal = pyqtSignal(int, QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_installer = QThread()
        self.worker = LibraryInstallerWorker()
        self.worker.moveToThread(self.thread_installer)

        # --- Connections ---
        # 1. Connect the trigger signal to the worker's slot
        self.start_install_signal.connect(self.worker.do_install)
        self.worker.finished_signal.connect(self.finished_signal.emit)
        self.worker.finished_signal.connect(self.thread_installer.quit)
        self.thread_installer.finished.connect(self.thread_installer.deleteLater)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread_installer.start()

    def install(self, python_exec_path, library_name, model_index: QModelIndex):
        """
        Public method to start an installation.
        This EMITS A SIGNAL instead of calling a method directly.
        """
        print(f"Main thread ({QThread.currentThreadId()}): Requesting installation of {library_name}...")
        self.start_install_signal.emit(python_exec_path, library_name, model_index)

    def __del__(self):
        # Ensure thread is stopped when the object is destroyed
        if self.thread_installer.isRunning():
            self.thread_installer.quit()
            self.thread_installer.wait() # Wait for it to finish cleanly
