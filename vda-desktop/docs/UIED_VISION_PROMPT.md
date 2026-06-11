# 🎯 ULTRA-DETAILED VISION MODEL PROMPT FOR UIED

## Purpose:
VDA Vision will analyze the ACTUAL SCREENSHOT and provide EXTREMELY DETAILED labels for visual template matching.

## Prompt Structure:

```python
prompt = f"""🎯 **YOU ARE A VISION MODEL EXPERT** specializing in UI element recognition.

**YOUR TASK:** Look at the SCREENSHOT with numbered green boxes. For EACH numbered element, provide an EXTREMELY DETAILED visual description.

## 📸 WHY THIS MATTERS:
These labels will be used for **VISUAL TEMPLATE MATCHING**. More details = better matching.

## 🔍 ANALYSIS FRAMEWORK - FOR EACH NUMBERED ELEMENT:

### 1. VISUAL APPEARANCE (What do you SEE?)
- **Colors**: Exact colors (e.g., "bright blue #0078D4", "chrome red/yellow/green/blue")
- **Shape**: Geometric (e.g., "perfect circle", "rounded rectangle", "square")
- **Size**: Relative (e.g., "small 32px icon", "large 200px button")
- **Style**: Flat, material, skeuomorphic, outlined, filled

### 2. CONTENT & SYMBOLS (What's INSIDE?)
- **Icons**: Describe symbol (e.g., "magnifying glass", "gear wheel", "house", "X mark")
- **Text**: Any visible text (e.g., "button says 'Submit'")
- **Images**: Logos, pictures
- **Numbers**: Numeric indicators

### 3. APPLICATION CONTEXT (What APP?)
- **Brand**: Chrome, VS Code, Edge, Spotify, Discord
- **Location**: Taskbar, title bar, sidebar, toolbar
- **Function**: What does it DO?

### 4. SURROUNDING CONTEXT (What's AROUND it?)
- Group membership (e.g., "one of 5 icons in taskbar")
- Container (e.g., "inside VS Code sidebar")
- Relationships (e.g., "right of Chrome icon")

## 📋 COMPONENT TYPES:
- `app_icon` - Application launchers
- `symbol_icon` - Symbolic icons (gear, bell, search)
- `button` - Clickable buttons
- `text_label` - Static text
- `input_field` - Text inputs
- `container_panel` - Large containers
- `menu_item` - Menu options
- `tab` - Browser tabs
- `checkbox_toggle` - Checkboxes, switches
- `scrollbar` - Scroll bars

## 📝 ELEMENTS TO LABEL:
{component_list}

## 💀 RESPONSE FORMAT - JSON ARRAY:
[
  {{
    "number": 1,
    "label": "Windows taskbar - horizontal bar at bottom, dark gray (#202020), contains app icons, 1920×40px",
    "type": "container_panel",
    "visual_details": "Dark taskbar with centered Windows 11 style icons"
  }},
  {{
    "number": 2,
    "label": "Google Chrome icon - colorful circle with red (#EA4335), yellow (#FBBC05), green (#34A853), blue (#4285F4) segments in pinwheel pattern, 32×32px",
    "type": "app_icon",
    "visual_details": "Glossy Chrome logo with four colored sections"
  }}
]

## ⚠️ CRITICAL RULES:
1. LABEL ALL {min(len(components), 50)} ELEMENTS
2. Be EXTREMELY DESCRIPTIVE - 15-30 words per label
3. Describe COLORS with names AND hex codes
4. Describe SHAPES precisely
5. Describe SYMBOLS - what does it REPRESENT?
6. Identify APPLICATIONS by name
7. Include SIZE in pixels
8. Mention LOCATION
9. Describe FUNCTION
10. Use ENGLISH only

## 🔥 PERFECT LABEL EXAMPLE:
❌ BAD: "Chrome icon"
✅ PERFECT: "Google Chrome browser icon in Windows taskbar - circular logo with four colored segments: red (#EA4335) top-left, yellow (#FBBC05) top-right, green (#34A853) bottom-left, blue (#4285F4) center circle, glossy finish, 32×32px, launches Chrome browser"

NOW ANALYZE THE IMAGE AND LABEL ALL ELEMENTS:"""
```

## Expected Output:

```json
[
  {
    "number": 1,
    "label": "Windows taskbar at bottom of screen - dark gray horizontal bar (#202020), full width 1920px, height 40px, contains pinned application icons centered in Windows 11 style layout",
    "type": "container_panel",
    "visual_details": "Modern Windows 11 taskbar with centered icon group, dark theme"
  },
  {
    "number": 2,
    "label": "Google Chrome browser icon - distinctive circular logo divided into four colored sections: red (#EA4335) upper segment, yellow (#FBBC05) right segment, green (#34A853) lower segment, blue (#4285F4) center circle, glossy gradient finish, 32×32 pixels",
    "type": "app_icon",
    "visual_details": "Chrome pinwheel logo with glossy finish, launches Chrome browser when clicked"
  },
  {
    "number": 3,
    "label": "Visual Studio Code icon - blue square/ribbon shape (#0078D4) with white angle brackets forming stylized '<>' symbol representing code, 32×32 pixels, launches VS Code editor",
    "type": "app_icon",
    "visual_details": "Microsoft blue square with white chevron design, represents code editor application"
  },
  {
    "number": 4,
    "label": "VS Code Explorer sidebar panel - vertical dark gray panel (#252526) on left side of window, 250×800 pixels, contains file tree structure with yellow folder icons and blue file icons",
    "type": "container_panel",
    "visual_details": "Dark themed sidebar with collapsible folder hierarchy, file explorer functionality"
  },
  {
    "number": 5,
    "label": "Search magnifying glass icon in VS Code sidebar - simple line art magnifying glass symbol in white/light gray (#CCCCCC), circular lens with diagonal handle, 20×20 pixels, used for searching files",
    "type": "symbol_icon",
    "visual_details": "Classic search icon with circular lens and 45-degree handle, universal search symbol"
  }
]
```

## Key Improvements:

1. **Vision-First Approach**: VDA SEES the actual screenshot
2. **Detailed Visual Analysis**: Colors, shapes, symbols, text, context
3. **Template Matching Ready**: Labels include visual details for matching
4. **Application Recognition**: Identifies Chrome, VS Code, Edge, etc.
5. **Hierarchical Understanding**: Containers → Child elements → Sub-elements
6. **Size & Location Context**: Dimensions and position included
7. **Function Description**: What the element DOES
