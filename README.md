# PacMan - Python Package Manager

![PacMan Screenshot](website/Images/PacMan.png)

PacMan is a graphical desktop application for managing Python packages and virtual environments, built with PyQt6. It provides a user-friendly interface to simplify the process of installing, uninstalling, and managing Python libraries for your projects.

## Features

*   **Virtual Environment Management**: Automatically detects and lets you select a Python virtual environment for your project.
*   **List Installed Packages**: View a list of all packages installed in the selected environment.
*   **Search PyPI**: Search for available packages on the Python Package Index (PyPI).
*   **Install & Uninstall Packages**: Easily install packages from PyPI or uninstall existing ones.
*   **Dependency Tree**: Visualize the dependency tree of your installed packages.
*   **Onboarding**: A simple setup process for new users to configure their project environment.
*   **Custom Theming**: The application is styled with a clean, dark theme.

## Getting Started

### Prerequisites

*   Python 3.x

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/PacMan.git
    cd PacMan
    ```

2.  **Create and activate a virtual environment (Recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Once the dependencies are installed, you can run the application with:
```bash
python main.py
```

## Project Structure

The project is organized into several modules to separate concerns:

```
├── assets/               # Icons, fonts, and other static assets
├── config/               # YAML configuration files for the application
├── dependency_tree/      # Logic for visualizing the package dependency tree
├── helpers/              # Helper functions and classes (e.g., state management)
├── installer/            # UI and logic for installing new packages
├── library/              # UI and logic for listing installed packages
├── onboarding/           # Widgets for the first-time user setup
├── ui/                   # Shared UI components (e.g., the control bar)
├── workers/              # Background threads for long-running tasks
├── main.py               # Main application entry point
├── pacman.py             # The main application window and layout
├── requirements.txt      # A list of python dependencies for this project
└── roadmap.md            # Detailed project roadmap
```

## License

This project is licensed under the MIT License.