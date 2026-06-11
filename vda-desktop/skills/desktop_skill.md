# Desktop UI Control Skills

Practical instructions for controlling a Windows desktop via keyboard and mouse automation.

---

## 1. Windows OS Shortcuts

| Shortcut | Action |
|---|---|
| `Win+E` | Open File Explorer |
| `Win+D` | Show Desktop (minimize all windows) |
| `Alt+F4` | Close the active window |
| `Alt+Tab` | Switch between open windows |
| `Win+R` | Open the Run dialog |
| `Win+L` | Lock the computer |
| `Win+S` | Open Windows Search |
| `Ctrl+Shift+Esc` | Open Task Manager directly |
| `Win+Shift+S` | Take a screenshot (Snipping Tool) |
| `Win+Up` | Maximize the active window |
| `Win+Down` | Minimize/restore the active window |
| `Win+Left` | Snap window to the left half |
| `Win+Right` | Snap window to the right half |

---

## 2. Chrome Browser Shortcuts

### Tab Management

| Shortcut | Action |
|---|---|
| `Ctrl+T` | Open a new tab |
| `Ctrl+W` | Close the current tab |
| `Ctrl+Tab` | Switch to the next tab |
| `Ctrl+Shift+Tab` | Switch to the previous tab |
| `Ctrl+Shift+T` | Reopen the last closed tab |
| `Ctrl+1` through `Ctrl+8` | Switch to tab 1–8 |
| `Ctrl+9` | Switch to the last tab |

### Navigation

| Shortcut | Action |
|---|---|
| `Ctrl+L` | Focus the URL/address bar |
| `F5` | Refresh the current page |
| `Ctrl+Shift+R` | Hard refresh (bypass cache) |
| `Alt+Left` | Go back one page |
| `Alt+Right` | Go forward one page |

### Tools

| Shortcut | Action |
|---|---|
| `Ctrl+F` | Open Find on page |
| `Ctrl+H` | Open browsing History |
| `Ctrl+D` | Bookmark the current page |
| `Ctrl+J` | Open Downloads |
| `Ctrl+Shift+J` | Open Developer Tools (Console) |
| `F12` | Open Developer Tools |

---

## 3. Text Editing Shortcuts

### Clipboard

| Shortcut | Action |
|---|---|
| `Ctrl+A` | Select all text |
| `Ctrl+C` | Copy selected text |
| `Ctrl+V` | Paste from clipboard |
| `Ctrl+X` | Cut selected text |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Y` | Redo last undone action |

### Cursor Movement

| Shortcut | Action |
|---|---|
| `Home` | Move cursor to the start of the line |
| `End` | Move cursor to the end of the line |
| `Ctrl+Home` | Move cursor to the start of the document |
| `Ctrl+End` | Move cursor to the end of the document |
| `Ctrl+Left` | Move cursor one word to the left |
| `Ctrl+Right` | Move cursor one word to the right |

### Text Selection

| Shortcut | Action |
|---|---|
| `Shift+Home` | Select from cursor to the start of the line |
| `Shift+End` | Select from cursor to the end of the line |
| `Ctrl+Shift+Home` | Select from cursor to the start of the document |
| `Ctrl+Shift+End` | Select from cursor to the end of the document |
| `Ctrl+Shift+Left` | Select the word to the left |
| `Ctrl+Shift+Right` | Select the word to the right |
| `Shift+Arrow` | Extend selection one character/line at a time |

---

## 4. UI Navigation Without Mouse

Use keyboard navigation when mouse clicks are unreliable or when elements lack visual templates.

| Shortcut | Action |
|---|---|
| `Tab` | Move focus to the next interactive element |
| `Shift+Tab` | Move focus to the previous interactive element |
| `Enter` | Activate/click the currently focused element |
| `Space` | Toggle a checkbox or press a focused button |
| `Escape` | Close a dialog, popup, dropdown, or cancel an action |
| `Arrow Up/Down` | Navigate within menus, lists, and dropdowns |
| `Arrow Left/Right` | Navigate horizontal menus or tabs |
| `Alt+Down` | Open a dropdown/combo box |
| `Alt+F4` | Close the active window if Escape doesn't work |

### Tips

- Press `Tab` repeatedly to cycle through all focusable elements on the page.
- Use `Shift+Tab` to go backwards if you overshoot.
- Combine with `Enter` to click buttons, links, and submit forms.
- In dialog boxes, `Tab` moves between buttons (OK, Cancel, etc.) and `Enter` presses the focused one.

---

## 5. Common Website Navigation Patterns

### General Pattern

1. Press `Ctrl+L` to focus the URL bar.
2. Type the URL or search query.
3. Press `Enter` to navigate or search.
4. Use `Tab` to move through page elements.
5. Press `Enter` to activate the desired element.

### LinkedIn

1. `Ctrl+L` → type `linkedin.com` → `Enter`
2. Wait for page to load (use `wait` action, 2–3 seconds).
3. `Tab` repeatedly to reach Jobs, Messaging, or Notifications in the top navigation bar.
4. `Enter` to open the selected section.
5. To search: `Tab` to the search bar → type query → `Enter`.

### Google Search

1. `Ctrl+L` → type the search query directly → `Enter`
   - Chrome uses Google as the default search engine, so typing in the URL bar works as a search.
2. `Tab` through the search results.
3. `Enter` to open the desired result.
4. `Alt+Left` to go back to search results.

### YouTube

1. `Ctrl+L` → type `youtube.com` → `Enter`
2. Wait for page to load.
3. Press `/` to focus the YouTube search bar (YouTube-specific shortcut).
4. Type the search query → `Enter`.
5. `Tab` through video results → `Enter` to play.

### Gmail

1. `Ctrl+L` → type `mail.google.com` → `Enter`
2. Wait for page to load.
3. Press `C` to compose a new email (Gmail keyboard shortcut).
4. Type recipient address → `Tab` → type subject → `Tab` → type body.
5. `Ctrl+Enter` to send the email.

---

## 6. Error Recovery Strategies

### Click Failed (No Pixel Change Detected)

- **First:** Retry the click once at the same coordinates.
- **Then:** Try the keyboard shortcut equivalent instead.
- **Example:** If clicking the URL bar fails → use `Ctrl+L` instead.

### Wrong Window Focused

- Press `Alt+Tab` to switch to the correct window.
- Or click the correct application icon in the taskbar (single click).
- Verify by taking a screenshot after switching.

### Page Not Loaded Yet

- Use the `wait` action to pause for 2–3 seconds.
- Take a new screenshot to verify the page has loaded.
- If still loading, wait again (up to 10 seconds total).
- If still not loaded, press `F5` to refresh.

### Typed in Wrong Field

- Press `Ctrl+A` to select all text in the field.
- Press `Delete` or `Backspace` to clear it.
- Retype the correct text.

### Autofill Dropdown Appeared

- If the desired suggestion is highlighted: press `Enter` to accept it.
- If the dropdown is unwanted: press `Escape` to dismiss it, then continue typing.
- **Never** try to click autofill dropdown items — use keyboard only.

### Stuck in a Loop (Same Action Failing Repeatedly)

- **Stop** after 2 consecutive identical failures.
- Switch strategy completely:
  - Mouse clicking → keyboard shortcuts
  - Direct URL navigation → search-based navigation
  - Tab navigation → coordinate-based clicking
- If all approaches fail, report the issue to the user and ask for guidance.

### Dialog or Popup Blocking

- Press `Escape` to try dismissing it.
- Press `Enter` to accept/confirm the dialog if appropriate.
- Use `Tab` + `Enter` to navigate to a specific dialog button.
- If a cookie consent banner appears, `Tab` to "Accept" → `Enter`.

### Element Not Found on Screen

- Scroll down: press `Page Down` or `Space` (on non-input pages).
- Scroll up: press `Page Up`.
- Use `Ctrl+F` to search for text on the page.
- Try `Ctrl+End` to jump to the bottom of the page.

---

## 7. Smart Decision Rules

### URL Bar Interaction

- **ALWAYS** use `Ctrl+L` to focus the URL bar — never try to click it.
- **ALWAYS** press `Enter` after typing a URL or search query.
- Clear the URL bar with `Ctrl+A` → type new URL (it auto-replaces selected text).

### Click Types

- **Double-click** for desktop icons and file names in File Explorer.
- **Single-click** for taskbar icons, hyperlinks, and buttons.
- **Right-click** to open context menus.

### Autofill Handling

- When Chrome autofill appears, press `Enter` to accept, or `Escape` to dismiss.
- **Never** click autofill dropdown items with the mouse.

### Failure Escalation

- If **2+ consecutive steps fail**, change strategy completely.
- If **keyboard approach fails**, try mouse approach (and vice versa).
- If **3+ different strategies fail**, pause and report to the user.

### Navigation Preference

- Prefer `Tab` navigation for elements that don't have saved templates.
- Prefer keyboard shortcuts over mouse clicks for reliability.
- Prefer direct URL entry over clicking through menus to reach a page.

### Typing Safety

- Always verify the correct field is focused before typing.
- Use `Ctrl+A` → `Delete` to clear a field before entering new text.
- After typing, take a screenshot to verify the text was entered correctly.

### Wait Before Verify

- After any navigation action (click, Enter on URL, page load), wait 1–2 seconds.
- Always take a screenshot after waiting to verify the result.
- Don't assume an action succeeded — verify visually.

### Window Management

- Before interacting with an application, verify it is the foreground window.
- Use `Alt+Tab` or click the taskbar icon to bring a window to the front.
- If a window is minimized, single-click its taskbar icon to restore it.
