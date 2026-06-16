# src/note_window.py

import os
import re
import uuid
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QGraphicsDropShadowEffect, QApplication, QMenu, QFrame, QLabel, QScrollArea
)
from PySide6.QtGui import QAction, QColor, QTextCursor, QMouseEvent
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, QPropertyAnimation, QEasingCurve

from editor import MarkdownEditor
from styles import get_theme_stylesheet, THEMES

class MarkdownHelpOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpOverlay")
        self.setStyleSheet("""
            #HelpOverlay {
                background-color: rgba(20, 20, 20, 0.98);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
            QLabel {
                color: #F2F2F7;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(6)
        
        # Header Row
        header_layout = QHBoxLayout()
        title = QLabel("📝 Formatting Guide", self)
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0A84FF;")
        header_layout.addWidget(title)
        
        close_btn = QPushButton("×", self)
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #AEAEB2;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF453A;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        main_layout.addLayout(header_layout)
        
        # Scroll Area for guide content
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.25);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 4, 0)
        scroll_layout.setSpacing(8)
        
        help_sections = [
            ("Headers", "# Heading 1\n## Heading 2\n### Heading 3\n#### Heading 4\n##### Heading 5"),
            ("Text Styles", "**Bold** / __Bold__\n*Italic* / _Italic_\n<u>Underline</u>\n~~Strike-through~~\n==Highlight tag=="),
            ("Checklists", "- [ ] Unchecked Task\n- [x] Completed Task"),
            ("Lists", "- Bullet Point\n1. Numbered Item"),
            ("Blockquotes & Lines", "> Blockquote text\n--- (3 dashes) Divider line"),
            ("Code & Math", "`inline code`\n$$ LaTeX Math $$"),
            ("Links", "[label](url) link")
        ]
        
        for sec_title, sec_content in help_sections:
            sec_lbl = QLabel(f"<b>{sec_title}</b>", self)
            sec_lbl.setStyleSheet("font-size: 11px; color: #AEAEB2;")
            scroll_layout.addWidget(sec_lbl)
            
            content_lbl = QLabel(sec_content, self)
            content_lbl.setStyleSheet("font-size: 10px; color: #30D158; font-family: 'Courier New'; line-height: 1.4;")
            content_lbl.setWordWrap(True)
            scroll_layout.addWidget(content_lbl)
            
            # Divider line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); max-height: 1px;")
            scroll_layout.addWidget(line)
            
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        self.hide()


class TitleBar(QWidget):
    def __init__(self, note, parent=None):
        super().__init__(parent or note)
        self.note = note
        self.setObjectName("TitleBar")
        self.setFixedHeight(20)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(3)
        
        # Left: Color Dot Collapse Button
        self.color_btn = QPushButton(self)
        self.color_btn.setFixedSize(12, 12)
        self.color_btn.setToolTip("Toggle collapse note")
        layout.addWidget(self.color_btn)
        
        layout.addStretch()
        
        # Right Actions
        self.settings_btn = QPushButton("⚙", self)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setProperty("class", "TitleBarButton")
        self.settings_btn.setFixedSize(16, 16)
        layout.addWidget(self.settings_btn)
        
        self.pin_btn = QPushButton("📍", self)
        self.pin_btn.setToolTip("Lock position & collapse state")
        self.pin_btn.setProperty("class", "TitleBarButton")
        self.pin_btn.setFixedSize(16, 16)
        layout.addWidget(self.pin_btn)
        
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setToolTip("Hide Note")
        self.close_btn.setProperty("class", "TitleBarButton")
        self.close_btn.setFixedSize(16, 16)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if self.note.is_pinned:
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.note.is_pinned:
            event.ignore()
            return
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_start_pos'):
            dist = (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength()
            if dist > 3:
                window = self.window()
                if window.windowHandle():
                    window.windowHandle().startSystemMove()
                delattr(self, 'drag_start_pos')
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_start_pos'):
            delattr(self, 'drag_start_pos')
        super().mouseReleaseEvent(event)


class StickyNote(QWidget):
    config_changed = Signal()
    note_deleted = Signal(str)

    def __init__(self, parent=None, note_id=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.note_id = note_id or str(uuid.uuid4())
        
        # Storage
        self.data_dir = "./data"
        self.notes_dir = os.path.join(self.data_dir, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        self.filepath = os.path.join(self.notes_dir, f"{self.note_id}.md")
        
        # Default Settings
        self.theme_key = "yellow"
        self.is_pinned = False
        self.is_collapsed = False
        self.expanded_geometry = QRect(200, 200, 240, 200)
        
        self.opacity_anim = None
        self.geom_anim = None
        self.is_focused = False
        
        # Window attributes
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 80)
        
        self.init_ui()
        self.load_note()
        self.apply_theme()
        
        # Autosave setup
        self.editor.textChanged.connect(self.save_note)
        
        # 1. Force the Window Manager to recognize the Always-on-Top hint
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        
        # 2. Tell the OS to update the window behavior immediately
        self.show()
    def init_ui(self):
        # Base frame
        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("NoteWidget")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.addWidget(self.main_widget)
        
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.content_layout.addWidget(self.title_bar)
        
        # Editor
        self.editor = MarkdownEditor(self)
        self.content_layout.addWidget(self.editor)
        
        # Help Overlay Guide
        self.help_overlay = MarkdownHelpOverlay(self)
        
        # Collapsed Dot Button
        self.dot_widget = QPushButton(self)
        self.dot_widget.setObjectName("CollapsedDot")
        self.dot_widget.setFixedSize(20, 20)
        self.dot_widget.setToolTip("Click to expand note")
        self.dot_widget.hide()
        
        # Connect Controls
        self.title_bar.pin_btn.clicked.connect(self.toggle_pinned)
        self.title_bar.close_btn.clicked.connect(self.deactivate)
        self.title_bar.color_btn.clicked.connect(self.toggle_collapse)
        self.title_bar.settings_btn.clicked.connect(self.show_settings_menu)
        
        self.dot_widget.installEventFilter(self)
        
        # Graphics effect shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(0, 3)
        self.main_widget.setGraphicsEffect(self.shadow)

    def showEvent(self, event):
        super().showEvent(event)
        self.reinforce_stays_on_top()

    def reinforce_stays_on_top(self):
        self.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Cover the entire note area (margins of note window are 8px)
        self.help_overlay.setGeometry(8, 8, self.width() - 16, self.height() - 16)

    # Hover & Focus opacity controls
    def enterEvent(self, event):
        self.apply_theme_state(is_hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.apply_theme_state(is_hovered=self.is_focused)
        super().leaveEvent(event)

    def set_focused_state(self, is_focused):
        self.is_focused = is_focused
        self.apply_theme_state(self.underMouse() or self.is_focused)
        self.reinforce_stays_on_top()

    def apply_theme_state(self, is_hovered):
        if self.is_collapsed:
            theme = THEMES.get(self.theme_key, THEMES["yellow"])
            hex_color = theme['accent_color'].lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            alpha = 240 if is_hovered else 90
            hover_alpha = 240
            
            self.dot_widget.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {alpha});
                    border: 1px solid rgba(255, 255, 255, 0.75);
                    border-radius: 6px;
                    width: 12px;
                    height: 12px;
                    margin: 3px;
                }}
                QPushButton:hover {{
                    background-color: rgba({r}, {g}, {b}, {hover_alpha});
                    border-color: white;
                }}
            """)
        else:
            qss = get_theme_stylesheet(self.theme_key, is_hovered=is_hovered)
            self.setStyleSheet(qss)
            
            theme = THEMES.get(self.theme_key, THEMES["yellow"])
            self.title_bar.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['accent_color']};
                    border-radius: 6px;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                }}
            """)

    def eventFilter(self, watched, event):
        if watched == self.dot_widget:
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.dot_drag_start = event.globalPosition().toPoint()
                    self.dot_drag_triggered = False
                    return True
            elif event.type() == QMouseEvent.Type.MouseMove:
                if hasattr(self, 'dot_drag_start'):
                    dist = (event.globalPosition().toPoint() - self.dot_drag_start).manhattanLength()
                    if dist > 3:
                        self.dot_drag_triggered = True
                        if self.windowHandle():
                            self.windowHandle().startSystemMove()
                        delattr(self, 'dot_drag_start')
                    return True
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    if hasattr(self, 'dot_drag_start'):
                        delattr(self, 'dot_drag_start')
                    if not self.dot_drag_triggered:
                        self.toggle_collapse()
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if self.is_pinned:
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_pinned:
            event.ignore()
            return
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_start_pos'):
            dist = (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength()
            if dist > 3:
                if self.windowHandle():
                    self.windowHandle().startSystemMove()
                delattr(self, 'drag_start_pos')
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_start_pos'):
            delattr(self, 'drag_start_pos')
        super().mouseReleaseEvent(event)

    def apply_theme(self):
        self.apply_theme_state(is_hovered=self.underMouse() or self.is_focused)

    def show_settings_menu(self):
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
        
        theme_menu = menu.addMenu("🎨 Themes")
        theme_menu.setStyleSheet(menu.styleSheet())
        for key, theme in THEMES.items():
            action = QAction(theme["name"], self)
            action.triggered.connect(lambda checked=False, k=key: self.set_theme(k))
            theme_menu.addAction(action)
            
        menu.addSeparator()
        
        help_action = QAction("❓ Markdown Guide", self)
        help_action.triggered.connect(self.show_help_overlay)
        menu.addAction(help_action)
        
        menu.exec(self.title_bar.settings_btn.mapToGlobal(QPoint(0, self.title_bar.settings_btn.height())))

    def show_help_overlay(self):
        self.help_overlay.show()
        self.help_overlay.raise_()

    def set_theme(self, theme_key):
        self.theme_key = theme_key
        self.apply_theme()
        self.config_changed.emit()

    def toggle_pinned(self):
        self.is_pinned = not self.is_pinned
        self.apply_pinned_state()
        self.config_changed.emit()

    def apply_pinned_state(self):
        if self.is_pinned:
            self.title_bar.pin_btn.setText("📌")
            self.title_bar.pin_btn.setToolTip("Locked (Click to Unlock)")
            self.title_bar.pin_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        else:
            self.title_bar.pin_btn.setText("📍")
            self.title_bar.pin_btn.setToolTip("Unlocked (Click to Lock)")
            self.title_bar.pin_btn.setStyleSheet("")

    def toggle_collapse(self):
        if self.is_pinned:
            return
            
        if self.geom_anim and self.geom_anim.state() == QPropertyAnimation.State.Running:
            return
            
        if not self.is_collapsed:
            # Collapse to Dot
            self.expanded_geometry = self.geometry()
            self.is_collapsed = True
            
            center = self.geometry().center()
            target_rect = QRect(center.x() - 10, center.y() - 10, 20, 20)
            
            self.main_widget.hide()
            self.main_layout.removeWidget(self.main_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.addWidget(self.dot_widget)
            self.dot_widget.show()
            
            self.apply_theme_state(is_hovered=False)
            self.animate_transition(target_rect, is_expanding=False)
        else:
            # Expand to Note
            self.is_collapsed = False
            self.dot_widget.hide()
            self.main_layout.removeWidget(self.dot_widget)
            
            self.main_layout.setContentsMargins(8, 8, 8, 8)
            self.main_layout.addWidget(self.main_widget)
            self.main_widget.show()
            
            self.apply_theme_state(is_hovered=True)
            self.animate_transition(self.expanded_geometry, is_expanding=True)

    def animate_transition(self, target_rect, is_expanding=True):
        self.geom_anim = QPropertyAnimation(self, b"geometry")
        if is_expanding:
            self.geom_anim.setDuration(250)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        else:
            self.geom_anim.setDuration(200)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.InQuad)
            
        self.geom_anim.setStartValue(self.geometry())
        self.geom_anim.setEndValue(target_rect)
        self.geom_anim.finished.connect(self.reinforce_stays_on_top)
        self.geom_anim.start()

    def deactivate(self):
        self.hide()
        self.config_changed.emit()

    def load_note(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setPlainText(content)
                self.load_metadata()
            except Exception as e:
                print("Error loading note file:", e)

    def save_note(self):
        content = self.editor.toPlainText()
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.save_metadata()
        except Exception as e:
            print("Error saving note file:", e)

    def load_config(self, conf):
        self.theme_key = conf.get("theme", "yellow")
        self.is_pinned = conf.get("pinned", False)
        self.is_collapsed = conf.get("collapsed", False)
        
        x = conf.get("x", 200)
        y = conf.get("y", 200)
        w = conf.get("w", 240)
        h = conf.get("h", 200)
        self.expanded_geometry = QRect(x, y, w, h)
        
        if self.is_collapsed:
            center = self.expanded_geometry.center()
            self.setGeometry(QRect(center.x() - 10, center.y() - 10, 20, 20))
            self.main_widget.hide()
            self.main_layout.removeWidget(self.main_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.addWidget(self.dot_widget)
            self.dot_widget.show()
        else:
            self.setGeometry(self.expanded_geometry)
            
        self.apply_pinned_state()
        self.apply_theme()

    def get_config(self):
        if not self.is_collapsed:
            self.expanded_geometry = self.geometry()
            
        return {
            "id": self.note_id,
            "theme": self.theme_key,
            "pinned": self.is_pinned,
            "collapsed": self.is_collapsed,
            "active": self.isVisible(),
            "x": self.expanded_geometry.x(),
            "y": self.expanded_geometry.y(),
            "w": self.expanded_geometry.width(),
            "h": self.expanded_geometry.height()
        }

    def load_metadata(self):
        meta_path = self.filepath + ".meta"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                self.load_config(meta)
            except Exception as e:
                print("Error loading note metadata:", e)

    def save_metadata(self):
        meta_path = self.filepath + ".meta"
        try:
            meta = self.get_config()
            with open(meta_path, 'w') as f:
                json.dump(meta, f)
        except Exception as e:
            print("Error saving note metadata:", e)
