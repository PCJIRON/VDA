# Project Roadmap

**Project:** Qwen Desktop  
**Version:** 0.1.0

---

## Phase 1: Foundation (Week 1-2)

**Goal:** Basic application structure and OAuth authentication

### Tasks

- [x] 1.1 Create project folder structure
- [x] 1.2 Create planning documents
- [ ] 1.3 Set up Python package (pyproject.toml)
- [ ] 1.4 Create requirements.txt with dependencies
- [ ] 1.5 Implement main window skeleton
- [ ] 1.6 Implement OAuth authentication flow
- [ ] 1.7 Token storage and management
- [ ] 1.8 Basic settings management

### Deliverables
- Runnable application with login screen
- OAuth working end-to-end
- Token persisted securely

### Success Criteria
```bash
py run.py
# → Application launches
# → Can login with Qwen OAuth
# → Token saved for next session
```

---

## Phase 2: Core Chat (Week 3-4)

**Goal:** Chat interface and API integration

### Tasks

- [ ] 2.1 Create chat widget layout
- [ ] 2.2 Implement message bubble component
- [ ] 2.3 Create input area with send button
- [ ] 2.4 Implement Qwen API client
- [ ] 2.5 Send/receive messages
- [ ] 2.6 Stream responses in real-time
- [ ] 2.7 Markdown rendering
- [ ] 2.8 Syntax highlighting for code

### Deliverables
- Working chat interface
- Messages sent to Qwen API
- Responses displayed with formatting

### Success Criteria
```bash
py run.py
# → Can send messages
# → AI responses appear with markdown
# → Code blocks highlighted
```

---

## Phase 3: File Attachments (Week 5-6)

**Goal:** File attachment system

### Tasks

- [ ] 3.1 Create attachment preview component
- [ ] 3.2 Implement drag-and-drop handler
- [ ] 3.3 File picker dialog integration
- [ ] 3.4 File type detection
- [ ] 3.5 File validation (size, type)
- [ ] 3.6 Remove attachments UI
- [ ] 3.7 Send files with API requests
- [ ] 3.8 Image preview for multimodal

### Deliverables
- Drag-and-drop file attachments
- File previews in input area
- Files sent with messages

### Success Criteria
```bash
py run.py
# → Can drag files onto input
# → Files shown as previews
# → Files sent with message
```

---

## Phase 4: Polish & Testing (Week 7-8)

**Goal:** Refinement, testing, and documentation

### Tasks

- [ ] 4.1 Error handling and user feedback
- [ ] 4.2 Loading indicators
- [ ] 4.3 Settings dialog UI
- [ ] 4.4 Model selection
- [ ] 4.5 Conversation history management
- [ ] 4.6 Unit tests for core modules
- [ ] 4.7 Integration tests
- [ ] 4.8 README documentation
- [ ] 4.9 User guide

### Deliverables
- Polished UI
- Test coverage > 70%
- Complete documentation

### Success Criteria
```bash
py -m pytest tests/ -v
# → All tests pass
# → Coverage > 70%
```

---

## Phase 5: Release (Week 9)

**Goal:** Production release preparation

### Tasks

- [ ] 5.1 Performance optimization
- [ ] 5.2 Cross-platform testing
- [ ] 5.3 Build scripts for distribution
- [ ] 5.4 Installer creation (optional)
- [ ] 5.5 Release notes
- [ ] 5.6 Version 0.1.0 release

### Deliverables
- Release candidate
- Distribution packages
- Release announcement

---

## Timeline Summary

| Phase | Duration | End Date |
|-------|----------|----------|
| 1: Foundation | Week 1-2 | 2026-04-11 |
| 2: Core Chat | Week 3-4 | 2026-04-25 |
| 3: Attachments | Week 5-6 | 2026-05-09 |
| 4: Polish | Week 7-8 | 2026-05-23 |
| 5: Release | Week 9 | 2026-05-30 |

---

## Current Status

**Active Phase:** Phase 1 - Foundation  
**Progress:** 20% (2/10 tasks complete)  
**Next Task:** Set up Python package configuration

---

## Risk Management

| Risk | Impact | Mitigation |
|------|--------|------------|
| OAuth API changes | High | Monitor Qwen API docs |
| PyQt compatibility | Medium | Test on all platforms |
| Rate limiting | Medium | Implement backoff |
| Token security | High | Use OS keyring |

---

## Dependencies

### Blockers
- None currently

### Upcoming
- Qwen API access for testing
- OAuth credentials for development

---

## Notes

- Focus on OAuth and file attachments as priority features
- Maintain modular structure throughout development
- Test frequently with `py run.py`
- Write tests alongside features
