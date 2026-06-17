# src/main.py

import sys
import os
import json
import uuid
import tempfile
import getpass
import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QAction, QFont
from PySide6.QtCore import QObject, Qt, QRect, QLockFile, QPoint

from note_window import StickyNote
from dashboard import NotesDashboard
from styles import THEMES
from autostart import AutostartManager

class NoteManager(QObject):
    def __init__(self, app, startup_mode=False):
        super().__init__()
        self.app = app
        self.startup_mode = startup_mode
        
        # File paths (resolved relative to script root for cross-platform reliability)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.config_file = os.path.join(self.data_dir, "config.json")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Dummy parent for taskbar hiding
        self.dummy_parent = QWidget()
        
        # Autostart Manager
        self.autostart_mgr = AutostartManager(self.base_dir)
        
        # Note collections
        self.notes = {}               # Active note window objects: {id: StickyNote}
        self.all_notes_config = {}    # All note configs (active & inactive): {id: config_dict}
        
        # Default settings config
        self.defaults_config = {
            "theme": "distinct",
            "pinned": False,
            "width": 240,
            "height": 200
        }
        
        # Load notes configuration
        self.load_all_notes()
        
        # Initialize Dashboard
        self.dashboard = NotesDashboard(self)
        
        # Initialize System Tray
        self.init_tray()
        
        # Auto-create a note if none exist at all
        if not self.all_notes_config:
            self.create_new_note(skip_show=self.startup_mode)
            
        # Set global application window icon
        self.app.setWindowIcon(self.generate_tray_icon())
        
        # Hook up focus change monitoring
        self.app.focusWindowChanged.connect(self.handle_focus_window_changed)

    def get_all_notes_config(self):
        # Update active note coordinates before returning
        for note_id, note in self.notes.items():
            self.all_notes_config[note_id] = note.get_config()
        # Sort notes by date modified if possible, or just return values
        return list(self.all_notes_config.values())

    def load_all_notes(self):
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            print("Error loading config file:", e)
            return
            
        # Load defaults if present
        if "defaults" in config_data:
            self.defaults_config.update(config_data["defaults"])
            
        notes_config = config_data.get("notes", [])
        for note_conf in notes_config:
            note_id = note_conf.get("id")
            if note_id:
                # Force active status to False if starting up in tray mode
                if self.startup_mode:
                    note_conf["active"] = False
                    
                # Add to all notes tracker
                self.all_notes_config[note_id] = note_conf
                
                # Only spawn note if it was active
                if note_conf.get("active", True):
                    # Enforce limit of 6 on startup too
                    if len(self.notes) >= 6:
                        self.all_notes_config[note_id]["active"] = False
                        continue
                        
                    note = StickyNote(parent=self.dummy_parent, note_id=note_id, manager=self)
                    note.config_changed.connect(self.save_all_config)
                    note.note_deleted.connect(self.delete_note)
                    
                    note.load_config(note_conf)
                    self.notes[note_id] = note
                    note.show()

    def save_all_config(self):
        # Synchronize active note positions
        for note_id, note in self.notes.items():
            self.all_notes_config[note_id] = note.get_config()
            
        config_data = {
            "notes": list(self.all_notes_config.values()),
            "defaults": self.defaults_config
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print("Error saving config file:", e)

    def select_distinct_theme_color(self):
        # Count theme colors used by active notes
        counts = {theme_key: 0 for theme_key in THEMES.keys()}
        for note in self.notes.values():
            if note.theme_key in counts:
                counts[note.theme_key] += 1
                
        # Choose the theme key that is least used
        least_used = min(counts, key=counts.get)
        return least_used

    def create_new_note(self, skip_show=False):
        if len(self.notes) >= 6:
            if not skip_show:
                QMessageBox.warning(
                    None, 
                    "Active Notes Limit", 
                    "You have reached the maximum limit of 6 active notes.\n"
                    "Please close or delete an existing note before spawning a new one."
                )
            return None
        # Generate time-based note_id in format ddmmyy-hhmmss
        base_id = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
        note_id = base_id
        counter = 1
        while note_id in self.all_notes_config:
            note_id = f"{base_id}_{counter}"
            counter += 1
        
        # Calculate new cascading window coordinates
        default_x, default_y = 150, 150
        offset = 25 * (len(self.notes) % 5)
        
        # Assign defaults
        theme_key = self.defaults_config.get("theme", "distinct")
        if theme_key == "distinct":
            theme_key = self.select_distinct_theme_color()
            
        pinned = self.defaults_config.get("pinned", False)
        width = self.defaults_config.get("width", 240)
        height = self.defaults_config.get("height", 200)
        
        initial_config = {
            "id": note_id,
            "theme": theme_key,
            "pinned": pinned,
            "collapsed": False,
            "view_mode": "edit",
            "active": not skip_show,
            "x": default_x + offset,
            "y": default_y + offset,
            "w": width,
            "h": height
        }
        
        self.all_notes_config[note_id] = initial_config
        
        if not skip_show:
            note = StickyNote(parent=self.dummy_parent, note_id=note_id, manager=self)
            note.config_changed.connect(self.save_all_config)
            note.note_deleted.connect(self.delete_note)
            note.load_config(initial_config)
            self.notes[note_id] = note
            note.show()
            self.save_all_config()
            return note
            
        self.save_all_config()
        return None

    def toggle_note_active(self, note_id, active):
        if active:
            # Spawning note on desktop
            if note_id in self.notes:
                return # Already active
                
            # Check limit of 6 active notes
            if len(self.notes) >= 6:
                QMessageBox.warning(
                    None, 
                    "Active Notes Limit", 
                    "You have reached the maximum limit of 6 active notes.\n"
                    "Please deactivate or delete a note to show this one."
                )
                # Refresh dashboard to restore unchecked checkbox
                self.dashboard.reload_notes()
                return
                
            # Create instance and load saved config
            note_conf = self.all_notes_config.get(note_id)
            if note_conf:
                note_conf["active"] = True
                note = StickyNote(parent=self.dummy_parent, note_id=note_id, manager=self)
                note.config_changed.connect(self.save_all_config)
                note.note_deleted.connect(self.delete_note)
                
                note.load_config(note_conf)
                self.notes[note_id] = note
                note.show()
                self.save_all_config()
        else:
            # Deactivating (closing/hiding) note from desktop
            if note_id in self.notes:
                note = self.notes.pop(note_id)
                self.all_notes_config[note_id] = note.get_config()
                self.all_notes_config[note_id]["active"] = False
                note.close() # Safely saves and hides
                self.save_all_config()

    def delete_note(self, note_id):
        # Confirm deletion
        reply = QMessageBox.question(
            None, 
            "Delete Note", 
            "Are you sure you want to permanently delete this note and its content?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 1. Close/remove active note window if open
        if note_id in self.notes:
            note = self.notes.pop(note_id)
            note.close()
            
        # 2. Remove from config lists
        if note_id in self.all_notes_config:
            self.all_notes_config.pop(note_id)
            
        # 3. Delete markdown file and its metadata file
        filepath = os.path.join(self.data_dir, "notes", f"{note_id}.md")
        meta_filepath = filepath + ".meta"
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print("Error deleting markdown file:", e)
                
        if os.path.exists(meta_filepath):
            try:
                os.remove(meta_filepath)
            except Exception as e:
                print("Error deleting metadata file:", e)
                
        self.save_all_config()

    def collapse_all_active_notes(self):
        for note in self.notes.values():
            if not note.is_collapsed:
                note.toggle_collapse()
        self.save_all_config()

    def drag_activate_note(self, note_id, global_pos):
        if not note_id:
            return
        # Spawning note on desktop and dragging it immediately
        if note_id not in self.notes:
            if len(self.notes) >= 6:
                QMessageBox.warning(
                    None, 
                    "Active Notes Limit", 
                    "You have reached the maximum limit of 6 active notes.\n"
                    "Please deactivate or delete a note before dragging this one."
                )
                self.dashboard.show()
                return
                
            note_conf = self.all_notes_config.get(note_id)
            if note_conf:
                note_conf["active"] = True
                note = StickyNote(parent=self.dummy_parent, note_id=note_id, manager=self)
                note.config_changed.connect(self.save_all_config)
                note.note_deleted.connect(self.delete_note)
                
                note.load_config(note_conf)
                self.notes[note_id] = note
        else:
            note = self.notes[note_id]
            
        note.show()
        note.raise_()
        
        # Center the titlebar of the note under the mouse cursor
        w = note.width()
        offset = QPoint(w // 2, 10)
        note.move(global_pos - offset)
        
        # Trigger system move drag
        if note.windowHandle():
            note.windowHandle().startSystemMove()
            
        self.save_all_config()

    def handle_focus_window_changed(self, window):
        focused_note_id = None
        for note_id, note in self.notes.items():
            if note.windowHandle() == window:
                focused_note_id = note_id
                break
                
        # Set focused state on all active notes
        for note_id, note in self.notes.items():
            is_focused = (note_id == focused_note_id)
            note.set_focused_state(is_focused)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.generate_tray_icon())
        self.tray_icon.setToolTip("DigiNotes Manager")
        
        # Tray Menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #F2F2F7;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)
        
        dash_action = QAction("📋 Open Dashboard", self)
        dash_action.triggered.connect(self.show_dashboard)
        menu.addAction(dash_action)
        
        new_action = QAction("📝 New Note", self)
        new_action.triggered.connect(self.create_new_note)
        menu.addAction(new_action)
        
        collapse_action = QAction("− Collapse All Active", self)
        collapse_action.triggered.connect(self.collapse_all_active_notes)
        menu.addAction(collapse_action)
        
        # Autostart option
        autostart_action = QAction("⚙ Run on System Startup", self, checkable=True)
        autostart_action.setChecked(self.autostart_mgr.is_enabled())
        autostart_action.triggered.connect(self.toggle_autostart)
        menu.addAction(autostart_action)
        
        menu.addSeparator()
        
        exit_action = QAction("❌ Exit DigiNotes", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def toggle_autostart(self, enabled):
        success = self.autostart_mgr.set_enabled(enabled)
        sender = self.sender()
        if sender and not success:
            sender.setChecked(not enabled)

    def render_icon_pixmap(self, size):
        f = size / 32.0
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Note back card (Blue theme accent)
        painter.setBrush(QColor("#0A84FF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            QRect(int(4 * f), int(4 * f), int(24 * f), int(24 * f)), 
            int(4 * f), int(4 * f)
        )
        
        # Note paper face (Sunny Yellow theme accent)
        painter.setBrush(QColor("#FDF4C8"))
        painter.drawRoundedRect(
            QRect(int(8 * f), int(8 * f), int(20 * f), int(20 * f)), 
            int(2 * f), int(2 * f)
        )
        
        # Draw lines representing text
        pen = QPen(QColor("#CA8A04"))
        pen.setWidth(max(1, int(2 * f)))
        painter.setPen(pen)
        painter.drawLine(int(12 * f), int(13 * f), int(22 * f), int(13 * f))
        painter.drawLine(int(12 * f), int(17 * f), int(22 * f), int(17 * f))
        painter.drawLine(int(12 * f), int(21 * f), int(18 * f), int(21 * f))
        
        painter.end()
        return pixmap

    def generate_tray_icon(self):
        icon = QIcon()
        icon.addPixmap(self.render_icon_pixmap(32))
        icon.addPixmap(self.render_icon_pixmap(64))
        icon.addPixmap(self.render_icon_pixmap(256))
        return icon

    def tray_icon_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.dashboard.isVisible():
                self.dashboard.hide()
            else:
                self.show_dashboard()

    def show_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def exit_app(self):
        # Save state of all notes
        for note in self.notes.values():
            note.save_note()
        # Set all notes to inactive
        for note_id in self.all_notes_config:
            self.all_notes_config[note_id]["active"] = False
        self.notes.clear()
        self.save_all_config()
        self.app.quit()


def main():
    # Lock check to enforce single instance (using user-specific suffix to avoid multi-user permission collision)
    try:
        username = getpass.getuser()
    except Exception:
        username = "default"
    lock_file = QLockFile(os.path.join(tempfile.gettempdir(), f"diginotes_{username}.lock"))
    if not lock_file.tryLock(100):
        # Start a temporary application context just to show the warning messagebox
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None, 
            "DigiNotes Already Running", 
            "An instance of DigiNotes is already running in the background.\n"
            "Please check your system tray icon to access your dashboard and notes."
        )
        sys.exit(0)
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Parse arguments
    startup_mode = "--startup" in sys.argv or "-s" in sys.argv
    
    manager = NoteManager(app, startup_mode=startup_mode)
    
    # Keep lock_file reference alive throughout execution
    app.setProperty("lock_file", lock_file)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
