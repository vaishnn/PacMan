import json
import os
from installer.pypi import get_app_support_directory

def load_state(file_name = "state.json"):
    directory = get_app_support_directory()
    file_path = os.path.join(directory, file_name)
    data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass
    return data

def save_state(project_path, venv_name_selected, file_name = "state.json"):
    directory = get_app_support_directory()
    file_path = os.path.join(directory, file_name)
    data = {
        "project_folder": project_path,
        "virtual_env_name": venv_name_selected,
    }
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file)
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    print(load_state())
