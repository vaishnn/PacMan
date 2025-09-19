# P4cMan 📦

P4cMan is a modern, high-performance desktop application for managing Python virtual environments and their packages. Built with a sleek PyQt6 user interface and a powerful Go backend for heavy lifting, P4cMan aims to provide a fast and intuitive development experience.

![P4cMan Demo](assets/readme/p4cman-demo.gif)


## ✨ Features

* **Modern UI**: A sleek, frameless user interface built with PyQt6 and styled with a flexible YAML-based theming engine.
* **Virtual Environment Management**: Effortlessly discover existing virtual environments within a project directory or create new ones from any detected Python interpreter on your system.
* **Package Manager**: View, search, install, and uninstall packages from PyPI within the context of your selected environment.
* **High-Performance Backend**: Leverages helper tools written in Go to perform concurrent, blocking operations (like discovering environments and fetching package data) without freezing the UI.
* **Rich Package Details**: Hover over any installed library to see a detailed tooltip with its summary, author, dependencies, license, and more.
* **Dependency Analysis**: Includes tools for visualizing the dependency tree of your projects.

---

## ⚙️ Tech Stack

* **Frontend & UI**: Python / PyQt6
* **Backend Helpers**: Go
* **Configuration**: YAML
* **Styling**: QSS (Qt Style Sheets) with YAML templating

---

## 📂 Project Structure

The project is organized into distinct modules for clarity and maintainability. This separation of concerns makes it easier to navigate, debug, and contribute to the codebase.

```plaintext
P4cMan/
├── main.py                 # Application entry point
├── main_window.py          # Main application shell (QMainWindow)
|
├── assets/                 # Icons, fonts, and other static resources
├── bin/                    # Compiled Go executables (platform-specific)
├── components/             # Self-contained UI features (installer, library, etc.)
├── config/                 # YAML configuration files for UI and paths
├── go-tools/               # Source code for the Go helper programs
├── helpers/                # Python helper modules (state management, etc.)
|
├── build.sh                # Script to build the Go executables
└── requirements.txt        # Python package dependencies
```
## 🚀 Getting Started

Follow these steps to get a local copy up and running.
Prerequisites
- Python 3.8+
- Go 1.25+
- Git

## Installation & Setup

1. Clone the repository
```bash
git clone https://github.com/vaishnn/P4cMan.git
cd P4cMan
```
2. Install Python dependencies
- It's recommended to do this in a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```
3. Build the Go helper executables
- The build script will compile the Go programs and place them in the bin/ directory.
```bash
# Make the script executable (only need to do this once)
chmod +x build.sh

# Run the build script
./build.sh
```
4. Run the application
```bash
python main.py
```
### 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
### 📄 License

This project is licensed under the MIT License.
