import json
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import os
import csv
from helpers.find_local_envs import find_virtual_envir

def get_site_packages_path(venv_path):
    """Gets the site-packages path for a given virtual environment."""
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    python_exec = os.path.join(venv_path, bin_dir, "python")
    code = "import sysconfig; print(sysconfig.get_paths()['purelib'])"
    try:
        result = subprocess.run([python_exec, "-c", code], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def _get_path_size(path):
    """Calculates the total size of a file or a directory."""
    if not os.path.exists(path):
        return 0
    if os.path.isfile(path):
        return os.path.getsize(path)

    total_size = 0
    try:
        for entry in os.scandir(path):
            if entry.is_dir():
                total_size += _get_path_size(entry.path)
            elif entry.is_file():

                total_size += entry.stat().st_size

    except OSError:
        # Handle potential permission errors or other OS issues gracefully
        return 0
    return total_size

# --- Main Logic ---

def get_installed_libraries_with_size(venv_path):
    """
    Lists all installed packages in a venv and calculates their size
    using the definitive hybrid strategy.
    """
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    pip_exec = os.path.abspath(os.path.join(venv_path, bin_dir, "pip"))
    python_exec = os.path.abspath(os.path.join(venv_path, bin_dir, "python"))

    if not os.path.isfile(pip_exec):
        pass
        # raise FileNotFoundError(f"pip executable not found at {pip_exec}")

    result = subprocess.run([pip_exec, "list", "--format=json", "--disable-pip-version-check"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list packages: {result.stderr}")

    packages = json.loads(result.stdout)
    site_packages = get_site_packages_path(venv_path)

    if not site_packages:
        raise NotADirectoryError("Could not determine site-packages directory.")

    details = []
    abs_site_packages = os.path.abspath(site_packages)
    for pkg in packages:
        name = pkg["name"]
        version = pkg["version"]

        paths_to_size = set()

        # --- STRATEGY 1: Modern Packages (.dist-info/RECORD) ---
        dist_info_name = f"{name.replace('-', '_')}-{version}.dist-info"
        dist_info_path = os.path.join(site_packages, dist_info_name)
        record_path = os.path.join(dist_info_path, 'RECORD')
        is_modern_package = os.path.isfile(record_path)
        if is_modern_package:
            # 1. Add the metadata folder itself to the set of paths.

            # 2. Read the RECORD to find all top-level code/data folders.
            try:
                with open(record_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row:
                            continue
                        relative_path = row[0]
                        abs_file_path = os.path.abspath(os.path.join(site_packages,relative_path))


                        if os.path.commonpath([abs_site_packages, abs_file_path]) == abs_site_packages:
                            top_level_item = relative_path.split(os.path.sep)[0]
                            paths_to_size.add(os.path.join(site_packages, top_level_item))
            except Exception:
                # If RECORD is malformed, we'll rely on the fallback below
                is_modern_package = False

        # --- STRATEGY 2: Fallback for Legacy Packages (no RECORD) ---
        if not is_modern_package:
            # 1. Guess the package folder name.
            path_underscores = os.path.join(site_packages, name.replace('-', '_'))
            if os.path.exists(path_underscores):
                paths_to_size.add(path_underscores)

            path_hyphens = os.path.join(site_packages, name)
            if os.path.exists(path_hyphens):
                paths_to_size.add(path_hyphens)

        # --- Final Calculation ---
        # Sum the sizes of all unique paths identified by the strategies.
        total_size = sum(_get_path_size(path) for path in paths_to_size)

        details.append({
            "name": name,
            "version": version,
            "size": total_size
        })

    return python_exec, details


class FetchLibraryList(QObject):
    """Seperate Thread for Get's list of library with version and space it's sharing using record and some naming convention"""
    finished = pyqtSignal(int, list)
    fetch = pyqtSignal(str, str)
    libraries = pyqtSignal(str, list, list)
    def __init__(self):
        super().__init__()
        self.threadRunner = QThread()
        self.worker = GoWorker()
        self.worker.moveToThread(self.threadRunner)
        self.fetch.connect(self.worker.run)
        self.worker.finished.connect(self.libraries.emit)
        self.threadRunner.finished.connect(self.worker.deleteLater)
        self.threadRunner.start()

    def get_details(self, project_path, virtual_env = ""):
        self.fetch.emit(project_path, virtual_env)

    def stop(self):
        if self.threadRunner.isRunning():
            self.threadRunner.quit()
            self.threadRunner.wait()




class GoWorker(QObject):
    """
    Worker class for getting list of libraries
    """
    finished  = pyqtSignal( str, list, list)
    def run(self, project_path, virtual_env_name = ""):

        try:
            virtual_env_paired_with_python_version = []
            virtual_envs = find_virtual_envir(project_path)
            for virtual_environment in virtual_envs:
                virtual_env_paired_with_python_version.append(virtual_environment.venv_name+ ":   " +
                    f"{virtual_environment.python_version}")
            if virtual_env_name == "":
                virtual_env_name = virtual_env_paired_with_python_version[0].split(":")[0].strip()

            venv_path = os.path.abspath(os.path.join(project_path, virtual_env_name))
            python_exec, details = get_installed_libraries_with_size(venv_path)

            self.finished.emit(python_exec, details, virtual_env_paired_with_python_version)
        except FileNotFoundError:
            self.finished.emit("", "", [], "Executable Not Found")
        except Exception as e:
            self.finished.emit("", "", [], f"Some error idk {e}")
