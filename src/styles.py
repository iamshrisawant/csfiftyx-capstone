# src/styles.py

THEMES = {
    "carbon": {
        "name": "Carbon Dark",
        "bg_color": "rgba(30, 30, 30, 0.85)",
        "border_color": "rgba(255, 255, 255, 0.12)",
        "accent_color": "#0A84FF",
        "text_color": "#F2F2F7",
        "subtext_color": "#AEAEB2",
        "title_bg": "rgba(20, 20, 20, 0.4)",
    },
    "yellow": {
        "name": "Sunny Yellow",
        "bg_color": "rgba(253, 244, 200, 0.92)",
        "border_color": "rgba(234, 179, 8, 0.3)",
        "accent_color": "#CA8A04",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(254, 240, 138, 0.5)",
    },
    "blue": {
        "name": "Ocean Blue",
        "bg_color": "rgba(219, 234, 254, 0.92)",
        "border_color": "rgba(59, 130, 246, 0.3)",
        "accent_color": "#2563EB",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(191, 219, 254, 0.5)",
    },
    "green": {
        "name": "Mint Green",
        "bg_color": "rgba(220, 252, 231, 0.92)",
        "border_color": "rgba(34, 197, 94, 0.3)",
        "accent_color": "#16A34A",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(187, 247, 208, 0.5)",
    },
    "pink": {
        "name": "Rose Pink",
        "bg_color": "rgba(252, 231, 243, 0.92)",
        "border_color": "rgba(236, 72, 153, 0.3)",
        "accent_color": "#DB2777",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(251, 207, 232, 0.5)",
    },
    "purple": {
        "name": "Lavender Purple",
        "bg_color": "rgba(243, 232, 255, 0.92)",
        "border_color": "rgba(168, 85, 247, 0.3)",
        "accent_color": "#9333EA",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(233, 213, 255, 0.5)",
    }
}

QSS_TEMPLATE = """
/* Main Sticky Note Frame */
#NoteWidget {
    background-color: %(bg_color)s;
    border: 1px solid %(border_color)s;
    border-radius: 12px;
}

/* Title Bar */
#TitleBar {
    background-color: %(title_bg)s;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

#TitleLabel {
    color: %(text_color)s;
    font-weight: bold;
    font-family: 'Inter', 'Outfit', 'Segoe UI', sans-serif;
    font-size: 12px;
    background: transparent;
}

/* Custom Window Controls */
.TitleBarButton {
    border: none;
    background: transparent;
    color: %(text_color)s;
    border-radius: 4px;
    width: 22px;
    height: 22px;
    font-size: 13px;
}

.TitleBarButton:hover {
    background-color: rgba(120, 120, 120, 0.25);
}

.TitleBarButton#CloseButton:hover {
    background-color: #FF453A;
    color: white;
}

/* Input Fields & Text Area */
#EditorArea, #RenderArea {
    background: transparent;
    border: none;
    color: %(text_color)s;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.5;
    selection-background-color: %(accent_color)s;
    selection-color: white;
}

/* Custom Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 2px 4px 0px;
}

QScrollBar::handle:vertical {
    background: rgba(120, 120, 120, 0.35);
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(120, 120, 120, 0.6);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Slash Autocomplete Pop-up */
#SlashMenu {
    background-color: rgba(30, 30, 30, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    color: #F2F2F7;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

#SlashMenu::item {
    padding: 6px 12px;
    border-radius: 4px;
    color: #E5E5EA;
}

#SlashMenu::item:selected {
    background-color: %(accent_color)s;
    color: white;
}

/* Collapsed Dot Styling */
#CollapsedDot {
    background-color: %(accent_color)s;
    border: 2px solid white;
    border-radius: 18px; /* Half of 36px size */
}
"""

def get_theme_stylesheet(theme_key):
    theme = THEMES.get(theme_key, THEMES["carbon"])
    return QSS_TEMPLATE % theme
