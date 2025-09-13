import os
import subprocess
import sys

class Virtual_Env:
    def __init__(self, venv_name: str, venv_path: str, python_version: str, pip_path: str, python_path:str, libraries: list):
        self.venv_name = venv_name
        self.venv_path = venv_path
        self.python_version = python_version
        self.pip_path = pip_path
        self.python_path = python_path
        self.libraries = libraries

    def to_dict(self):
        return {
            "venv_name": self.venv_name,
            "venv_path": self.venv_path,
            "python_version": self.python_version,
            "pip_path": self.pip_path,
            "python_path": self.python_path,
            "libraries": [library.to_dict() for library in self.libraries if self.libraries],
        }
    def __str__(self) -> str:
        return f"""
        Venv Name: {self.venv_name}
        Venv Path: {self.venv_path}
        Python Version: {self.python_version}
        Pip Path: {self.pip_path}
        Python Path: {self.python_path}
        Libraries: {', '.join([library.name for library in self.libraries])}
        """

def find_virtual_envir(path: str) -> list[Virtual_Env]:
    # Find every virtual environment in the given path
    bin_dir_path: str
    python_exec: list
    pip_exec: list
    activate_exec: list

    if sys.platform == "win32":
        bin_dir_path = 'Scripts'
        python_exec = ['python.exe']
        pip_exec = ['pip.exe']
        activate_exec = ['activate.bat', 'Activate.ps1']
    else:

        bin_dir_path = 'bin'
        python_exec = ['python3', 'python']
        pip_exec = ['pip3', 'pip']
        activate_exec = ['activate']


    found_env = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            bin_path = os.path.join(path, item, bin_dir_path)
            include_path = os.path.join(path, item, "include")
            lib_path = os.path.join(path, item, "lib")
            if not (os.path.isdir(bin_path) and os.path.isdir(include_path) and os.path.isdir(lib_path)):
                continue
            has_python = any(
                pythons:=[os.path.isfile(os.path.join(bin_path, exe)) and os.access(os.path.join(bin_path, exe), os.X_OK) for exe in python_exec]
            )
            has_pip = any(
                pips:=[os.path.isfile(os.path.join(bin_path, exe)) and os.access(os.path.join(bin_path, exe), os.X_OK) for exe in pip_exec]
            )
            has_activate = any(
                os.path.isfile(os.path.join(bin_path, exe)) for exe in activate_exec
            )
            if has_python and has_pip and has_activate:
                python_present = [os.path.abspath(os.path.join(bin_path, python_exec[index])) for index, python_exe in enumerate(pythons) if python_exe]
                pip_present = [os.path.abspath(os.path.join(bin_path, pip_exec[index])) for index, pip_exe in enumerate(pips) if pip_exe]
                python_version = "Unknown"
                try:
                    result = subprocess.run(
                        [python_present[0], "--version"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5
                    )
                    version_output=(result.stdout+result.stderr).strip()
                    if version_output:
                        python_version = version_output.replace("Python", "").strip()
                        components = Virtual_Env(
                            venv_name=item,
                            venv_path=os.path.abspath(os.path.join(path, item)),
                            python_version=python_version,
                            python_path=os.path.abspath(os.path.join(bin_path, python_present[0])),
                            pip_path=os.path.abspath(os.path.join(bin_path, pip_present[0])),
                            libraries=[]
                        )
                        found_env.append(components)
                    else:
                        break
                except Exception as e:
                    print(f"Error occurred while getting Python version: {e}")
                    break

    return found_env

if __name__ == "__main__":
    print(find_virtual_envir("./"))
    print(2)
