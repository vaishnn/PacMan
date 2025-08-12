import wx
import wx.lib.mixins.listctrl as listmix
import importlib.metadata
import sys
import os
import math
import subprocess
import threading

def find_environment_paths(env_root):
    """
    Given the root of a Python environment, find the site-packages and python executable paths.
    Returns (site_packages_path, python_executable_path) or (None, None) if not found.
    """
    # Look for the python executable
    if sys.platform == "win32":
        py_exec = os.path.join(env_root, 'Scripts', 'python.exe')
    else:
        py_exec = os.path.join(env_root, 'bin', 'python')

    if not os.path.exists(py_exec):
        return None, None

    # Find the site-packages directory
    site_packages = None
    try:
        # Ask the target python interpreter where its site-packages is
        cmd = [py_exec, "-c", "import site; print(site.getsitepackages()[0])"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        site_packages = result.stdout.strip()
    except (subprocess.CalledProcessError, IndexError):
        # Fallback for older python versions or unusual setups
        if sys.platform == "win32":
            site_packages_dir = os.path.join(env_root, 'Lib', 'site-packages')
            if os.path.exists(site_packages_dir):
                site_packages = site_packages_dir
        else:
            lib_dir = os.path.join(env_root, 'lib')
            if os.path.exists(lib_dir):
                for item in os.listdir(lib_dir):
                    if item.startswith('python'):
                        sp_path = os.path.join(lib_dir, item, 'site-packages')
                        if os.path.exists(sp_path):
                            site_packages = sp_path
                            break

    return site_packages, py_exec

def get_installed_packages_with_sizes(site_packages_path):
    """
    Retrieves all installed Python packages from a specific site-packages directory.
    """
    packages = []
    # Use the path argument to look for packages in the selected environment
    for dist in importlib.metadata.distributions(path=[site_packages_path]):
        name = dist.metadata['name']
        version = dist.metadata['version']
        try:
            files = importlib.metadata.files(dist.name)
            total_size = 0
            if files:
                # To get the actual location, we need to resolve the file path against the search path
                resolved_files = [f for f in files if os.path.exists(os.path.join(site_packages_path, str(f)))]
                total_size = sum(os.path.getsize(os.path.join(site_packages_path, str(f))) for f in resolved_files)
            packages.append({'name': name, 'version': version, 'size': total_size})
        except (importlib.metadata.PackageNotFoundError, FileNotFoundError):
            packages.append({'name': name, 'version': version, 'size': 'N/A'})
            continue
    return packages

class SortableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent, *args, **kw):
        wx.ListCtrl.__init__(self, parent, *args, **kw)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 3)
        self.itemDataMap = {}

    def GetListCtrl(self):
        return self

class PackageListFrame(wx.Frame):
    def __init__(self, parent, title, env_paths):
        super(PackageListFrame, self).__init__(parent, title=title, size=(700, 550))

        self.site_packages_path, self.python_executable = env_paths

        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        install_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.package_install_input = wx.TextCtrl(self.panel, style=wx.TE_PROCESS_ENTER)
        self.package_install_input.SetHint("Enter package name to install")
        install_button = wx.Button(self.panel, label="Install")

        install_sizer.Add(self.package_install_input, 1, wx.EXPAND | wx.ALL, 5)
        install_sizer.Add(install_button, 0, wx.ALL, 5)

        main_sizer.Add(install_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.package_list_ctrl = SortableListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.package_list_ctrl.InsertColumn(0, 'Package', width=250)
        self.package_list_ctrl.InsertColumn(1, 'Version', width=100)
        self.package_list_ctrl.InsertColumn(2, 'Size', width=100, format=wx.LIST_FORMAT_RIGHT)

        main_sizer.Add(self.package_list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        uninstall_button = wx.Button(self.panel, label="Uninstall Selected")
        refresh_button = wx.Button(self.panel, label="Refresh")

        button_sizer.Add(uninstall_button, 0, wx.ALL, 5)
        button_sizer.Add(refresh_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        self.panel.SetSizer(main_sizer)
        self.CreateStatusBar()
        self.Centre()
        self.Show()

        install_button.Bind(wx.EVT_BUTTON, self.on_install)
        self.package_install_input.Bind(wx.EVT_TEXT_ENTER, self.on_install)
        uninstall_button.Bind(wx.EVT_BUTTON, self.on_uninstall)
        refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh)

        wx.CallAfter(self.load_package_data)

    def run_pip_command(self, command, message):
        progress = wx.ProgressDialog("In Progress", message, parent=self, style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME)

        def task(cmd, py_exec):
            try:
                subprocess.run([py_exec, "-m", "pip"] + cmd, check=True, capture_output=True, text=True, startupinfo=None)
                wx.CallAfter(progress.Destroy)
                wx.CallAfter(self.on_refresh)
            except subprocess.CalledProcessError as e:
                wx.CallAfter(progress.Destroy)
                error_msg = f"Failed to {cmd[0]} package.\n\nError: {e.stderr}"
                wx.CallAfter(wx.MessageBox, error_msg, "Error", wx.OK | wx.ICON_ERROR)

        thread = threading.Thread(target=task, args=(command, self.python_executable))
        thread.start()
        progress.ShowModal()

    def on_install(self, event):
        package_name = self.package_install_input.GetValue().strip()
        if not package_name:
            wx.MessageBox("Please enter a package name to install.", "Info", wx.OK | wx.ICON_INFORMATION)
            return
        self.run_pip_command(["install", package_name], f"Installing {package_name}...")
        self.package_install_input.Clear()

    def on_uninstall(self, event):
        selected_item = self.package_list_ctrl.GetFirstSelected()
        if selected_item == -1:
            wx.MessageBox("Please select a package to uninstall.", "Info", wx.OK | wx.ICON_INFORMATION)
            return
        package_name = self.package_list_ctrl.GetItemText(selected_item)
        confirm = wx.MessageBox(f"Are you sure you want to uninstall {package_name}?", "Confirm Uninstall", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if confirm == wx.YES:
            self.run_pip_command(["uninstall", "-y", package_name], f"Uninstalling {package_name}...")

    def on_refresh(self, event=None):
        self.load_package_data()

    def format_size(self, size_bytes):
        if not isinstance(size_bytes, (int, float)) or size_bytes < 0: return "N/A"
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def load_package_data(self):
        self.SetStatusText("Scanning packages...")
        self.package_list_ctrl.DeleteAllItems()
        self.package_list_ctrl.InsertItem(0, "Please wait, scanning packages...")
        self.panel.Layout()

        packages = get_installed_packages_with_sizes(self.site_packages_path)
        packages.sort(key=lambda p: p['size'] if isinstance(p['size'], (int, float)) else -1, reverse=True)
        self.package_list_ctrl.DeleteAllItems()

        self.package_list_ctrl.itemDataMap = {}
        total_size = 0
        for i, package in enumerate(packages):
            self.package_list_ctrl.InsertItem(i, package['name'])
            self.package_list_ctrl.SetItem(i, 1, package['version'])
            formatted_size = self.format_size(package['size'])
            self.package_list_ctrl.SetItem(i, 2, formatted_size)
            self.package_list_ctrl.SetItemData(i, i)
            self.package_list_ctrl.itemDataMap[i] = (package['name'], package['version'], package.get('size', 0))
            if isinstance(package['size'], (int, float)):
                total_size += package['size']

        listmix.ColumnSorterMixin.__init__(self.package_list_ctrl, 3)
        self.SetStatusText(f"Found {len(packages)} packages. Total size: {self.format_size(total_size)}")

def find_venv_path(base_path):
    """Searches for common venv names in the base path."""
    common_names = ['venv', '.venv']
    for name in common_names:
        path = os.path.join(base_path, name)
        if os.path.isdir(path):
            return path
    return None

if __name__ == '__main__':
    app = wx.App(False)

    env_root_path = None

    dlg = wx.DirDialog(None, "Choose a Project Folder Containing Your Virtual Environment", "", wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    if dlg.ShowModal() == wx.ID_OK:
        project_path = dlg.GetPath()
        dlg.Destroy()

        env_root_path = find_venv_path(project_path)

        if not env_root_path:
            # If not found automatically, ask the user for the venv folder name
            entry_dlg = wx.TextEntryDialog(None, "Could not find 'venv' or '.venv'.\nPlease enter the name of your virtual environment folder:", "Enter Venv Name")
            if entry_dlg.ShowModal() == wx.ID_OK:
                venv_name = entry_dlg.GetValue()
                path = os.path.join(project_path, venv_name)
                if os.path.isdir(path):
                    env_root_path = path
                else:
                    wx.MessageBox(f"The folder '{venv_name}' does not exist in the selected directory.", "Error", wx.OK | wx.ICON_ERROR)
            entry_dlg.Destroy()

    else:
        dlg.Destroy()

    if not env_root_path:
        app.Destroy()
        sys.exit(0)

    env_paths = find_environment_paths(env_root_path)
    if not all(env_paths):
        wx.MessageBox("Could not find a valid Python executable and/or site-packages in the specified environment.", "Error", wx.OK | wx.ICON_ERROR)
        app.Destroy()
        sys.exit(1)

    frame = PackageListFrame(None, f"Package Manager - {env_root_path}", env_paths)
    app.MainLoop()
