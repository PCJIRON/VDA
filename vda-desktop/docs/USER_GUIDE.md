# VDA Desktop - User Guide

**Version:** 0.4.0  
**Last Updated:** 2026-03-28

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [First-Time Setup](#first-time-setup)
4. [Using VDA Desktop](#using-vda-desktop)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Introduction

VDA Desktop is a native desktop application for chatting with VDA AI models. It provides:

- **OAuth Authentication** - Free tier with 1,000 requests/day
- **File Attachments** - Drag-and-drop or pick files
- **Conversation Management** - Save and load conversations
- **Markdown Support** - Rich formatting and syntax highlighting

**Platforms:** Windows 10/11, macOS 11+, Linux (Ubuntu 20.04+)

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Internet connection

### Step 1: Clone or Download

```bash
# If using Git
git clone https://github.com/YOUR_USERNAME/vda-desktop.git
cd vda-desktop
```

### Step 2: Install Dependencies

```bash
# Install required packages
py -m pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Run tests (optional)
py -m pytest tests/ -v

# Start the application
py run.py
```

---

## First-Time Setup

### OAuth Authentication

VDA Desktop uses OAuth for free tier access (1,000 requests/day).

#### Step 1: Launch Application

```bash
py run.py
```

#### Step 2: Login

1. Click the **"Login"** button in the toolbar
2. Your browser will open to the OAuth provider
3. Sign in with your VDA/Google account
4. Authorize the application
5. You'll be redirected back automatically

#### Step 3: Verify Login

- Toolbar should show "Logged In" (green)
- Rate limit indicator shows "API: 1000 left"

---

## Using VDA Desktop

### Sending Messages

1. Type your message in the input area at the bottom
2. Press **Enter** to send (or click "Send")
3. Wait for the typing indicator (animated dots)
4. AI response will stream in real-time

### Attaching Files

#### Method 1: Drag-and-Drop

1. Open your file explorer
2. Drag a file onto the input area
3. Blue dashed border will appear
4. Drop the file
5. File appears as an attachment chip

#### Method 2: File Picker

1. Click the 📎 (paperclip) icon
2. Navigate to your file
3. Select the file
4. File appears as an attachment chip

#### Supported File Types

- **Code:** `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, `.cpp`, `.c`, `.h`
- **Config:** `.json`, `.yaml`, `.yml`, `.toml`, `.ini`
- **Documents:** `.md`, `.txt`, `.rst`
- **Images:** `.png`, `.jpg`, `.gif` (for multimodal models)

#### File Limits

- Maximum: 10 files per message
- Maximum: 10MB per file

### Managing Conversations

#### Save Conversation

1. Press **Ctrl+S** (or **Cmd+S** on macOS)
2. Conversation saves to `~/.vda-desktop/conversations/`
3. Auto-saves when starting new chat

#### Load Conversation

1. Press **Ctrl+O** (or **Cmd+O** on macOS)
2. Select a conversation from the file dialog
3. Messages load in the chat window

**OR** use the sidebar:

1. Sidebar on left shows recent conversations
2. Click a conversation to load it

#### Delete Conversation

1. Right-click a conversation in the sidebar
2. Click "Delete"
3. Confirm deletion

#### New Chat

1. Press **Ctrl+N** (or **Cmd+N** on macOS)
2. Or click "New Chat" in the toolbar
3. Current conversation auto-saves first

### Copying Messages

1. Hover over any AI message
2. Click the 📋 (clipboard) icon
3. Icon changes to ✅ briefly
4. Message content is copied to clipboard
5. Paste anywhere with Ctrl+V

### Rate Limiting

**Free Tier:** 1,000 requests per day

The toolbar shows your remaining quota:
- **Green:** 100+ requests remaining
- **Orange:** 10-99 requests remaining
- **Red:** <10 requests remaining

When you hit the limit:
- Error message displays
- Wait time shows (until quota resets)
- Quota resets at midnight UTC

---

## Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| New Chat | Ctrl+N | Cmd+N |
| Open Conversation | Ctrl+O | Cmd+O |
| Save Conversation | Ctrl+S | Cmd+S |
| Clear Conversation | Ctrl+Shift+C | Cmd+Shift+C |
| Preferences | Ctrl+, | Cmd+, |
| Send Message | Enter | Enter |
| New Line | Shift+Enter | Shift+Enter |
| Quit | Ctrl+Q | Cmd+Q |

---

## Troubleshooting

### Application Won't Start

**Symptom:** Error on launch or window doesn't appear

**Solutions:**
1. Verify Python version: `py --version` (should be 3.9+)
2. Reinstall dependencies: `py -m pip install -r requirements.txt --force-reinstall`
3. Check console for error messages

### OAuth Login Fails

**Symptom:** Browser doesn't open or callback fails

**Solutions:**
1. Check default browser is set correctly
2. Ensure internet connection is active
3. Try manual OAuth: copy auth URL from console
4. Clear browser cache and cookies

### File Attachment Not Working

**Symptom:** Drag-and-drop doesn't work or file rejected

**Solutions:**
1. Check file size (max 10MB)
2. Verify file type is supported
3. Try file picker instead of drag-and-drop
4. Check file permissions

### Rate Limit Error

**Symptom:** "Rate limit exceeded" message

**Solutions:**
1. Wait for quota reset (midnight UTC)
2. Check remaining quota in toolbar
3. Consider upgrading to paid tier if needed

### Conversations Not Saving

**Symptom:** Save fails or conversations disappear

**Solutions:**
1. Check disk space
2. Verify write permissions in home directory
3. Check folder exists: `~/.vda-desktop/conversations/`
4. Restart application

### UI Freezing During API Calls

**Symptom:** Application becomes unresponsive when sending messages

**Solutions:**
1. This should not happen (async API calls)
2. Check network connection
3. Restart application
4. Report as bug if persistent

---

## FAQ

### Q: Is VDA Desktop free?

**A:** Yes! With OAuth authentication, you get 1,000 free requests per day.

### Q: Where are my conversations stored?

**A:** 
- **Windows:** `C:\Users\%USER%\AppData\Local\VDA\VDA Desktop\conversations\`
- **macOS:** `~/Library/Preferences/VDA/conversations/`
- **Linux:** `~/.config/vda-desktop/conversations/`

### Q: Can I use my own API key instead of OAuth?

**A:** Currently, OAuth is the primary authentication method. API key support may be added in future releases.

### Q: How do I export conversations?

**A:** Export feature is planned for a future release. Currently, you can manually copy conversation JSON files from the storage folder.

### Q: Does VDA Desktop work offline?

**A:** No, an internet connection is required for API calls. The UI will work offline, but you won't receive AI responses.

### Q: Can I use VDA Desktop on multiple devices?

**A:** Yes, but the 1,000 requests/day quota is shared across all devices for the same OAuth account.

### Q: How do I update VDA Desktop?

**A:** 
```bash
# If using Git
git pull origin main

# Reinstall dependencies
py -m pip install -r requirements.txt
```

### Q: Where can I get help?

**A:** 
- Check this User Guide
- Review the [README.md](../README.md)
- Open an issue on GitHub
- Check existing issues for solutions

---

## Support

For additional help:
- **Documentation:** See `docs/` folder
- **Issues:** https://github.com/YOUR_USERNAME/vda-desktop/issues
- **Discussions:** https://github.com/YOUR_USERNAME/vda-desktop/discussions

---

**Happy Chatting! 🎉**
