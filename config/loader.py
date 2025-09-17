import os
import re
import yaml
from PyQt6.QtGui import QFont, QFontDatabase

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
