import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_WINDOW_PY = os.path.join(PROJECT_DIR, "main_window.py")

def get_pythonw_path():
    """Returns path to pythonw.exe on Windows (no console window), or sys.executable."""
    if sys.platform == "win32":
        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        if os.path.exists(pythonw_exe):
            return pythonw_exe
    return sys.executable

def get_windows_startup_file():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    if not os.path.exists(startup_dir):
        return None
    return os.path.join(startup_dir, "StartAirFlick.vbs")

def get_mac_launch_agent_file():
    home = os.path.expanduser("~")
    launch_agents = os.path.join(home, "Library", "LaunchAgents")
    return os.path.join(launch_agents, "com.airflick.drop.plist")

def get_linux_autostart_file():
    home = os.path.expanduser("~")
    autostart_dir = os.path.join(home, ".config", "autostart")
    return os.path.join(autostart_dir, "airflick.desktop")

def is_autostart_enabled():
    """Checks if autostart is currently registered for this app."""
    if sys.platform == "win32":
        vbs_path = get_windows_startup_file()
        if vbs_path and os.path.exists(vbs_path):
            try:
                with open(vbs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if PROJECT_DIR in content:
                        return True
            except Exception:
                pass
        return False
    elif sys.platform == "darwin":
        agent_path = get_mac_launch_agent_file()
        return os.path.exists(agent_path)
    else:
        desktop_path = get_linux_autostart_file()
        return os.path.exists(desktop_path)

def enable_autostart():
    """Automatically registers AirFlick Drop to launch silently on system startup."""
    try:
        if sys.platform == "win32":
            vbs_path = get_windows_startup_file()
            if not vbs_path:
                return False
            pythonw = get_pythonw_path()
            vbs_content = (
                f'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.CurrentDirectory = "{PROJECT_DIR}"\n'
                f'WshShell.Run """{pythonw}"" ""{MAIN_WINDOW_PY}"" --startup", 0, False\n'
            )
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_content)
            print(f"[AutoStart] Windows startup script automatically installed at: {vbs_path}")
            return True

        elif sys.platform == "darwin":
            agent_file = get_mac_launch_agent_file()
            os.makedirs(os.path.dirname(agent_file), exist_ok=True)
            python_bin = sys.executable
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.airflick.drop</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{MAIN_WINDOW_PY}</string>
        <string>--startup</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>
</dict>
</plist>
"""
            with open(agent_file, "w", encoding="utf-8") as f:
                f.write(plist_content)
            print(f"[AutoStart] macOS LaunchAgent registered at: {agent_file}")
            return True

        elif sys.platform.startswith("linux"):
            desktop_file = get_linux_autostart_file()
            os.makedirs(os.path.dirname(desktop_file), exist_ok=True)
            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={sys.executable} "{MAIN_WINDOW_PY}" --startup
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=AirFlick Drop
Comment=AirFlick Companion File Transfer
"""
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(desktop_content)
            print(f"[AutoStart] Linux autostart desktop entry created at: {desktop_file}")
            return True

    except Exception as e:
        print(f"[AutoStart] Failed to enable autostart: {e}")
        return False

def disable_autostart():
    """Removes the autostart entry."""
    try:
        if sys.platform == "win32":
            vbs_path = get_windows_startup_file()
            if vbs_path and os.path.exists(vbs_path):
                os.remove(vbs_path)
                print(f"[AutoStart] Removed Windows startup script.")
                return True
        elif sys.platform == "darwin":
            agent_file = get_mac_launch_agent_file()
            if os.path.exists(agent_file):
                os.remove(agent_file)
                print(f"[AutoStart] Removed macOS LaunchAgent.")
                return True
        else:
            desktop_file = get_linux_autostart_file()
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                print(f"[AutoStart] Removed Linux autostart file.")
                return True
    except Exception as e:
        print(f"[AutoStart] Failed to disable autostart: {e}")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--disable":
        disable_autostart()
    else:
        enable_autostart()
