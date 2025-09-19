import logging
import os

def setup_logging():
    """Creates a logging system"""

    log_folder = os.path.join(os.path.expanduser('~'), 'p4cman-logs')
