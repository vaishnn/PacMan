# PacMan
![PacMan ScreenShot](website/Images/PacMan.png)


PacMan is a graphical desktop application for managing Python packages, built with PyQt6. It provides a user-friendly interface to interact with `pip` and PyPI, simplifying the process of installing, uninstalling, and managing Python libraries.

## Features

*   **List Installed Packages:** View a list of all packages installed in a selected virtual environment.
*   **Search PyPI:** Search for available packages on the Python Package Index.
*   **Install Packages:** Install packages from PyPI with a single click.
*   **Uninstall Packages:** Remove packages from your environment.
*   **Virtual Environment Support:** Automatically detects and lists packages from a selected virtual environment.
*   **Custom Theming:** The application uses a customizable color scheme and fonts.

## Getting Started

### Prerequisites

*   Python 3
*   pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd PacMan
    ```

2.  **Install dependencies:**
    ```bash
    pip install PyQt6 requests beautifulsoup4 pyyaml
    ```

### Running the Application

```bash
python main.py
```

## Project Structure

```
├── Installer/      # Widgets and logic for the package installer
├── library/        # Widgets and logic for managing installed libraries
├── doingSomethingGO/ # Experimental Go code for listing packages
├── fonts/          # Application fonts
├── icons/          # UI icons
├── main.py         # Main application entry point
├── config.yaml     # Application configuration (API endpoints, fonts)
├── colorScheme.yaml # Application stylesheet
├── setup.py        # py2app build script for macOS
└── roadmap.md      # Detailed project roadmap
```

## Roadmap

A detailed project roadmap with planned features can be found in [roadmap.md](roadmap.md).

## License

This project is licensed under the MIT License.
