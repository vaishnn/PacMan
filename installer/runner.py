import sys
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout

# --- The Worker ---
# This object will run in a separate thread and handle reading from the subprocess.
# It inherits from QObject to use Qt's signal/slot mechanism.
class StreamWorker(QObject):
    # Define a signal that will carry a string.
    # We'll emit this signal whenever we receive a new line of data.
    data_received = pyqtSignal(str)

    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self._is_running = True

    def run(self):
        """Reads from the stream and emits signals."""
        for line in iter(self.stream.readline, ''):
            if not self._is_running:
                break
            line = line.strip()
            if line:
                self.data_received.emit(line)
        # Signal that we're done
        self.data_received.emit("--- Stream closed ---")

    def stop(self):
        self._is_running = False


# --- The Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Go Communicator")
        self.go_process = None

        # --- UI Setup ---
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter a command and press Enter or click Send...")

        # Add a horizontal layout for buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Process")
        self.send_button = QPushButton("Send Command")
        self.stop_button = QPushButton("Stop Process")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.stop_button)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)

        self.main_layout.addWidget(self.command_input)
        self.main_layout.addLayout(button_layout) # Add the button layout here
        self.main_layout.addWidget(self.output_display)

        self.setCentralWidget(self.central_widget)

        # --- Connect Signals and Slots ---
        self.start_button.clicked.connect(self.start_subprocess)
        self.stop_button.clicked.connect(self.shutdown_subprocess)
        self.send_button.clicked.connect(self.send_command)
        self.command_input.returnPressed.connect(self.send_command)

        self.update_button_states()

    def update_button_states(self):
        """Enable/disable buttons based on process state."""
        is_running = self.go_process is not None and self.go_process.poll() is None
        self.start_button.setEnabled(not is_running)
        self.send_button.setEnabled(is_running)
        self.stop_button.setEnabled(is_running)

    def start_subprocess(self):
        """Launches the Go subprocess and sets up reader threads."""
        if self.go_process and self.go_process.poll() is None:
            self.output_display.append("--- Process is already running. ---")
            return

        try:
            self.go_process = subprocess.Popen(
                ['./s_go'], # Assumes the compiled Go program is named 'producer'
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1
            )
            self.output_display.append("--- Go subprocess started ---")

            # Setup worker and thread for stdout
            self.stdout_thread = QThread()
            self.stdout_worker = StreamWorker(self.go_process.stdout)
            self.stdout_worker.moveToThread(self.stdout_thread)
            self.stdout_thread.started.connect(self.stdout_worker.run)
            self.stdout_worker.data_received.connect(self.update_display)
            self.stdout_thread.start()

            # Setup worker and thread for stderr
            self.stderr_thread = QThread()
            self.stderr_worker = StreamWorker(self.go_process.stderr)
            self.stderr_worker.moveToThread(self.stderr_thread)
            self.stderr_thread.started.connect(self.stderr_worker.run)
            self.stderr_worker.data_received.connect(self.update_display)
            self.stderr_thread.start()

        except FileNotFoundError:
            self.output_display.append("ERROR: Go executable not found.")
            self.output_display.append("Please compile producer.go first: go build producer.go")
        except Exception as e:
            self.output_display.append(f"An unexpected error occurred: {e}")

        self.update_button_states()

    def send_command(self):
        """Sends the text from the input box to the Go process's stdin."""
        if self.go_process is None or self.go_process.poll() is not None:
            self.output_display.append("--- Process is not running. Cannot send command. ---")
            return

        command = self.command_input.text()
        if command:
            self.go_process.stdin.write(command + '\n')
            self.go_process.stdin.flush()
            self.command_input.clear()

    def update_display(self, text):
        """This method is a 'slot' that safely updates the QTextEdit."""
        self.output_display.setText(text)

    def shutdown_subprocess(self):
        """Gracefully shuts down the subprocess and associated threads."""
        self.output_display.append("--- Shutting down subprocess ---")
        if self.go_process:
            # 1. Terminate the subprocess first.
            # This closes the pipes and allows the blocking readline() calls in the
            # worker threads to exit.
            if self.go_process.poll() is None:
                try:
                    self.go_process.terminate()
                    # Wait for the process to terminate.
                    self.go_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.go_process.kill() # If terminate fails, kill it.
                except (IOError, BrokenPipeError):
                    pass # Ignore pipe errors on shutdown

            # 2. Now that the pipes are closed, the worker threads can finish.
            # Quit the QThreads and wait for them to exit cleanly.
            if hasattr(self, 'stdout_thread') and self.stdout_thread.isRunning():
                self.stdout_thread.quit()
                self.stdout_thread.wait() # This will no longer hang

            if hasattr(self, 'stderr_thread') and self.stderr_thread.isRunning():
                self.stderr_thread.quit()
                self.stderr_thread.wait() # This will no longer hang

            self.go_process = None
        self.update_button_states()

    def closeEvent(self, event):
        """This method is called when the window is closed."""
        self.shutdown_subprocess()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
