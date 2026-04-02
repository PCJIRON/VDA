import pathlib

path = 'qwen_desktop/ui/settings_dialog.py'
code = pathlib.Path(path).read_text('utf-8')

# Import our common svgs
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
'''

if 'get_svg_icon' not in code:
    code = code.replace('from PyQt6.QtWidgets import (', import_stmt + '\nfrom PyQt6.QtWidgets import (')

# List Widget Items
code = code.replace('item_acc = QListWidgetItem("\uE77B  Account")', 'item_acc = QListWidgetItem(" Account"); item_acc.setIcon(get_svg_icon("\uE77B", "#4b5563"))')
code = code.replace('item_mcp = QListWidgetItem("\uE734  MCP Servers")', 'item_mcp = QListWidgetItem(" MCP Servers"); item_mcp.setIcon(get_svg_icon("\uE734", "#4b5563"))')
code = code.replace('item_plug = QListWidgetItem("\uE718  Plugins")', 'item_plug = QListWidgetItem(" Plugins"); item_plug.setIcon(get_svg_icon("\uE718", "#4b5563"))')

# title
code = code.replace('title_lbl = QLabel("\uE713  Settings")', 'title_lbl = QLabel(" Settings")')

# Close btn
code = code.replace('self.close_btn = QPushButton("\uE711")', 'self.close_btn = QPushButton(""); self.close_btn.setIcon(get_svg_icon("\uE711", "#6b7280"))')

pathlib.Path(path).write_text(code, 'utf-8')
print("Settings dialog icons updated.")