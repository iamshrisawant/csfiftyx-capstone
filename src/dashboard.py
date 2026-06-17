# src/dashboard.py

import os
import re
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton, QGraphicsDropShadowEffect,
    QApplication
)
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QObject, QEvent

from styles import get_dashboard_stylesheet, THEMES

class NoteListItemWidget(QWidget):
    delete_triggered = Signal(str)

    def __init__(self, note_id, note_data, notes_dir, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.note_data = note_data
        self.is_active = note_data.get("active", True)
        
        # Read file contents for preview
        self.notes_dir = notes_dir
        self.filepath = os.path.join(self.notes_dir, f"{note_id}.md")
        self.title_text = "Empty Note"
        self.mtime_str = ""
        self.load_note_preview()
        
        self.init_ui()

    def load_note_preview(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    lines = content.split('\n')
                    first_line = lines[0]
                    self.title_text = re.sub(r'^#+\s*', '', first_line).strip() or "Untitled"
                else:
                    self.title_text = "Untitled Note"
                
                # Get modified time
                mtime = os.path.getmtime(self.filepath)
                dt = datetime.datetime.fromtimestamp(mtime)
                self.mtime_str = dt.strftime("%b %d, %H:%M")
            except Exception as e:
                print("Error loading preview:", e)

    def init_ui(self):
        self.setObjectName("NoteListItemWidget")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Color dot indicator
        theme_key = self.note_data.get("theme", "yellow")
        theme_color = THEMES.get(theme_key, THEMES["yellow"])["accent_color"]
        
        self.dot = QWidget(self)
        self.dot.setFixedSize(8, 8)
        self.dot.setStyleSheet(f"""
            background-color: {theme_color};
            border-radius: 4px;
        """)
        self.dot.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Text layout (Title and subtitle/time status)
        text_widget = QWidget(self)
        text_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        title_lbl = QLabel(self.title_text, self)
        title_lbl.setProperty("class", "ItemTitle")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)
        
        status_text = "Active" if self.is_active else "Inactive"
        status_color = "#30D158" if self.is_active else "#AEAEB2"
        
        subtitle_lbl = QLabel(self)
        subtitle_lbl.setProperty("class", "ItemSubtitle")
        subtitle_lbl.setText(f"<html>{self.mtime_str} &nbsp;•&nbsp; <span style='color:{status_color}; font-weight:500;'>{status_text}</span></html>")
        subtitle_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(subtitle_lbl)
        
        layout.addWidget(text_widget, 1)
        
        # Delete button
        self.del_btn = QPushButton("🗑", self)
        self.del_btn.setProperty("class", "ItemDeleteButton")
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.setToolTip("Permanently Delete Note")
        self.del_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.del_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def on_delete_clicked(self):
        self.delete_triggered.emit(self.note_id)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dashboard = self.window()
            if hasattr(dashboard, 'toggle_note'):
                dashboard.toggle_note(self.note_id)
            event.accept()
        else:
            super().mousePressEvent(event)


class DashboardEventFilter(QObject):
    def __init__(self, dashboard):
        super().__init__(dashboard)
        self.dashboard = dashboard
        self.drag_start_pos = None
        self.drag_item = None
        self.drag_note_id = None
        self.drag_triggered = False

    def eventFilter(self, watched, event):
        if watched == self.dashboard.list_widget:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_start_pos = event.position().toPoint()
                    item = self.dashboard.list_widget.itemAt(self.drag_start_pos)
                    if item:
                        self.drag_item = item
                        widget = self.dashboard.list_widget.itemWidget(item)
                        if widget:
                            self.drag_note_id = widget.note_id
                        self.drag_triggered = False
                    else:
                        self.drag_item = None
                        self.drag_note_id = None
                        self.drag_triggered = False
                        
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton and self.drag_item and not self.drag_triggered:
                    dist = (event.position().toPoint() - self.drag_start_pos).manhattanLength()
                    if dist > QApplication.startDragDistance():
                        self.drag_triggered = True
                        self.dashboard.hide()
                        self.dashboard.manager.drag_activate_note(self.drag_note_id, event.globalPosition().toPoint())
                        self.drag_item = None
                        self.drag_note_id = None
                        return True
                        
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_item = None
                self.drag_note_id = None
                self.drag_triggered = False
                
        return super().eventFilter(watched, event)


class NotesDashboard(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        # Resolve path relative to script root for cross-platform reliability
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.notes_dir = os.path.join(base_dir, "data", "notes")
        
        # Window configuration - Compact Sidebar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(320, 460)
        self.resize(320, 520)
        
        self.settings_dialog = None
        self.init_ui()
        self.setStyleSheet(get_dashboard_stylesheet())
        self.setWindowIcon(self.manager.generate_tray_icon())
        
        # Center on screen initially
        screen_geo = self.manager.app.primaryScreen().geometry()
        x = (screen_geo.width() - self.width()) // 2
        y = (screen_geo.height() - self.height()) // 2
        self.move(x, y)

    def init_ui(self):
        # Base glassmorphic panel
        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("DashboardWidget")
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(16)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow.setOffset(0, 6)
        self.main_widget.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.main_widget)
        
        # Internal elements layout
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)
        
        # 1. Custom Title Handle
        title_bar = QWidget(self)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("DigiNotes Dashboard", self)
        title_lbl.setObjectName("DashboardTitle")
        title_bar_layout.addWidget(title_lbl)
        
        title_bar_layout.addStretch()
        
        self.new_btn = QPushButton("+", self)
        self.new_btn.setFixedSize(20, 20)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8E8E93;
                border: none;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        self.new_btn.clicked.connect(self.create_note_clicked)
        title_bar_layout.addWidget(self.new_btn)
        
        self.settings_btn = QPushButton("⚙", self)
        self.settings_btn.setFixedSize(20, 20)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8E8E93;
                border: none;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        self.settings_btn.clicked.connect(self.open_settings)
        title_bar_layout.addWidget(self.settings_btn)

        self.close_btn = QPushButton("×", self)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8E8E93;
                border: none;
                font-size: 15px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        title_bar_layout.addWidget(self.close_btn)
        
        content_layout.addWidget(title_bar)
        
        # Title bar dragging support with fallback
        title_bar.mousePressEvent = self.title_press
        title_bar.mouseMoveEvent = self.title_move
        title_bar.mouseReleaseEvent = self.title_release
        
        # 2. Search Box
        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("🔍 Search notes...")
        self.search_bar.textChanged.connect(self.filter_notes)
        content_layout.addWidget(self.search_bar)
        
        # 3. Notes List Widget
        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("NotesList")
        content_layout.addWidget(self.list_widget)
        
        # Event filter for drag and drop
        self.drag_filter = DashboardEventFilter(self)
        self.list_widget.installEventFilter(self.drag_filter)

    def toggle_note(self, note_id):
        # Find the note config to toggle its active status
        for note_data in self.manager.get_all_notes_config():
            if note_data.get("id") == note_id:
                self.manager.toggle_note_active(note_id, not note_data.get("active", True))
                self.reload_notes()
                break

    def create_note_clicked(self):
        self.manager.create_new_note()
        self.reload_notes()

    def open_settings(self):
        from settings import SettingsDialog
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.manager, parent=None)
        self.settings_dialog.populate_note_selector()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.title_drag_start = event.globalPosition().toPoint()
            event.accept()

    def title_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'title_drag_start'):
            dist = (event.globalPosition().toPoint() - self.title_drag_start).manhattanLength()
            if dist > 3:
                window = self.window()
                moved = False
                if window and window.windowHandle():
                    moved = window.windowHandle().startSystemMove()
                if not moved:
                    # Fallback to manual window moving
                    delta = event.globalPosition().toPoint() - self.title_drag_start
                    window.move(window.pos() + delta)
                    self.title_drag_start = event.globalPosition().toPoint()
            event.accept()

    def title_release(self, event):
        if hasattr(self, 'title_drag_start'):
            delattr(self, 'title_drag_start')
        event.accept()

    def showEvent(self, event):
        self.reload_notes()
        self.search_bar.clear()
        super().showEvent(event)

    def reload_notes(self):
        self.list_widget.clear()
        notes_config = self.manager.get_all_notes_config()
        
        for note_data in notes_config:
            note_id = note_data.get("id")
            if not note_id:
                continue
                
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(100, 54))
            
            row_widget = NoteListItemWidget(note_id, note_data, self.notes_dir, self)
            row_widget.delete_triggered.connect(self.handle_delete_triggered)
            
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row_widget)
            
        if hasattr(self, 'settings_dialog') and self.settings_dialog and self.settings_dialog.isVisible():
            self.settings_dialog.populate_note_selector()

    def filter_notes(self, query):
        query = query.lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                match = (query in widget.title_text.lower())
                item.setHidden(not match)

    def handle_delete_triggered(self, note_id):
        self.manager.delete_note(note_id)
        self.reload_notes()
