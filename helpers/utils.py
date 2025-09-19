import sys
import os

# This code is specifically for mac
# Note to self: add some if else statements for windows execution
def get_app_support_directory(appName: str = "P4cMan") -> str:
    """Returns the application support directory path for macOS."""
    # Just creates the directory if it doesn't exist
    app_support_dir = os.path.expanduser(f"~/Library/Application Support/{appName}")
    os.makedirs(app_support_dir, exist_ok=True)

    return app_support_dir

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS #type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
