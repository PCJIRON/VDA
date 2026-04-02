import pathlib
import sys

path = 'qwen_desktop/ui/floating_assistant.py'
code = pathlib.Path(path).read_text('utf-8')

import_stmt = '''from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt

def get_svg_icon(fluent_code, color="black", size=24):
    from qwen_desktop.ui.components.base_button import COMMON_SVGS
    svg_str = COMMON_SVGS.get(fluent_code, "").replace("{color}", color).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg_str))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def get_svg_pixmap(fluent_code, color="black", size=24):
    from qwen_desktop.ui.components.base_button import COMMON_SVGS
    svg_str = COMMON_SVGS.get(fluent_code, "").replace("{color}", color).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg_str))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap
'''

if 'get_svg_icon' not in code:
    code = code.replace('from PyQt6.QtWidgets import (', import_stmt + '\nfrom PyQt6.QtWidgets import (')

# Chip
code = code.replace('chip = QLabel(f"\uE7C3 {name}")', 'chip = QLabel(f" {name}"); chip.setToolTip("File")') # Text only chip maybe? Or we add a pixmap

# Instead of QLabel with text for icon, use setPixmap
code = code.replace('icon_lbl = QLabel("\uE7C3")', 'icon_lbl = QLabel(""); icon_lbl.setPixmap(get_svg_pixmap("\uE7C3", "#6b7280", 16))')

# Close btn
code = code.replace('close_btn = QPushButton("\uE711")', 'close_btn = QPushButton(""); close_btn.setIcon(get_svg_icon("\uE711", "#6b7280", 16))')

pathlib.Path(path).write_text(code, 'utf-8')
print("Floating assistant icons updated.")