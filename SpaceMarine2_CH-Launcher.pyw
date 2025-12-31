# -*- coding: utf-8 -*-
# ==================================================
# Space Marine 2 - CH-Launcher
VERSION = "1.0.1"
DEBUG = False

# ==================================================
# IMPORTS
# ==================================================
import os
import sys
import shutil
import ctypes
import subprocess
import threading
import webbrowser
import urllib.request
import urllib.error
import time

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# ==================================================
# VARIABLES
# ==================================================

APP_NAME = "Space Marine 2"
APP_TITLE = "Space Marine 2 - CH-Launcher"
APP_ID = "2183900"
APP_EXE = "start_protected_game.exe"

LAUNCHER_NAME = "CHSpaceMarinesLauncher.EXE"

START_WAIT = 17
MAX_START_WAIT = 60

TARGET_PATH = r'C:\Program Files (x86)\Steam\steamapps\common\Space Marine 2'

# ==============================

TIMEOUT_SECONDS = 5
POLL_INTERVAL = 0.5

INTERFACE_KEYWORDS = (
    "drahtlos",
    "ethernet",
    "lan",
    "netzwerk",
    "wi-fi",
    "wifi",
    "wireless",
    "wlan",
)

DISABLED_KEYWORDS = (
    "deaktiviert",
    "desativado",
    "deshabilitado",
    "devre dışı",
    "dezactivat",
    "disabilitato",
    "disabled",
    "désactivé",
    "letiltva",
    "uitgeschakeld",
    "wyłączone",
    "zakázané",
    "zakázáno",
    "вимкнено",
    "отключено",
)

CONNECTED_KEYWORDS = (
    "aangesloten",
    "bağlı",
    "conectado",
    "conectat",
    "connected",
    "connecté",
    "connesso",
    "csatlakoztatva",
    "połączono",
    "pripojené",
    "připojeno",
    "verbunden",
    "подключено",
    "підключено",
)

# ==================================================
# FUNCTIONS
# ==================================================

# ==============================
# Logging
# ==============================
def print_debug(message: str):
    # print_debug a message via stdout if DEBUG is enabled
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stdout)

def print_error(message: str):
    # print_error a message via stderr
    print(message, file=sys.stderr)

def print_success(message: str):
    # print_success a message via stdout
    print(message, file=sys.stdout)


# ==============================
# Path resolution
# ==============================
def resolve_target_path():
    # Resolve and validate TARGET_PATH, fallback to script directory if not found.
    if TARGET_PATH and os.path.isdir(TARGET_PATH):
        print_debug(f"Using configured path: {TARGET_PATH}")
        return TARGET_PATH
    fallback = os.path.dirname(os.path.realpath(__file__))
    print_debug(f"Using script directory: {fallback}")
    return fallback

BASE_PATH = resolve_target_path()
LAUNCHER_PATH = os.path.join(BASE_PATH, LAUNCHER_NAME)
EAC_PATH = os.path.join(BASE_PATH, "EasyAntiCheat")

SETTINGS_MAIN = os.path.join(EAC_PATH, "Settings.json")
Settings_original = os.path.join(EAC_PATH, "Settings_original.json")
Settings_modified = os.path.join(EAC_PATH, "Settings_modified.json")


# ==============================
# Admin Privileges
# ==============================
def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin() -> bool:
    print_debug("Requesting administrator privileges...")

    params = " ".join(f'"{arg}"' for arg in sys.argv)

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )

    return result > 32

def ensure_admin(relaunch: bool = False) -> bool:
    if is_admin() and not relaunch:
        print_debug("Running with administrator privileges.")
        return True

    success = relaunch_as_admin()

    if success:
        sys.exit(0)

    print_error("Administrator privileges denied.")
    return False


# ==============================
# Process Detection
# ==============================
def find_process(process: str) -> bool:
    user32 = ctypes.windll.user32
    process = process.lower()
    found = False

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, lparam):
        nonlocal found

        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)

        title = buffer.value
        if title.strip().lower() == process:
            found = True

            print_debug(f"Found: {title}")
            return False

        return True

    user32.EnumWindows(enum_proc, 0)
    return found


# ==============================
# Network Interface Management
# ==============================

# Get lists of active and inactive physical network interfaces.
def get_active_physical_interfaces():
    print_debug("Querying network interfaces...")
    result = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True,
        text=True,
        shell=False,
        check=False
    )

    if result.returncode != 0:
        print_error("Warning: Failed to query network interfaces.")
        return [], []

    active_interfaces = []
    inactive_interfaces = []

    for line in result.stdout.splitlines():
        line_lower = line.lower()
        parts = line.split()

        if len(parts) >= 4:
            interface_name = " ".join(parts[3:])
            if not any(word in line_lower for word in INTERFACE_KEYWORDS):
                continue

            if not any(word in line_lower for word in DISABLED_KEYWORDS):
                if not any(word in line_lower for word in CONNECTED_KEYWORDS):
                    continue
                print_success(f"Connected interface detected: {interface_name}")
                active_interfaces.append(interface_name)
            else:
                print_success(f"Inactive interface detected: {interface_name}")
                inactive_interfaces.append(interface_name)

    if not active_interfaces and not inactive_interfaces:
        print_error("No physical network interfaces found.")

    return active_interfaces, inactive_interfaces

# Check if a network interface is enabled.
def is_interface_enabled(interface_name: str) -> bool:
    result = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True,
        text=True,
        shell=False,
        check=False
    )

    for line in result.stdout.splitlines():
        if interface_name.lower() in line.lower():
            return not any(word in line.lower() for word in DISABLED_KEYWORDS)

    return False

# Enable or disable a network interface.
def set_interface_state(interface_name: str, enable: bool) -> bool:
    action = "enable" if enable else "disable"
    print_success(f"Attempting to {action} interface: {interface_name}")

    result = subprocess.run(
        [
            "netsh",
            "interface",
            "set",
            "interface",
            f'name="{interface_name}"',
            f"admin={action}"
        ],
        capture_output=True,
        text=True,
        shell=False,
        check=False
    )

    if result.returncode != 0:
        print_error(f"Failed to {action} interface.")
        if result.stderr.strip():
            print_error(f"{result.stderr.strip()}")
        return False

    start_time = time.time()
    while time.time() - start_time < TIMEOUT_SECONDS:
        if is_interface_enabled(interface_name) == enable:
            print_success(f"Interface {action}d successfully.")
            return True
        time.sleep(POLL_INTERVAL)

    print_error(f"WARNING: Timeout waiting for interface to {action}.")
    return False


# ==============================
# URL Reachability
# ==============================

# Check if a URL is reachable via HEAD request.
def is_reachable(URL, timeout=3):
    try:
        req = urllib.request.Request(
            f"{URL}",
            method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, TimeoutError):
        return False


# ==============================
# Utility functions
# ==============================

# Check if a file exists and is not empty.
def file_exists_and_not_empty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

# Safely delete a file if it exists.
def safe_delete(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
            print_debug(f"Deleted: {os.path.basename(path)}")
        except (OSError, PermissionError) as e:
            print_error(f"Could not delete {os.path.basename(path)}: {e}")

# Copy a file if the source exists and is not empty.
def copy_if_not_empty(src: str, dst: str):
    try:
        if os.path.isfile(src):
            if os.path.getsize(src) > 0:
                shutil.copy2(src, dst)
                print_success(f"Copied: {os.path.basename(src)} -> {os.path.basename(dst)}")
            else:
                print_error(f"Source file is empty: {os.path.basename(src)}")
        else:
            print_error(f"Source file not found: {os.path.basename(src)}")
    except (OSError, PermissionError) as e:
        print_error(
            f"Could not copy {os.path.basename(src)} to {os.path.basename(dst)}:\n"
            f"{e}"
        )


# ==============================
# GUI
# ==============================

class ConsoleRedirect:
    # Redirect console output to a Tkinter widget.
    def __init__(self, widget, tag="debug"):
        # Initialize the console redirect.
        self.widget = widget
        self.tag = tag

    def write(self, message):
        # Write a message to the widget.
        self.widget.after(0, self._append, message)

    def _append(self, message):
        # Append a message to the widget.
        self.widget.configure(state="normal")
        self.widget.insert("end", message, self.tag)
        self.widget.see("end")
        self.widget.configure(state="disabled")

    def flush(self):
        # Flush the output stream.
        ...


class LauncherGUI(tk.Tk):
    # Main launcher GUI application.
    def __init__(self):
        # Initialize the launcher GUI.
        super().__init__()

        self.title(f"{APP_TITLE} v{VERSION}")

        self.width = 450
        self.height = 400

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)

        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.minsize(self.width, self.height)
        self.resizable(True, True)

        self.attributes("-topmost", False)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.active = []
        self.inactive = []

        self.configure(bg="#1e1e1e")
        self._setup_styles()
        self._build_ui()

        sys.stdout = ConsoleRedirect(self.console, tag="debug" if DEBUG else "normal")
        sys.stderr = ConsoleRedirect(self.console, tag="error")

        ensure_admin()


    def clear_console(self):
        # Clear the console output.
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _setup_styles(self):
        # Setup GUI styles.
        self.style.map(
            "TButton",
            background=[
                ("active", "#222222"), # Hover
                ("pressed", "#222222") # Klick
            ],
            foreground=[
                ("disabled", "#777777")
            ]
        )

        self.style.configure(
            "TFrame",
            background="#1e1e1e"
        )

        self.style.configure(
            "TButton",
            background="#333333",
            foreground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            justify="center",
            padding=3,
        )

    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # -- Top Row -----------------------------
        btn_frame_top = ttk.Frame(main)
        btn_frame_top.pack(fill="x")

        for i in range(3):
            btn_frame_top.columnconfigure(i, weight=1, uniform="buttons")

        ttk.Button(
            btn_frame_top,
            text="Clear\nConsole Output",
            command=self.clear_console
        ).grid(row=0, column=0, sticky="ew")

        ttk.Button(
            btn_frame_top,
            text="Toogle\nAlways on Top",
            command=self.toggle_topmost
        ).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Button(
            btn_frame_top,
            text="Reload\nthis Launcher",
            command=lambda: ensure_admin(relaunch=True)
        ).grid(row=0, column=2, sticky="ew")

        # -- Middle Top --------------------------
        btn_frame_middle_top = ttk.Frame(main)
        btn_frame_middle_top.pack(fill="x")

        for i in range(3):
            btn_frame_middle_top.columnconfigure(i, weight=1, uniform="buttons")

        ttk.Button(
            btn_frame_middle_top,
            text="Detect\nInternet Interfaces",
            command=lambda: self.run_thread(self.detect)
        ).grid(row=1, column=0, sticky="ew", pady=(5, 2.5))

        ttk.Button(
            btn_frame_middle_top,
            text="Enable\nInternet Interfaces",
            command=lambda:
                self.run_thread(self.enable_inactive)
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 2.5))

        ttk.Button(
            btn_frame_middle_top,
            text="Disable\nInternet Interfaces",
            command=lambda:
                self.run_thread(self.disable_active)
        ).grid(row=1, column=2, sticky="ew", pady=(5, 2.5))

        # -- Middle Bot --------------------------
        btn_frame_middle_bot = ttk.Frame(main)
        btn_frame_middle_bot.pack(fill="x")

        for i in range(3):
            btn_frame_middle_bot.columnconfigure(i, weight=1, uniform="buttons")

        ttk.Button(
            btn_frame_middle_bot,
            text="Copy\nOriginal Settings",
            command=lambda: copy_if_not_empty(Settings_original, SETTINGS_MAIN)
        ).grid(row=2, column=0, sticky="ew", pady=(2.5, 5))

        ttk.Button(
            btn_frame_middle_bot,
            text="Copy\nModified Settings",
            command=lambda: copy_if_not_empty(Settings_modified, SETTINGS_MAIN)
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=(2.5, 5))

        ttk.Button(
            btn_frame_middle_bot,
            text="Start\nRepair Process",
            command=lambda: self.run_thread(self.repair)
        ).grid(row=2, column=2, sticky="ew", pady=(2.5, 5))

        # -- Bottom Row --------------------------
        btn_frame_bottom = ttk.Frame(main)
        btn_frame_bottom.pack(fill="x")

        for i in range(3):
            btn_frame_bottom.columnconfigure(i, weight=1, uniform="buttons")

        ttk.Button(
            btn_frame_bottom,
            text="Run Normal\n(Game unmodified)",
            command=lambda: self.run_thread(self.run_normal)
        ).grid(row=3, column=0, sticky="ew")

        ttk.Button(
            btn_frame_bottom,
            text=f"Run with Bypass\n(Auto: {START_WAIT}s)",
            command=lambda: self.run_thread(self.run_with_modification)
        ).grid(row=3, column=1, sticky="ew", padx=5)

        ttk.Button(
            btn_frame_bottom,
            text="Run with Bypass\n(Manual Confirm)",
            command=lambda: self.run_thread(lambda: self.run_with_modification(manual=True))
        ).grid(row=3, column=2, sticky="ew")

        # -- Separator ---------------------------

        ttk.Separator(main).pack(fill="x", pady=(10, 10))

        # -- Console Output ----------------------
        console_frame = ttk.Frame(main)
        console_frame.pack(fill="both", expand=True)

        self.console = tk.Text(
            console_frame,
            height=10,
            bg="#111111",
            fg="#00ff00",
            insertbackground="white",
            state="disabled",
            wrap="word"
        )

        scrollbar = ttk.Scrollbar(
            console_frame,
            orient="vertical",
            command=self.console.yview
        )

        self.console.configure(yscrollcommand=scrollbar.set)

        # Configure text tags for colors
        self.console.tag_configure("debug", foreground="#0000ff")
        self.console.tag_configure("normal", foreground="#00ff00")
        self.console.tag_configure("error", foreground="#ff0000")

        self.console.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # Run a function in a separate thread.
    def run_thread(self, func):
        self.clear_console()
        threading.Thread(target=func, daemon=True).start()

    # Toggle the always-on-top attribute.
    def toggle_topmost(self, state=None) -> None:
        if state is not None:
            self.attributes("-topmost", state)
            if state:
                print_debug("Enabling always on top.")
            else:
                print_debug("Disabling always on top.")
        else:
            if self.attributes("-topmost"):
                print_debug("Disabling always on top.")
                self.attributes("-topmost", False)
            else:
                print_debug("Enabling always on top.")
                self.attributes("-topmost", True)

    # Run the repair flow for the game.
    def run_repair_flow(self, first_launch: bool = False) -> None:
        URL="https://store.steampowered.com"

        if first_launch:
            proceed = messagebox.askyesno(
                "First Launch Repair",
                "Settings_original.json not found.\n"
                "This indicates first launch of this launcher.\n\n"
                "The repair process will now start to ensure that the correct files are present. OK?"
            )
        else:
            proceed = messagebox.askyesno(
                "Start Repair?",
                "The repair process will start now. OK?"
            )

        if not proceed:
            print_error("Repair process cancelled by user.")
            return

        if not is_reachable(URL, timeout=3):
            print_error(
                f"{URL} not reachable.\n"
                "Cannot repair game via Steam, check your internet connections."
            )
            return

        topmost = self.attributes("-topmost")

        try:
            print_success("Starting repair flow...")
            safe_delete(Settings_original)
            safe_delete(Settings_modified)

            self.toggle_topmost(state=False)
            print_success("Validating game files via Steam...")
            webbrowser.open(f"steam://validate/{APP_ID}")

            while True:
                messagebox.showinfo(
                    "Repair Process",
                    "Repair started..\n\n"
                    "Wait until Steam finishes validating the game files!"
                )

                proceed = messagebox.askyesno(
                    "Confirmation",
                    "Repair process really finished?"
                )

                if proceed:
                    print_debug("Repair process confirmed as complete.")
                    break

            copy_if_not_empty(SETTINGS_MAIN, Settings_original)

        except (OSError, RuntimeError, ValueError) as e:
            self.toggle_topmost(state=topmost)
            print_error(
                "An error occurred during repair:"
                f"{e}"
            )
            return

    # Run the game in normal mode.
    def run_normal(self):
        print_success("=== Running in NORMAL mode ===")
        copy_if_not_empty(Settings_original, SETTINGS_MAIN)

        topmost = self.attributes("-topmost")

        try:
            self.toggle_topmost(state=True)

            print_debug("Starting the game via Steam...")
            webbrowser.open(f"steam://rungameid/{APP_ID}")

            self.toggle_topmost(state=False)

        except (OSError, RuntimeError) as e:
            print_error(
                "Failed to start the game via Steam protocol:\n"
                f"{e}"
            )
            self.toggle_topmost(state=topmost)

        sys.exit(0)

    # Run the game with modifications.
    def run_with_modification(self, manual: bool = False) -> None:
        if not is_admin():
            print_error(
                "Cannot run modifications without administrator privileges.\n"
                "Reload Launcher and grant administrator privileges."
            )
            return

        success = False
        topmost = self.attributes("-topmost")

        print_success("=== Running with BYPASS ===")
        try:
            print_success("Disabling network interfaces...")
            self.disable_active()

            print_success(f"Starting game via launcher: {LAUNCHER_NAME}")
            subprocess.Popen([LAUNCHER_PATH], cwd=BASE_PATH)

            print_success(f"Waiting for {APP_NAME} to start...")
            for i in range(MAX_START_WAIT, 0, -1):
                if find_process(APP_NAME):
                    self.toggle_topmost(state=True)
                    print_debug(f"{APP_NAME} process detected.")
                    if manual:
                        # Prompt user for manual confirmation
                        messagebox.showinfo(
                            "Manual Confirmation",
                            f"{APP_NAME} process detected.\n\n"
                            "Please confirm when the game has fully launched."
                        )
                    else:
                        print_success(f"Waiting {START_WAIT} seconds for full launch...")
                        # Extra wait to ensure full launch
                        time.sleep(START_WAIT)
                    break

                time.sleep(1)

                if i <= 1:
                    print_error(f"Game did not start after {MAX_START_WAIT} seconds.")
                    return

            success = True

        except (OSError, RuntimeError, FileNotFoundError) as e:
            print_error(
                "Failed to start the game via Launcher:\n"
                f"{e}"
            )
            self.toggle_topmost(state=topmost)

        finally:
            print_success("Enabling network interfaces...")
            self.enable_inactive()

            if success:
                self.toggle_topmost(state=False)
                copy_if_not_empty(SETTINGS_MAIN, Settings_modified)

    # Run the repair flow.
    def repair(self):
        success = self.run_repair_flow()
        if success:
            sys.exit(0)

    # Detect active and inactive network interfaces.
    def detect(self):
        print_debug("Detecting interfaces..")
        self.active, self.inactive = get_active_physical_interfaces()
        print_debug("Detection complete.")

    # Disable all active network interfaces.
    def disable_active(self):
        self.detect()
        if not self.active:
            print_success("No active interfaces found.")
            return

        print_debug(f"Found {len(self.active)} active interface(s).")

        if is_admin():
            for iface in self.active:
                set_interface_state(iface, False)
        else:
            print_error(
                "Cannot disable interfaces without administrator privileges.\n"
                "Reload Launcher and grant administrator privileges."
            )
            return

    # Enable all inactive network interfaces.
    def enable_inactive(self):
        self.detect()
        if not self.inactive:
            print_success("No inactive interfaces found.")
            return

        print_debug(f"Found {len(self.inactive)} inactive interface(s).")

        if is_admin():
            for iface in self.inactive:
                set_interface_state(iface, True)
        else:
            print_error(
                "Cannot enable interfaces without administrator privileges.\n"
                "Reload Launcher and grant administrator privileges."
            )
            return


# ==============================
# MAIN ENTRY POINT
# ==============================
if __name__ == "__main__":
    app = LauncherGUI()

    # ==============================
    # Pre-launch checks
    # ==============================

    if not os.path.isfile(os.path.join(BASE_PATH, APP_EXE)):
        messagebox.showwarning(
            "Game not found!",
            f"{APP_EXE} not found in default steam location.\n"
            f"You can copy {os.path.realpath(__file__)} into the game root directory e.g.:\n"
            rf"{TARGET_PATH}\{os.path.basename(__file__)} (default)"
        )
        sys.exit(1)

    if not os.path.isfile(LAUNCHER_PATH):
        messagebox.showwarning(
            f"CH-Launcher not found!",
            f"{LAUNCHER_NAME} not found in game location.\n"
            "Please download the latest version and copy into the game root directory e.g.:\n"
            rf"{TARGET_PATH}\{LAUNCHER_NAME} (default)"
        )
        sys.exit(1)

    if not os.path.isdir(EAC_PATH):
        messagebox.showwarning(
            "EAC directory not found!",
            f"{os.path.basename(EAC_PATH)} directory not found.\n"
            rf"Missing path: {EAC_PATH} (default)"
        )
        sys.exit(1)

    if not file_exists_and_not_empty(Settings_original):
        app.run_repair_flow(first_launch = True)

    app.mainloop()
