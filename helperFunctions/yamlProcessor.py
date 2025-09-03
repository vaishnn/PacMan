import re
import yaml

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
    pattern = r'\{\{\s*colors\.([a-zA-Z0-9._]+)\s*\}\}'
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

def seperate_yaml(yaml_dict: dict):
    """
    This will seperate the yaml file into colors and stylesheet
    (stylesheet have 2 or more different things )
    """
    colors = yaml_dict.get('colors', {})
    stylesheet = yaml_dict.get('stylesheet', {})

    _processed_stylesheets = {}

    for key, value in stylesheet.items():
        _processed_stylesheets[key] = process_yaml_templated(value, colors)

    yaml_dict['stylesheet'] = _processed_stylesheets
    return yaml_dict

# Currently will not be saving as QSS but still defining for future implementation
def write_stylesheet(processed_dict: dict, output_dir: str):
    pass

def load_config(yaml_file_path: str) -> dict:
    """Just Merges Every Function Present in the File"""
    yaml_dict = load_yaml(yaml_file_path)
    yaml_dict = seperate_yaml(yaml_dict)

    return yaml_dict
