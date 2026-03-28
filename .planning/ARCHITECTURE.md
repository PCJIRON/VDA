# Architecture Overview

**Project:** Qwen Desktop  
**Version:** 0.4.0

---

## System Architecture

### High-Level Components

```text
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface (PyQt6)                   │
│   (MainWindow, ChatWidget, InputArea, ConversationSidebar)      │
└─────────────┬──────────────┴─────────────────────┴──────┬───────┘
              │                                           │
              └───────────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      Core App Logic       │
                    │      (app.py / QApp)      │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
│    Auth       │         │    API/Core   │         │ Attachments/  │
│   System      │         │     Logic     │         │   Config      │
│ (OAuth Flow)  │         │ (Qwen Models) │         │ (File I/O)    │
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## Core Application Layers

### 1. User Interface (UI)
The presentation layer is built entirely with `PyQt6`. The `ui/` module contains specific layout widgets, main windows, and reusable PyQt elements.
* `main_window.py`: Orchestrates everything.
* `chat_widget.py`: Handles message bubbles and scrolling history.
* `input_area.py`: Manages the text box and file attachment drops.

### 2. Core Logic
Data transport, serialization, API abstraction, and persistent connections.
* `api_client.py`: DashScope/Qwen REST endpoints logic.
* `conversation_manager.py`: Handles conversation state, load/save across sessions.

### 3. Authentication
* `oauth_handler.py`: Implements device flow to log users in via standard OAuth2.
* `token_manager.py`: Persists access and refresh tokens to OS credential storage using `keyring`.

### 4. Utilities
Shared system-level helpers including rate limiters, logging, and error management.
* `rate_limiter.py`: In-memory thread-safe limiting.
* `file_encoder.py`: Base64 preparation of file attachments.

## Data Flow
* User sends input in `InputArea` -> Triggers `sendMessage` signal.
* `MainWindow` forwards the message to `api_client.py` inside a `QThread` (to prevent UI blocking).
* Background thread streams chunks back via specific PyQt `Signals`.
* UI updates `.appendChunk` to real-time render markdown text.
