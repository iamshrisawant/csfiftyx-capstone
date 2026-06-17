# src/styles.py

THEMES = {
    "yellow": {
        "name": "Sunny Yellow",
        "bg_color": "rgba(254, 240, 138, 0.94)",
        "border_color": "rgba(234, 179, 8, 0.35)",
        "accent_color": "#CA8A04",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(253, 224, 71, 0.45)",
    },
    "blue": {
        "name": "Ocean Blue",
        "bg_color": "rgba(219, 234, 254, 0.94)",
        "border_color": "rgba(59, 130, 246, 0.35)",
        "accent_color": "#1D4ED8",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(191, 219, 254, 0.45)",
    },
    "green": {
        "name": "Mint Green",
        "bg_color": "rgba(209, 250, 229, 0.94)",
        "border_color": "rgba(16, 185, 129, 0.35)",
        "accent_color": "#047857",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(167, 243, 208, 0.45)",
    },
    "orange": {
        "name": "Pastel Orange",
        "bg_color": "rgba(255, 237, 213, 0.94)",
        "border_color": "rgba(249, 115, 22, 0.35)",
        "accent_color": "#C2410C",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(254, 215, 170, 0.45)",
    },
    "purple": {
        "name": "Lavender Purple",
        "bg_color": "rgba(243, 232, 255, 0.94)",
        "border_color": "rgba(168, 85, 247, 0.35)",
        "accent_color": "#7E22CE",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(233, 213, 255, 0.45)",
    },
    "pink": {
        "name": "Rose Pink",
        "bg_color": "rgba(252, 231, 243, 0.94)",
        "border_color": "rgba(244, 63, 94, 0.35)",
        "accent_color": "#BE185D",
        "text_color": "#1C1C1E",
        "subtext_color": "#48484A",
        "title_bg": "rgba(251, 207, 232, 0.45)",
    }
}

QSS_TEMPLATE = """
/* Main Sticky Note Frame */
#NoteWidget {
    background-color: %(bg_color)s;
    border: 1px solid %(border_color)s;
    border-radius: 12px;
}

/* Title Bar - Thin Handle style */
#TitleBar {
    background-color: %(title_bg)s;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

/* Custom Window Controls - Compact */
.TitleBarButton {
    border: none;
    background: transparent;
    color: %(text_color)s;
    border-radius: 3px;
    width: 16px;
    height: 16px;
    font-size: 11px;
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
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: %(accent_color)s;
    selection-color: white;
}

/* Custom Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 4px 1px 4px 0px;
}

QScrollBar::handle:vertical {
    background: rgba(120, 120, 120, 0.3);
    min-height: 15px;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(120, 120, 120, 0.5);
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
    font-size: 12px;
}

#SlashMenu::item {
    padding: 4px 10px;
    border-radius: 4px;
    color: #E5E5EA;
}

#SlashMenu::item:selected {
    background-color: %(accent_color)s;
    color: white;
}

/* Collapsed Dot Styling - Minimalist Circle */
#CollapsedDot {
    background-color: %(accent_color)s;
    border: 1px solid white;
    border-radius: 12px; /* Half of 24px size */
}
"""

DASHBOARD_QSS = """
/* Dashboard Background */
#DashboardWidget {
    background-color: rgba(28, 28, 30, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 14px;
}

#DashboardTitle {
    color: #FFFFFF;
    font-weight: bold;
    font-size: 15px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

#SearchBar {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    color: #FFFFFF;
    padding: 7px 12px;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
}

#SearchBar:focus {
    border: 1px solid #0A84FF;
    background-color: rgba(255, 255, 255, 0.12);
}

/* Notes List */
#NotesList {
    background: transparent;
    border: none;
    color: #F2F2F7;
    font-size: 13px;
    padding: 0px;
}

#NotesList::item {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 0px; /* Set padding on the custom widget instead */
    margin-bottom: 8px;
}

#NotesList::item:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

#NotesList::item:selected {
    background-color: rgba(10, 132, 255, 0.15);
    border: 1px solid #0A84FF;
}

/* Note List Row Custom Widget Styles */
.ItemTitle {
    color: #FFFFFF;
    font-weight: 600;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
}

.ItemSubtitle {
    color: #AEAEB2;
    font-size: 11px;
    font-family: 'Inter', sans-serif;
}

.ItemDeleteButton {
    border: none;
    background: transparent;
    color: #AEAEB2;
    font-size: 12px;
    border-radius: 4px;
    width: 22px;
    height: 22px;
}

.ItemDeleteButton:hover {
    background-color: rgba(255, 69, 58, 0.2);
    color: #FF453A;
}

/* Custom Scrollbar for List */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 4px 1px 4px 0px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.15);
    min-height: 20px;
    border-radius: 3.5px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.3);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

import re

def get_theme_stylesheet(theme_key, is_hovered=True):
    theme = THEMES.get(theme_key, THEMES["yellow"]).copy()
    if not is_hovered:
        # Transition background alpha to 0.40 and title_bg to 0.15 for see-through
        theme["bg_color"] = re.sub(r',\s*0\.\d+\)', ', 0.40)', theme["bg_color"])
        theme["title_bg"] = re.sub(r',\s*0\.\d+\)', ', 0.15)', theme["title_bg"])
    return QSS_TEMPLATE % theme

def get_dashboard_stylesheet():
    return DASHBOARD_QSS
