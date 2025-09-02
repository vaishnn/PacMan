from PyQt6.QtCore import QObject
import requests
import yaml

def loadConfig(configFile: str) -> dict:
    try:
        with open(configFile, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file '{configFile}' not found.")
        return {}


def requestInfo(link: str, API_ENDPOINT: str) -> dict:
    pass


class requestDetails(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
