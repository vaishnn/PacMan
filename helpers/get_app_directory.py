import os

# This code is specifically for mac
# Note to self: add some if else statements for windows execution
def get_app_support_directory(appName: str = "PacMan") -> str:
    """Returns the application support directory path for macOS."""
    # Just creates the directory if it doesn't exist
    app_support_dir = os.path.expanduser(f"~/Library/Application Support/{appName}")
    os.makedirs(app_support_dir, exist_ok=True)

    return app_support_dir
