# src/note_window.py

import os
import re
import uuid
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QTextBrowser, QMenu, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QAction, QColor, QTextCursor, QMouseEvent
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, QUrl

from editor import MarkdownEditor
from styles import get_theme_stylesheet, THEMES
from markdown_it import MarkdownIt

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(30)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)
        
        # Left: Color Dot Menu Button
        self.color_btn = QPushButton(self)
        self.color_btn.setFixedSize(14, 14)
        self.color_btn.setStyleSheet("""
            QPushButton {
                border-radius: 7px;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
        """)
        layout.addWidget(self.color_btn)
        
        # Title text (auto-extracted from Markdown)
        self.title_label = QLabel("Note", self)
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Action Buttons
        self.mode_btn = QPushButton("👁", self)
        self.mode_btn.setToolTip("Toggle Preview (Ctrl+P)")
        self.mode_btn.setProperty("class", "TitleBarButton")
        self.mode_btn.setFixedSize(22, 22)
        layout.addWidget(self.mode_btn)
        
        self.pin_btn = QPushButton("📌", self)
        self.pin_btn.setToolTip("Always on Top")
        self.pin_btn.setProperty("class", "TitleBarButton")
        self.pin_btn.setFixedSize(22, 22)
        layout.addWidget(self.pin_btn)
        
        self.collapse_btn = QPushButton("−", self)
        self.collapse_btn.setToolTip("Collapse to Dot")
        self.collapse_btn.setProperty("class", "TitleBarButton")
        self.collapse_btn.setFixedSize(22, 22)
        layout.addWidget(self.collapse_btn)
        
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setToolTip("Hide Note")
        self.close_btn.setProperty("class", "TitleBarButton")
        self.close_btn.setFixedSize(22, 22)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Delegate drag to Wayland compositor or OS
            window = self.window()
            if window and window.windowHandle():
                window.windowHandle().startSystemMove()
                event.accept()
            else:
                # Fallback drag initiation handled by parent
                self.parent().initiate_fallback_drag(event)


class StickyNote(QWidget):
    # Signal emitted when a note is updated or closed
    config_changed = Signal()
    note_deleted = Signal(str)

    def __init__(self, note_id=None, manager=None):
        super().__init__()
        self.manager = manager
        self.note_id = note_id or str(uuid.uuid4())
        
        # Load metadata and content
        self.data_dir = "./data"
        self.notes_dir = os.path.join(self.data_dir, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        
        self.filepath = os.path.join(self.notes_dir, f"{self.note_id}.md")
        
        # Default Settings
        self.theme_key = "yellow"
        self.is_pinned = False
        self.is_collapsed = False
        self.view_mode = "edit"  # "edit" or "render"
        self.expanded_geometry = QRect(200, 200, 300, 260)
        
        # Window attributes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(120, 80)
        
        self.init_ui()
        self.load_note()
        self.apply_theme()
        
        # Setup Autosave on text changes
        self.editor.textChanged.connect(self.save_note)
        self.editor.textChanged.connect(self.update_title)

    def init_ui(self):
        # Base shadow frame to host glassmorphism styling
        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("NoteWidget")
        
        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)  # Margin space for drop shadow
        self.main_layout.addWidget(self.main_widget)
        
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.content_layout.addWidget(self.title_bar)
        
        # Content Stack: Editor and Viewer
        self.stack = QStackedWidget(self)
        self.content_layout.addWidget(self.stack)
        
        # Page 1: Editor
        self.editor = MarkdownEditor(self, is_dark_theme=False)
        self.stack.addWidget(self.editor)
        
        # Page 2: Rendered view
        self.viewer = QTextBrowser(self)
        self.viewer.setObjectName("RenderArea")
        self.viewer.setOpenLinks(False)
        self.viewer.anchorClicked.connect(self.handle_link_click)
        self.stack.addWidget(self.viewer)
        
        # Collapsed Dot Widget
        self.dot_widget = QPushButton(self)
        self.dot_widget.setObjectName("CollapsedDot")
        self.dot_widget.setFixedSize(36, 36)
        self.dot_widget.setToolTip("Double-click to expand note")
        self.dot_widget.hide()
        
        # Connect Buttons
        self.title_bar.mode_btn.clicked.connect(self.toggle_view_mode)
        self.title_bar.pin_btn.clicked.connect(self.toggle_pinned)
        self.title_bar.collapse_btn.clicked.connect(self.toggle_collapse)
        self.title_bar.close_btn.clicked.connect(self.hide)
        self.title_bar.color_btn.clicked.connect(self.show_color_menu)
        
        # Collapsed Dot interaction
        self.dot_widget.installEventFilter(self)
        
        # Add Drop Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.main_widget.setGraphicsEffect(shadow)

    def eventFilter(self, watched, event):
        # Handle dragging and clicking of the collapsed dot
        if watched == self.dot_widget:
            if event.type() == QMouseEvent.Type.MouseButtonDblClick:
                self.toggle_collapse()
                return True
            elif event.type() == QMouseEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    window = self.window()
                    if window and window.windowHandle():
                        window.windowHandle().startSystemMove()
                        event.accept()
                    else:
                        self.initiate_fallback_drag(event)
                    return True
        return super().eventFilter(watched, event)

    def initiate_fallback_drag(self, event):
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initiate_fallback_drag(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def apply_theme(self):
        # Load theme stylesheet
        qss = get_theme_stylesheet(self.theme_key)
        self.setStyleSheet(qss)
        
        # Update Title Bar Color Dot indicator
        theme = THEMES.get(self.theme_key, THEMES["yellow"])
        self.title_bar.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['accent_color']};
                border-radius: 7px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }}
        """)
        
        # Update Editor syntax highlight colors
        is_dark = (self.theme_key == "carbon")
        self.editor.update_theme(is_dark)
        
        # Re-render viewer in case colors changed
        if self.view_mode == "render":
            self.render_markdown()

    def show_color_menu(self):
        menu = QMenu(self)
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
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        for key, theme in THEMES.items():
            action = QAction(theme["name"], self)
            # Create a closure for the theme key
            action.triggered.connect(lambda checked=False, k=key: self.set_theme(k))
            menu.addAction(action)
            
        menu.addSeparator()
        
        delete_action = QAction("🗑 Delete Note", self)
        delete_action.setStyleSheet("color: #FF453A;")
        delete_action.triggered.connect(self.confirm_delete)
        menu.addAction(delete_action)
        
        menu.exec(self.title_bar.color_btn.mapToGlobal(QPoint(0, self.title_bar.color_btn.height())))

    def set_theme(self, theme_key):
        self.theme_key = theme_key
        self.apply_theme()
        self.config_changed.emit()

    def confirm_delete(self):
        # Trigger note manager deletion
        self.note_deleted.emit(self.note_id)

    def toggle_pinned(self):
        self.is_pinned = not self.is_pinned
        self.apply_pinned_state()
        self.config_changed.emit()

    def apply_pinned_state(self):
        flags = self.windowFlags()
        if self.is_pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.title_bar.pin_btn.setText("📌")
            self.title_bar.pin_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
            self.title_bar.pin_btn.setText("📍")
            self.title_bar.pin_btn.setStyleSheet("")
            
        self.setWindowFlags(flags)
        self.show()

    def toggle_view_mode(self):
        if self.view_mode == "edit":
            self.view_mode = "render"
            self.title_bar.mode_btn.setText("✏")
            self.title_bar.mode_btn.setToolTip("Edit Note (Ctrl+P)")
            self.render_markdown()
            self.stack.setCurrentIndex(1)
        else:
            self.view_mode = "edit"
            self.title_bar.mode_btn.setText("👁")
            self.title_bar.mode_btn.setToolTip("Preview Note (Ctrl+P)")
            self.stack.setCurrentIndex(0)
            self.editor.setFocus()
        self.config_changed.emit()

    def render_markdown(self):
        raw_text = self.editor.toPlainText()
        theme = THEMES.get(self.theme_key, THEMES["yellow"])
        
        # Render HTML
        html = self.get_rendered_html(raw_text, theme["text_color"], theme["accent_color"])
        self.viewer.setHtml(html)

    def get_rendered_html(self, markdown_text, text_color, accent_color):
        # Preprocess Markdown Checkboxes into clickable anchors
        lines = markdown_text.split('\n')
        checkbox_idx = 0
        processed_lines = []
        
        for line in lines:
            # Matches "- [ ] " or "* [ ] "
            match_unchecked = re.match(r'^(\s*[\-\*]\s+)\[\s\](.*)', line)
            # Matches "- [x] " or "* [x] "
            match_checked = re.match(r'^(\s*[\-\*]\s+)\[[xX]\](.*)', line)
            
            if match_unchecked:
                prefix, rest = match_unchecked.groups()
                line = f"{prefix}<a href='toggle:{checkbox_idx}' style='text-decoration:none; color:{text_color}; font-family: monospace; font-size:16px;'>☐</a> {rest}"
                checkbox_idx += 1
            elif match_checked:
                prefix, rest = match_checked.groups()
                line = f"{prefix}<a href='toggle:{checkbox_idx}' style='text-decoration:none; color:{accent_color}; font-family: monospace; font-size:16px;'>☑</a> <span style='text-decoration: line-through; opacity: 0.6;'>{rest}</span>"
                checkbox_idx += 1
                
            processed_lines.append(line)
            
        processed_md = '\n'.join(processed_lines)
        
        # Render markdown to HTML
        md = MarkdownIt("commonmark")
        html_body = md.render(processed_md)
        
        # Wrap HTML with layout stylesheet matching the selected theme style
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{
                color: {text_color};
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
                font-size: 13.5px;
                line-height: 1.5;
                margin: 8px 12px;
            }}
            p {{ margin: 0 0 8px 0; }}
            a {{
                color: {accent_color};
                text-decoration: none;
            }}
            h1, h2, h3, h4 {{
                margin: 12px 0 6px 0;
                font-weight: bold;
                color: {accent_color};
            }}
            h1 {{ font-size: 16px; border-bottom: 1px solid rgba(0,0,0,0.08); padding-bottom: 2px; }}
            h2 {{ font-size: 14px; }}
            h3 {{ font-size: 13px; }}
            code {{
                font-family: 'Courier New', monospace;
                background-color: rgba(120, 120, 120, 0.12);
                padding: 1px 4px;
                border-radius: 3px;
                font-size: 12px;
            }}
            pre {{
                background-color: rgba(120, 120, 120, 0.12);
                padding: 6px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            ul, ol {{
                margin: 0 0 8px 0;
                padding-left: 20px;
            }}
            li {{ margin-bottom: 2px; }}
        </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        return styled_html

    def handle_link_click(self, url):
        url_str = url.toString()
        if url_str.startswith("toggle:"):
            try:
                idx = int(url_str.split(":")[1])
                self.toggle_checkbox_at_index(idx)
            except Exception as e:
                print("Error toggling checkbox:", e)

    def toggle_checkbox_at_index(self, index_to_toggle):
        markdown_text = self.editor.toPlainText()
        pattern = re.compile(r'(\[\s\]|\[[xX]\])')
        matches = list(pattern.finditer(markdown_text))
        
        if 0 <= index_to_toggle < len(matches):
            match = matches[index_to_toggle]
            start, end = match.span()
            current_val = match.group(1)
            
            new_val = "[x]" if current_val == "[ ]" else "[ ]"
            
            new_text = markdown_text[:start] + new_val + markdown_text[end:]
            
            # Update Editor text, which saves the file and updates viewer
            self.editor.setPlainText(new_text)
            self.render_markdown()

    def toggle_collapse(self):
        if not self.is_collapsed:
            # Collapse to Dot
            self.expanded_geometry = self.geometry()
            self.is_collapsed = True
            
            # Hide main elements
            self.main_widget.hide()
            
            # Remove margin space for the dot view
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            
            # Show dot and style the window frame to be tiny (transparent wrap)
            self.main_layout.removeWidget(self.main_widget)
            self.main_layout.addWidget(self.dot_widget)
            
            # Set the dot background color matching the accent
            theme = THEMES.get(self.theme_key, THEMES["yellow"])
            self.dot_widget.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['accent_color']};
                    border: 2px solid white;
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {theme['border_color']};
                }}
            """)
            
            self.dot_widget.show()
            self.resize(36, 36)
        else:
            # Expand to Note window
            self.is_collapsed = False
            
            # Hide dot
            self.dot_widget.hide()
            self.main_layout.removeWidget(self.dot_widget)
            
            # Restore margins for note frame and shadow
            self.main_layout.setContentsMargins(8, 8, 8, 8)
            
            # Show note frame
            self.main_layout.addWidget(self.main_widget)
            self.main_widget.show()
            
            # Restore previous expanded sizing
            self.setGeometry(self.expanded_geometry)
            
        self.config_changed.emit()

    def update_title(self):
        # Auto-extract title from the first header or first line
        raw_text = self.editor.toPlainText().strip()
        if not raw_text:
            self.title_bar.title_label.setText("Note")
            return
            
        first_line = raw_text.split("\n")[0]
        # Strip Markdown header markings like #, ##, etc.
        clean_title = re.sub(r'^#+\s*', '', first_line).strip()
        # Truncate if too long
        if len(clean_title) > 20:
            clean_title = clean_title[:18] + "..."
            
        self.title_bar.title_label.setText(clean_title or "Note")

    def load_note(self):
        # Load markdown note file contents
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.update_title()

    def save_note(self):
        # Write markdown text contents to file
        content = self.editor.toPlainText()
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def load_config(self, config_dict):
        # Hydrate note coordinates and state
        self.theme_key = config_dict.get("theme", "yellow")
        self.is_pinned = config_dict.get("pinned", False)
        self.is_collapsed = config_dict.get("collapsed", False)
        self.view_mode = config_dict.get("view_mode", "edit")
        
        x = config_dict.get("x", 200)
        y = config_dict.get("y", 200)
        w = config_dict.get("w", 300)
        h = config_dict.get("h", 260)
        
        self.expanded_geometry = QRect(x, y, w, h)
        
        # Apply configurations
        self.apply_theme()
        self.apply_pinned_state()
        
        # Sync views
        if self.view_mode == "render":
            self.view_mode = "edit"  # toggle_view_mode will switch it to render
            self.toggle_view_mode()
        else:
            self.stack.setCurrentIndex(0)
            
        # Apply collapsed state
        if self.is_collapsed:
            self.is_collapsed = False  # toggle_collapse will invert this
            self.toggle_collapse()
            # Move the dot window to the center of where the note was
            center_x = x + w // 2 - 18
            center_y = y + h // 2 - 18
            self.move(center_x, center_y)
        else:
            self.setGeometry(self.expanded_geometry)

    def get_config(self):
        # Return note geometry and properties configuration dict
        geom = self.expanded_geometry if not self.is_collapsed else self.expanded_geometry
        current_geom = self.geometry()
        
        # If expanded, save current position, otherwise keep the saved expanded geometry
        if not self.is_collapsed:
            x, y, w, h = current_geom.x(), current_geom.y(), current_geom.width(), current_geom.height()
        else:
            x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            
        return {
            "id": self.note_id,
            "theme": self.theme_key,
            "pinned": self.is_pinned,
            "collapsed": self.is_collapsed,
            "view_mode": self.view_mode,
            "x": x,
            "y": y,
            "w": w,
            "h": h
        }

    def keyPressEvent(self, event):
        # Capture shortcuts
        # Ctrl+P toggles View/Edit Mode
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_P:
            self.toggle_view_mode()
            event.accept()
            return
            
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.save_note()
        self.config_changed.emit()
        super().closeEvent(event)
