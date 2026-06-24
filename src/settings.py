# src/settings.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QComboBox, QSpinBox, QPushButton, QTabWidget, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from styles import THEMES

class SettingsDialog(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        
        # Window configuration
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(360, 420)
        self.resize(360, 420)
        
        self.drag_start_pos = None
        self.init_ui()
        self.load_defaults()
        self.setWindowIcon(self.manager.generate_tray_icon())
        
        # Center relative to dashboard
        if self.manager.dashboard:
            geo = self.manager.dashboard.geometry()
            self.move(geo.x() + 40, geo.y() + 40)

    def init_ui(self):
        # Base glassmorphic panel
        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("SettingsWidget")
        
        # Style sheet to match glassmorphic premium design
        self.main_widget.setStyleSheet("""
            #SettingsWidget {
                background-color: rgba(30, 30, 30, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
            QLabel {
                color: #F2F2F7;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
            }
            #SettingsTitle {
                font-size: 15px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: transparent;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #AEAEB2;
                padding: 6px 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
                font-weight: bold;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #FFFFFF;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: rgba(255, 255, 255, 0.12);
            }
            QSpinBox {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #FFFFFF;
                padding: 4px;
                font-size: 12px;
            }
            QCheckBox {
                color: #F2F2F7;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0A84FF;
                border: none;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0070E0;
            }
            QPushButton#CloseButton {
                background: transparent;
                color: #8E8E93;
                font-size: 15px;
                font-weight: bold;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton#CloseButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 8)
        self.main_widget.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.main_widget)
        
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(12)
        
        # Title Bar
        title_bar = QWidget(self)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("DigiNotes Settings", self)
        title_lbl.setObjectName("SettingsTitle")
        title_bar_layout.addWidget(title_lbl)
        
        title_bar_layout.addStretch()
        
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn)
        
        content_layout.addWidget(title_bar)
        
        # Title bar dragging support
        title_bar.mousePressEvent = self.title_press
        title_bar.mouseMoveEvent = self.title_move
        title_bar.mouseReleaseEvent = self.title_release
        
        # Tabs
        self.tabs = QTabWidget(self)
        
        # Tab 1: New Note Defaults
        self.tab_defaults = QWidget()
        self.init_defaults_tab()
        self.tabs.addTab(self.tab_defaults, "New Note Defaults")
        
        # Tab 2: Individual Note Customization
        self.tab_individual = QWidget()
        self.init_individual_tab()
        self.tabs.addTab(self.tab_individual, "Configure Note")
        
        content_layout.addWidget(self.tabs)

    def init_defaults_tab(self):
        layout = QVBoxLayout(self.tab_defaults)
        layout.setSpacing(10)
        layout.setContentsMargins(4, 10, 4, 4)
        
        # Default Theme
        theme_layout = QHBoxLayout()
        theme_lbl = QLabel("Default Theme:", self.tab_defaults)
        self.default_theme_combo = QComboBox(self.tab_defaults)
        self.default_theme_combo.addItem("Least Used (Distinct)", "distinct")
        for key, details in THEMES.items():
            self.default_theme_combo.addItem(details["name"], key)
        theme_layout.addWidget(theme_lbl)
        theme_layout.addWidget(self.default_theme_combo, 1)
        layout.addLayout(theme_layout)
        
        # Default Pinning
        self.default_pin_chk = QCheckBox("Default Pinned", self.tab_defaults)
        layout.addWidget(self.default_pin_chk)
        
        # Default Width
        width_layout = QHBoxLayout()
        width_lbl = QLabel("Default Width (px):", self.tab_defaults)
        self.default_width_spin = QSpinBox(self.tab_defaults)
        self.default_width_spin.setRange(160, 600)
        self.default_width_spin.setValue(240)
        width_layout.addWidget(width_lbl)
        width_layout.addWidget(self.default_width_spin)
        layout.addLayout(width_layout)
        
        # Default Height
        height_layout = QHBoxLayout()
        height_lbl = QLabel("Default Height (px):", self.tab_defaults)
        self.default_height_spin = QSpinBox(self.tab_defaults)
        self.default_height_spin.setRange(120, 600)
        self.default_height_spin.setValue(200)
        height_layout.addWidget(height_lbl)
        height_layout.addWidget(self.default_height_spin)
        layout.addLayout(height_layout)
        
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save Defaults", self.tab_defaults)
        save_btn.clicked.connect(self.save_defaults)
        layout.addWidget(save_btn)

    def init_individual_tab(self):
        layout = QVBoxLayout(self.tab_individual)
        layout.setSpacing(10)
        layout.setContentsMargins(4, 10, 4, 4)
        
        # Note Selector
        select_layout = QHBoxLayout()
        select_lbl = QLabel("Select Note:", self.tab_individual)
        self.note_selector = QComboBox(self.tab_individual)
        self.note_selector.currentIndexChanged.connect(self.load_selected_note_properties)
        select_layout.addWidget(select_lbl)
        select_layout.addWidget(self.note_selector, 1)
        layout.addLayout(select_layout)
        
        # Theme
        theme_layout = QHBoxLayout()
        theme_lbl = QLabel("Note Theme:", self.tab_individual)
        self.note_theme_combo = QComboBox(self.tab_individual)
        for key, details in THEMES.items():
            self.note_theme_combo.addItem(details["name"], key)
        theme_layout.addWidget(theme_lbl)
        theme_layout.addWidget(self.note_theme_combo, 1)
        layout.addLayout(theme_layout)
        
        # Pinning
        self.note_pin_chk = QCheckBox("Pinned", self.tab_individual)
        layout.addWidget(self.note_pin_chk)
        
        # Dimensions
        width_layout = QHBoxLayout()
        width_lbl = QLabel("Width (px):", self.tab_individual)
        self.note_width_spin = QSpinBox(self.tab_individual)
        self.note_width_spin.setRange(160, 600)
        width_layout.addWidget(width_lbl)
        width_layout.addWidget(self.note_width_spin)
        layout.addLayout(width_layout)
        
        height_layout = QHBoxLayout()
        height_lbl = QLabel("Height (px):", self.tab_individual)
        self.note_height_spin = QSpinBox(self.tab_individual)
        self.note_height_spin.setRange(120, 600)
        height_layout.addWidget(height_lbl)
        height_layout.addWidget(self.note_height_spin)
        layout.addLayout(height_layout)
        
        layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("Apply Changes", self.tab_individual)
        apply_btn.clicked.connect(self.apply_selected_note_properties)
        layout.addWidget(apply_btn)
        
        self.populate_note_selector()

    def load_defaults(self):
        defaults = self.manager.defaults_config
        
        # Set ComboBox
        theme = defaults.get("theme", "distinct")
        idx = self.default_theme_combo.findData(theme)
        if idx >= 0:
            self.default_theme_combo.setCurrentIndex(idx)
            
        # Set Pinning
        self.default_pin_chk.setChecked(defaults.get("pinned", False))
        
        # Set Dimensions
        self.default_width_spin.setValue(defaults.get("width", 240))
        self.default_height_spin.setValue(defaults.get("height", 200))

    def save_defaults(self):
        theme = self.default_theme_combo.currentData()
        pinned = self.default_pin_chk.isChecked()
        width = self.default_width_spin.value()
        height = self.default_height_spin.value()
        
        self.manager.defaults_config.update({
            "theme": theme,
            "pinned": pinned,
            "width": width,
            "height": height
        })
        self.manager.save_all_config()
        
        # Refresh individual combo boxes to reflect the saved settings
        self.populate_note_selector()

    def populate_note_selector(self):
        self.note_selector.blockSignals(True)
        self.note_selector.clear()
        
        # Get all notes config
        notes_config = self.manager.get_all_notes_config()
        for conf in notes_config:
            note_id = conf.get("id")
            title = note_id
            filepath = os.path.join(self.manager.data_dir, "notes", f"{note_id}.md")
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        if first_line:
                            import re
                            title = re.sub(r'^#+\s*', '', first_line).strip() or "Untitled"
                except Exception:
                    pass
            self.note_selector.addItem(f"{title} ({note_id})", note_id)
            
        if self.note_selector.count() == 0:
            self.note_selector.addItem("No Notes Found", None)
            
        self.note_selector.blockSignals(False)
        self.load_selected_note_properties()

    def load_selected_note_properties(self):
        note_id = self.note_selector.currentData()
        if not note_id:
            return
            
        conf = self.manager.all_notes_config.get(note_id)
        if not conf:
            return
            
        # Load theme
        idx = self.note_theme_combo.findData(conf.get("theme", "yellow"))
        if idx >= 0:
            self.note_theme_combo.setCurrentIndex(idx)
            
        # Load pinning
        self.note_pin_chk.setChecked(conf.get("pinned", False))
        
        # Load dimensions
        self.note_width_spin.setValue(conf.get("w", 240))
        self.note_height_spin.setValue(conf.get("h", 200))

    def apply_selected_note_properties(self):
        note_id = self.note_selector.currentData()
        if not note_id:
            return
            
        theme = self.note_theme_combo.currentData()
        pinned = self.note_pin_chk.isChecked()
        w = self.note_width_spin.value()
        h = self.note_height_spin.value()
        
        # Update in config
        if note_id in self.manager.all_notes_config:
            conf = self.manager.all_notes_config[note_id]
            conf["theme"] = theme
            conf["pinned"] = pinned
            conf["w"] = w
            conf["h"] = h
            
        # Update active window in real-time
        if note_id in self.manager.notes:
            note = self.manager.notes[note_id]
            note.set_theme(theme)
            note.set_pinned(pinned)
            note.resize(w, h)
            
        self.manager.save_all_config()
        self.manager.dashboard.reload_notes()

    def title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            event.accept()

    def title_move(self, event):
        if self.drag_start_pos is not None:
            self.move(self.pos() + event.position().toPoint() - self.drag_start_pos)
            event.accept()

    def title_release(self, event):
        self.drag_start_pos = None
        event.accept()
