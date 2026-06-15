# src/main.py

import os
import sys
import json
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QAction
from PySide6.QtCore import QObject, Qt, QRect

from note_window import StickyNote

class NoteManager(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        # Paths
        self.data_dir = "./data"
        self.config_file = os.path.join(self.data_dir, "config.json")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.notes = {}  # dict of active StickyNote windows keyed by note_id
        
        # Setup System Tray
        self.init_tray()
        
        # Load and restore saved notes
        self.load_all_notes()
        
        # If no notes exist, create a blank starter note
        if not self.notes:
            self.create_new_note()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.generate_tray_icon())
        self.tray_icon.setToolTip("DotNotes - Sticky Notes")
        
        # Context Menu
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #F2F2F7;
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 122, 255, 0.7);
                color: white;
            }
        """)
        
        new_note_action = QAction("📝 New Note", self)
        new_note_action.triggered.connect(self.create_new_note)
        self.tray_menu.addAction(new_note_action)
        
        show_all_action = QAction("👁 Show All", self)
        show_all_action.triggered.connect(self.show_all_notes)
        self.tray_menu.addAction(show_all_action)
        
        hide_all_action = QAction("🙈 Hide All", self)
        hide_all_action.triggered.connect(self.hide_all_notes)
        self.tray_menu.addAction(hide_all_action)
        
        self.tray_menu.addSeparator()
        
        exit_action = QAction("🚪 Exit", self)
        exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Click on icon opens new note or restores all
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def generate_tray_icon(self):
        # Dynamically draw a premium notebook icon using QPainter
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Outer cover (Blue)
        painter.setBrush(QColor("#007AFF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRect(2, 2, 28, 28), 6, 6)
        
        # Inner page (Yellow)
        painter.setBrush(QColor("#FED700"))
        painter.drawRoundedRect(QRect(6, 6, 20, 20), 4, 4)
        
        # Lines representing written text (Dark Gray)
        painter.setPen(QPen(QColor("#2C2C2E"), 1.5))
        painter.drawLine(10, 11, 22, 11)
        painter.drawLine(10, 15, 22, 15)
        painter.drawLine(10, 19, 18, 19)
        
        painter.end()
        return QIcon(pixmap)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_all_notes()

    def create_new_note(self):
        note = StickyNote(manager=self)
        
        # Position slightly offset if there are already active notes
        if self.notes:
            active_notes = list(self.notes.values())
            # Find the bottom-rightmost coordinate of active notes
            max_x = max(n.x() for n in active_notes)
            max_y = max(n.y() for n in active_notes)
            
            # Position new note with cascade offset, keeping it on screen limits
            new_x = (max_x + 25) % (self.app.primaryScreen().size().width() - 320)
            new_y = (max_y + 25) % (self.app.primaryScreen().size().height() - 300)
            
            note.move(new_x, new_y)
            # Update expanded geom position
            note.expanded_geometry.moveTo(new_x, new_y)
            
        note.config_changed.connect(self.save_all_config)
        note.note_deleted.connect(self.delete_note)
        
        self.notes[note.note_id] = note
        note.show()
        self.save_all_config()
        return note

    def delete_note(self, note_id):
        # Prompt verification dialog
        reply = QMessageBox.question(
            None, 
            "Delete Note", 
            "Are you sure you want to permanently delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            note = self.notes.pop(note_id, None)
            if note:
                note.close()
                # Delete markdown file
                if os.path.exists(note.filepath):
                    try:
                        os.remove(note.filepath)
                    except Exception as e:
                        print("Error deleting note file:", e)
                        
                # Update config
                self.save_all_config()
                
                # If zero notes left, spawn a blank one
                if not self.notes:
                    self.create_new_note()

    def show_all_notes(self):
        for note in self.notes.values():
            note.show()
            note.raise_()

    def hide_all_notes(self):
        for note in self.notes.values():
            note.hide()

    def save_all_config(self):
        config_data = {
            "notes": [note.get_config() for note in self.notes.values()]
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print("Error saving config file:", e)

    def load_all_notes(self):
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            print("Error loading config file:", e)
            return
            
        notes_config = config_data.get("notes", [])
        for note_conf in notes_config:
            note_id = note_conf.get("id")
            if note_id:
                note = StickyNote(note_id=note_id, manager=self)
                note.config_changed.connect(self.save_all_config)
                note.note_deleted.connect(self.delete_note)
                
                note.load_config(note_conf)
                self.notes[note_id] = note
                note.show()

    def exit_app(self):
        # Save state of all notes
        for note in self.notes.values():
            note.save_note()
        self.save_all_config()
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    
    # Crucial: Prevent app from terminating when all windows are closed/hidden
    # This allows it to reside in the System Tray
    app.setQuitOnLastWindowClosed(False)
    
    # Initialize Note Manager
    manager = NoteManager(app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
