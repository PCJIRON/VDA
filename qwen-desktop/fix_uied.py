import re

with open('qwen_desktop/ui/uied_overlay.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r\"\"\"            QToolButton \{
                background-color: white;
                border: none;
                border-radius: 21px;
            \}
            QToolButton:hover \{
                background-color: #F3F4F6;
            \}\"\"\",
    \"\"\"            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 21px;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.15);
            }
            QToolButton:checked {
                background-color: white;
            }\"\"\", text
)

text = re.sub(
    r\"\"\"            QToolButton \{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            \}
            QToolButton:hover \{
                background-color: rgba\(255,255,255,0\.15\);
            \}
            QToolButton:checked \{
                background-color: white;
            \}\"\"\",
    \"\"\"            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 19px;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.15);
            }
            QToolButton:checked {
                background-color: white;
            }\"\"\", text
)

with open('qwen_desktop/ui/uied_overlay.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched successfully.')
