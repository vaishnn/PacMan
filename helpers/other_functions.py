import re
from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
import os
from PyQt6.QtSvg import QSvgRenderer
import yaml
from pathlib import Path
import subprocess

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


def svg_to_icon(svg_path: str, fill_color: QColor = QColor(Qt.GlobalColor.transparent), size = QSize(64, 64)):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(fill_color)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
    painter.end()
    return QIcon(pixmap)



def loadFont(fontPath: str, fontSize: int = 14) -> QFont:
    # This method is not working for relative paths, so currently using absolute paths
    try:
        scriptDir = os.getcwd()
        fontId = QFontDatabase.addApplicationFont(
            os.path.join(scriptDir, fontPath)
        )

        font = QFont(QFontDatabase.applicationFontFamilies(fontId)[0], int(fontSize))
        return font
    except Exception as e:
        print(f"Error loading font: {e}")
        return QFont("Arial", fontSize)


def load_yaml(path: str) -> dict:
    """
    This function loads a YAML file and returns its contents as a dictionary.
    - Loads YAML file if the file exists and it isn't corrupt.
    - Returns an empty dictionary if the file doesn't exist or is corrupt.
    """
    try:
        with open(path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found at {path}")
        return {}
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}

def process_yaml_templated(yaml_string: str, colors_dict):
    """
    This Processes the YAML string with templated colors.
    The Variables in the format {{ colors.<somename> }} will be replaced with the corresponding value from the colors
    """
    pattern = r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}'
    matches = re.finditer(pattern, yaml_string)

    result = yaml_string
    for match in matches:
        var_path = match.group(1)
        full_match = match.group(0)

        value = colors_dict
        try:
            for key in var_path.split('.'):
                value = value[key]

            result = result.replace(full_match, value)
        except (KeyError, TypeError):
            print("Error processing YAML template: ", full_match)

    return result

def seperate_yaml(ui, stylesheet: dict):
    """
    This will seperate the yaml file into colors and stylesheet
    (stylesheet have 2 or more different things )
    """

    _processed_stylesheets = {}

    for key, value in stylesheet.items():
        _processed_stylesheets[key] = process_yaml_templated(value, ui)

    return _processed_stylesheets

# Currently will not be saving as QSS but still defining for future implementation
def write_stylesheet(processed_dict: dict, output_dir: str):
    pass

def load_config(ui_file_path="config/ui.yaml",
    controls_file_path="config/paths.yaml",
    paths_file_path="config/application.yaml",
    application_path="config/controls.yaml") -> dict:
    """Just Merges Every Function Present in the File"""
    config = {}
    config.update(load_yaml(ui_file_path))
    config.update(load_yaml(controls_file_path))
    config.update(load_yaml(paths_file_path))
    config.update(load_yaml(application_path))

    config['stylesheet'] = seperate_yaml(config, config.get('stylesheet', ''))

    return config
