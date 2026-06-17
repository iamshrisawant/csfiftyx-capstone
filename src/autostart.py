import os
import sys
import platform

class AutostartManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.system = platform.system()
        
    def get_launcher_path(self):
        if self.system == "Windows":
            return os.path.join(self.base_dir, "run.bat")
        else:
            return os.path.join(self.base_dir, "run.sh")
            
    def is_enabled(self):
        if self.system == "Linux":
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, "diginotes.desktop")
            return os.path.exists(desktop_file)
            
        elif self.system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ
                )
                try:
                    winreg.QueryValueEx(key, "DigiNotes")
                    return True
                except FileNotFoundError:
                    return False
                finally:
                    winreg.CloseKey(key)
            except Exception:
                return False
                
        elif self.system == "Darwin": # macOS
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.diginotes.startup.plist")
            return os.path.exists(plist_path)
            
        return False
        
    def set_enabled(self, enable):
        if self.system == "Linux":
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, "diginotes.desktop")
            
            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                launcher = self.get_launcher_path()
                content = f"""[Desktop Entry]
Type=Application
Name=DigiNotes
Exec="{launcher}" --startup
Icon=system-run
Comment=Sticky notes manager
Terminal=false
X-GNOME-Autostart-enabled=true
"""
                try:
                    with open(desktop_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    os.chmod(desktop_file, 0o755)
                    return True
                except Exception as e:
                    print("Failed to enable autostart on Linux:", e)
                    return False
            else:
                if os.path.exists(desktop_file):
                    try:
                        os.remove(desktop_file)
                        return True
                    except Exception as e:
                        print("Failed to disable autostart on Linux:", e)
                        return False
                        
        elif self.system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_WRITE
                )
                try:
                    if enable:
                        launcher = self.get_launcher_path()
                        winreg.SetValueEx(key, "DigiNotes", 0, winreg.REG_SZ, f'"{launcher}" --startup')
                    else:
                        try:
                            winreg.DeleteValue(key, "DigiNotes")
                        except FileNotFoundError:
                            pass
                    return True
                finally:
                    winreg.CloseKey(key)
            except Exception as e:
                print("Failed to toggle autostart on Windows:", e)
                return False
                
        elif self.system == "Darwin":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.diginotes.startup.plist")
            if enable:
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                launcher = self.get_launcher_path()
                content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.diginotes.startup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{launcher}</string>
        <string>--startup</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                try:
                    with open(plist_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return True
                except Exception as e:
                    print("Failed to enable autostart on macOS:", e)
                    return False
            else:
                if os.path.exists(plist_path):
                    try:
                        os.remove(plist_path)
                        return True
                    except Exception as e:
                        print("Failed to disable autostart on macOS:", e)
                        return False
                        
        return False
