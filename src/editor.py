# src/editor.py

import re
from PySide6.QtWidgets import QTextEdit, QListWidget, QListWidgetItem
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor
from PySide6.QtCore import Qt, QPoint, QRect

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, is_dark_theme=True):
        super().__init__(parent)
        self.rules = []

        # Color definitions depending on theme contrast
        if is_dark_theme:
            color_header = QColor("#FF9F0A")  # Vibrant Orange
            color_bold = QColor("#30D158")    # Vibrant Green
            color_italic = QColor("#BF5AF2")  # Vibrant Purple
            color_code = QColor("#FFD60A")    # Yellow tint
            color_checkbox = QColor("#64D2FF")# Sky Blue
            color_link = QColor("#0A84FF")    # Electric Blue
        else:
            color_header = QColor("#D97706")  # Amber/Orange
            color_bold = QColor("#16A34A")    # Green
            color_italic = QColor("#9333EA")  # Purple
            color_code = QColor("#B45309")    # Darker Yellow/Brown
            color_checkbox = QColor("#0284C7")# Blue
            color_link = QColor("#2563EB")    # Blue link

        # Format rules
        # Headers (# Header)
        fmt_header = QTextCharFormat()
        fmt_header.setFontWeight(QFont.Weight.Bold)
        fmt_header.setForeground(color_header)
        self.rules.append((re.compile(r'^#+\s.*'), fmt_header))

        # Bold (**bold** or __bold__)
        fmt_bold = QTextCharFormat()
        fmt_bold.setFontWeight(QFont.Weight.Bold)
        fmt_bold.setForeground(color_bold)
        self.rules.append((re.compile(r'\*\*[^\*]+\*\*'), fmt_bold))
        self.rules.append((re.compile(r'__[^\_]+__'), fmt_bold))

        # Italic (*italic* or _italic_)
        fmt_italic = QTextCharFormat()
        fmt_italic.setFontItalic(True)
        fmt_italic.setForeground(color_italic)
        self.rules.append((re.compile(r'\*[^\*]+\*'), fmt_italic))
        self.rules.append((re.compile(r'\_[^\_]+\_'), fmt_italic))

        # Checkbox unchecked (- [ ])
        fmt_unchecked = QTextCharFormat()
        fmt_unchecked.setFontWeight(QFont.Weight.Bold)
        fmt_unchecked.setForeground(color_checkbox)
        self.rules.append((re.compile(r'^\s*-\s\[\s\]'), fmt_unchecked))

        # Checkbox checked (- [x] or - [X])
        fmt_checked = QTextCharFormat()
        fmt_checked.setFontWeight(QFont.Weight.Bold)
        fmt_checked.setForeground(color_checkbox)
        fmt_checked.setFontStrikeOut(True)
        self.rules.append((re.compile(r'^\s*-\s\[[xX]\]'), fmt_checked))

        # Bullet List (- or *)
        fmt_bullet = QTextCharFormat()
        fmt_bullet.setFontWeight(QFont.Weight.Bold)
        fmt_bullet.setForeground(color_link)
        self.rules.append((re.compile(r'^\s*[\-\*]\s'), fmt_bullet))

        # Code block / inline code (`code`)
        fmt_code = QTextCharFormat()
        fmt_code.setFontFamily("Courier New")
        fmt_code.setForeground(color_code)
        self.rules.append((re.compile(r'`[^`]+`'), fmt_code))

        # Link ([text](url))
        fmt_link = QTextCharFormat()
        fmt_link.setFontUnderline(True)
        fmt_link.setForeground(color_link)
        self.rules.append((re.compile(r'\[[^\]]+\]\([^\)]+\)'), fmt_link))

    def highlightBlock(self, text):
        for pattern, format_rule in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format_rule)


class SlashMenu(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("SlashMenu")
        self.setFixedWidth(180)
        self.setFixedHeight(160)

        # Commands list: (Label, Markdown Template, cursor_offset)
        self.commands = [
            ("☐ Todo Checkbox", "- [ ] ", 0),
            ("• Bullet Point", "- ", 0),
            ("Header 1", "# ", 0),
            ("Header 2", "## ", 0),
            ("Header 3", "### ", 0),
            ("** Bold Text", "****", -2),
            ("* Italic Text", "**", -1),
            ("` Code Block", "``", -1)
        ]

        for label, _, _ in self.commands:
            item = QListWidgetItem(label)
            self.addItem(item)

        self.setCurrentRow(0)


class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None, is_dark_theme=True):
        super().__init__(parent)
        self.setObjectName("EditorArea")
        self.setAcceptRichText(False)
        self.setPlaceholderText("Type note here... (use / for formatting commands)")

        self.is_dark_theme = is_dark_theme
        self.highlighter = MarkdownHighlighter(self.document(), is_dark_theme)

        # Slash autocomplete menu
        self.slash_menu = SlashMenu()
        self.slash_menu.itemClicked.connect(self.execute_command)
        self.slash_active = False
        self.slash_start_pos = -1

    def update_theme(self, is_dark_theme):
        self.is_dark_theme = is_dark_theme
        self.highlighter = MarkdownHighlighter(self.document(), is_dark_theme)
        self.highlighter.rehighlight()

    def keyPressEvent(self, event):
        if self.slash_menu.isVisible():
            key = event.key()

            if key == Qt.Key.Key_Up:
                row = self.slash_menu.currentRow()
                self.slash_menu.setCurrentRow(max(0, row - 1))
                return
            elif key == Qt.Key.Key_Down:
                row = self.slash_menu.currentRow()
                self.slash_menu.setCurrentRow(min(self.slash_menu.count() - 1, row + 1))
                return
            elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                self.execute_command(self.slash_menu.currentItem())
                return
            elif key == Qt.Key.Key_Escape:
                self.close_slash_menu()
                return
            elif key == Qt.Key.Key_Backspace:
                # If they delete the slash, close the menu
                cursor = self.textCursor()
                if cursor.position() == self.slash_start_pos + 1:
                    super().keyPressEvent(event)
                    self.close_slash_menu()
                    return

        super().keyPressEvent(event)

        # Trigger slash menu
        if event.text() == "/":
            self.show_slash_menu()
        elif self.slash_active:
            self.filter_slash_menu()

    def show_slash_menu(self):
        self.slash_active = True
        self.slash_start_pos = self.textCursor().position() - 1

        # Locate slash position in screen coords
        cursor_rect = self.cursorRect()
        global_pos = self.viewport().mapToGlobal(cursor_rect.bottomLeft())
        self.slash_menu.move(global_pos + QPoint(0, 5))
        self.slash_menu.show()
        self.slash_menu.setCurrentRow(0)
        self.setFocus()

    def filter_slash_menu(self):
        cursor = self.textCursor()
        curr_pos = cursor.position()

        # Check if cursor moved before the slash
        if curr_pos <= self.slash_start_pos:
            self.close_slash_menu()
            return

        # Get search query
        cursor.setPosition(self.slash_start_pos + 1, QTextCursor.MoveMode.KeepAnchor)
        query = cursor.selectedText().lower()

        visible_count = 0
        for i in range(self.slash_menu.count()):
            item = self.slash_menu.item(i)
            label = item.text().lower()
            if query in label or not query:
                item.setHidden(False)
                visible_count += 1
            else:
                item.setHidden(True)

        if visible_count == 0:
            self.slash_menu.hide()
        elif not self.slash_menu.isVisible():
            self.slash_menu.show()

    def close_slash_menu(self):
        self.slash_active = False
        self.slash_start_pos = -1
        self.slash_menu.hide()

    def execute_command(self, item):
        if not item:
            return

        cmd_label = item.text()
        template = ""
        offset = 0

        # Find template
        for label, t, o in self.slash_menu.commands:
            if label == cmd_label:
                template = t
                offset = o
                break

        if not template:
            self.close_slash_menu()
            return

        # Replace typed command (from slash_start_pos to current position)
        cursor = self.textCursor()
        cursor.setPosition(self.slash_start_pos, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(self.textCursor().position(), QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

        # Check if we should insert inline or at the beginning of the line
        # For block types: todo list, bullet points, headers
        is_block = template.startswith(("-", "#"))

        if is_block:
            # Check if current line is empty
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            line_text = cursor.block().text()
            if line_text == "":
                cursor.insertText(template)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                cursor.insertText("\n" + template)
        else:
            # Inline commands like bold/italic/code
            cursor.insertText(template)
            if offset != 0:
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, abs(offset))

        self.setTextCursor(cursor)
        self.close_slash_menu()

    def focusOutEvent(self, event):
        # Close slash menu if user clicks elsewhere
        super().focusOutEvent(event)
        # Check if list widget is active before closing
        if not self.slash_menu.hasFocus():
            self.close_slash_menu()
