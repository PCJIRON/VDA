import re
import pathlib

path = 'qwen_desktop/ui/components/base_button.py'
code = pathlib.Path(path).read_text('utf-8')

with open('fix_base_button_2.py', encoding='utf-8') as f:
    content = f.read()

svg_dict = content.split("'''")[1].strip()
new_paint_logic = content.split("'''")[3].strip()

# using find and replace
m = re.search(r'COMMON_SVGS = \{.*?\}', code, flags=re.DOTALL)
code = code[:m.start()] + svg_dict + code[m.end():]

m2 = re.search(r'        # Icon.*?(svg_content = COMMON_SVGS\.get.*?     painter\.drawText.*?self\.fluent_icon\))', code, flags=re.DOTALL)
if m2:
    code = code[:m2.start()] + new_paint_logic + code[m2.end():]
else:
    print('Failed to substitute paint_logic')

pathlib.Path(path).write_text(code, 'utf-8')
print('base button update applied correctly')
