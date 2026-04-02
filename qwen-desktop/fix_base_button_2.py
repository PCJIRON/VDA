import re
import pathlib

path = 'qwen_desktop/ui/components/base_button.py'
code = pathlib.Path(path).read_text('utf-8')

svg_dict = '''
COMMON_SVGS = {
    '\\uE711': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M6 18L18 6M6 6l12 12"></path></svg>', # close
    '\\uE723': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M12 4v16m8-8H4"></path></svg>', # attach
    '\\uE720': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M12 15a3 3 0 003-3V6a3 3 0 00-6 0v6a3 3 0 003 3z"></path><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v3M8 22h8"></path></svg>', # mic
    '\\uE724': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M5 15l7-7 7 7"></path></svg>', # send/up
    '\\uE713': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><circle cx="12" cy="12" r="3"></circle></svg>', # settings
    '\\uE890': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path d="M2.458 12C3.732 7.943 7.522 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.478 0-8.268-2.943-9.542-7z"></path></svg>', # vision
    '\\uE73A': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"></path></svg>', # gridView/menu
    '\\uE77B': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>', # person
    '\\uE734': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M5 12h14M12 5v14"></path></svg>', # mcp/server
    '\\uE718': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>', # plugins
    '\\uE70D': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M19 9l-7 7-7-7"></path></svg>', # dropdown
    '\\uE7C3': '<svg fill="none" viewBox="0 0 24 24" stroke="{color}" stroke-width="2"><path d="M8 9l3 3-3 3m5 0h3M4 6a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6z"></path></svg>', # code/chip
}
'''

new_paint_logic = '''
        # Icon
        svg_content = COMMON_SVGS.get(self.fluent_icon, None)
        if svg_content:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtCore import QByteArray, QRectF
            svg_string = svg_content.replace("{color}", "white")            
            renderer = QSvgRenderer(QByteArray(svg_string.encode('utf-8')))
            margin = 8
            renderer.render(painter, QRectF(margin, margin, self.width() - margin * 2, self.height() - margin * 2))
        else:
            painter.setPen(QColor("white"))
            font = QFont("Segoe Fluent Icons")
            font.setPixelSize(16)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            font.insertSubstitution("Segoe Fluent Icons", "Segoe MDL2 Assets")      
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.fluent_icon)
'''

code = re.sub(r'COMMON_SVGS = \{.*?\}', svg_dict.strip(), code, flags=re.DOTALL)
code = re.sub(r'        # Icon.*?(svg_content = COMMON_SVGS\.get.*?     painter\.drawText.*?self\.fluent_icon\))', new_paint_logic, code, flags=re.DOTALL)

pathlib.Path(path).write_text(code, 'utf-8')
print('base_button updated twice')
