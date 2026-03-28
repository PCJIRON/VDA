# Project Roadmap

**Project:** Qwen Desktop  
**Version:** 0.4.0

---

## Phase 1: Foundation (Week 1-2)

**Goal:** Basic application structure and OAuth authentication

### Tasks

- [x] 1.1 Create project folder structure
- [x] 1.2 Create planning documents
- [x] 1.3 Set up Python package (pyproject.toml)
- [x] 1.4 Create requirements.txt with dependencies
- [x] 1.5 Implement main window skeleton
- [x] 1.6 Implement OAuth authentication flow
- [x] 1.7 Token storage and management
- [x] 1.8 Basic settings management

### Deliverables
- [x] Runnable application with login screen
- [x] OAuth working end-to-end
- [x] Token persisted securely

---

## Phase 2: Core Chat (Week 3-4)

**Goal:** Chat interface and API integration

### Tasks

- [x] 2.1 Create chat widget layout
- [x] 2.2 Implement message bubble component
- [x] 2.3 Create input area with send button
- [x] 2.4 Implement Qwen API client
- [x] 2.5 Send/receive messages
- [x] 2.6 Stream responses in real-time
- [x] 2.7 Markdown rendering
- [x] 2.8 Syntax highlighting for code

### Deliverables
- [x] Working chat interface
- [x] Messages sent to Qwen API
- [x] Responses displayed with formatting

---

## Phase 3: File Attachments (Week 5-6)

**Goal:** File attachment system

### Tasks

- [x] 3.1 Create attachment preview component
- [x] 3.2 Implement drag-and-drop handler
- [x] 3.3 File picker dialog integration
- [x] 3.4 File type detection
- [x] 3.5 File validation (size, type)
- [x] 3.6 Remove attachments UI
- [x] 3.7 Send files with API requests
- [x] 3.8 Image preview for multimodal (Added support for base64)

### Deliverables
- [x] Drag-and-drop file attachments
- [x] File previews in input area
- [x] Files sent with messages

---

## Phase 4: Polish & Testing (Week 7-8)

**Goal:** Refinement, testing, and documentation

### Tasks

- [x] 4.1 Error handling and user feedback
- [x] 4.2 Loading indicators
- [x] 4.3 Settings dialog UI
- [x] 4.4 Rate Limit UI / Session handling
- [x] 4.5 Conversation history management (Sidebar)
- [x] 4.6 Unit tests for core modules
- [x] 4.7 Integration tests
- [x] 4.8 README documentation
- [x] 4.9 User guide

### Deliverables
- [x] Polished UI
- [x] Test coverage at ~75% (63 passing tests)
- [x] Complete documentation

---

## Phase 5: Release (Week 9)

**Goal:** Production release preparation

### Tasks

- [x] 5.5 Distribution packages built
- [x] 5.6 Prepared for GUI evolution

### Deliverables
- [x] Release candidate generated
- [x] Distribution packages built
- [x] Foundation for next-gen UI ready

---

## Phase 6: Floating Assistant (Current)

**Goal:** Transform into a persistent, frameless, and highly animated AI assistant.

### Tasks

- [x] 6.1 Implement `FloatingAssistant` (Expanding pill-shaped bar)
- [x] 6.2 Add `ChatHistoryPopup` (Floating message panel attached to bar)
- [x] 6.3 Implement `QPropertyAnimation` for smooth expansion/collapse
- [x] 6.4 Add screen clamping and boundary protection for dragging
- [x] 6.5 implement click-outside-to-collapse behavior
- [x] 6.6 Integrate existing OAuth/API client into new UI
- [x] 6.7 Add ⚙️ Settings/Auth button for easy Login/Logout
- [x] 6.8 Handle unauthenticated states with "Please login first" prompts

### Deliverables
- [x] Frameless, always-on-top floating button
- [x] Smooth expanding/collapsing interaction
- [x] Dynamic message window pinned to the assistant bar
- [x] Complete feature parity with old windowed UI


---

## Timeline Summary

| Phase | Status |
|-------|--------|
| 1: Foundation | ✅ Complete |
| 2: Core Chat | ✅ Complete |
| 3: Attachments | ✅ Complete |
| 4: Polish | ✅ Complete |
| 5: Release | ✅ Complete |
| 6: Floating Assistant | ✅ Complete |
| 7: Performance | ✅ Complete |

---

## Phase 7: Performance & Native Integration (Latest)

**Goal:** Future-proof the architecture with non-blocking threading and native `qwen-code` session compatibility.

### Tasks

- [x] 7.1 **Refactor to QThread** — Implement `APIServerWorker` to eliminate UI-blocking `asyncio` loops.
- [x] 7.2 **Native Session Service** — Implement `QwenSessionService` (Python port of `qwen-code` history engine).
- [x] 7.3 **JSONL Storage** — Switch persistence to `~/.qwen/tmp/<project_hash>/chats/*.jsonl` format.
- [x] 7.4 **Interaction Cleanup** — Resolve Click vs. Drag conflicts using Manhattan distance thresholds.
- [x] 7.5 **Instant Expand/Shrink** — Remove animation latency for a "snappy" high-performance feel.
- [x] 7.6 **Layout Stability** — Fix "Right-side push" bug to keep the widget anchored to its right-edge during resize.
- [x] 7.7 **Scrub Dependencies** — Remove `legacy_ui` and fix circular imports in `__init__.py`.

### Deliverables
- [x] Zero-UI-freeze streaming via QThread.
- [x] Full history interoperability with `qwen-code` CLI/IDE.
- [x] Stabilized frameless widget interactions.

---

## Current Status

**Active Phase:** Phase 6 - Floating Assistant Evolution  
**Progress:** 100% (New GUI Implemented)  
**Next Task:** Final verification of user interaction patterns

---

## Risk Management

| Risk | Impact | Mitigation |
|------|--------|------------|
| OAuth API changes | High | Integrated device flow (Done) |
| Rate limiting | Medium | Added visual indicator for API counts (Done) |
| Memory Limits | High | Added 10MB chunk/file restrictions (Done) |

---
