from setuptools import setup

APP = ['main.py'] # Your main script file
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    # --- THIS IS THE KEY PART FOR THE ICON ---
    'iconfile': 'icons/icon_1.icns', # Path to your icon file
    'packages': ['PyQt6'], # Include the PyQt6 package
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
