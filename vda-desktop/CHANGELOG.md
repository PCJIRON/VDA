# Changelog

All notable changes to VDA Desktop will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- macOS physical testing
- Linux physical testing
- Startup performance optimization
- Message timestamps
- Export conversation feature

---

## [0.4.0] - 2026-03-28

### Added

#### Phase 1: Foundation
- OAuth 2.0 authentication with VDA/Google
- File attachment system (picker + validation)
- Chat UI with markdown rendering
- Settings management
- 31 unit tests

#### Phase 2: Core Chat Enhancements
- Drag-and-drop file attachments
- Typing indicator (animated)
- Copy message functionality
- Conversation persistence (save/load)
- Keyboard shortcuts (Ctrl+N, Ctrl+O, Ctrl+S)

#### Phase 3: File Attachments Enhancements
- Send files with VDA API (base64 encoding)
- Rate limiting (1,000 requests/day)
- Enhanced error handling with retry
- Conversation sidebar UI
- 32 additional tests (63 total)

#### Phase 4: Polish & Testing (Partial)
- Cross-platform testing documentation
- Async conversation loading (QThread)
- Rate limit UI indicator (color-coded)
- User Guide documentation
- Developer Guide documentation
- Updated README with features

### Fixed

#### Security
- Memory DoS prevention (10MB file size limit)
- Rate limiter thread safety (threading.Lock)
- Token calculation edge cases

#### Runtime
- Unused `has_attachments` parameter removed
- Attachment content now sent (not placeholder)
- 4xx errors not retried unnecessarily

#### Code Quality
- Type hint consistency (`Optional[str]`)
- Import organization

### Changed

- User-Agent updated to "VDA-Desktop/0.4.0"
- Conversation loading now async (non-blocking)
- Rate limit display in toolbar

### Technical

- **Total Lines:** ~7,500
- **Test Coverage:** 63 tests passing
- **Commits:** 25+
- **Files Created:** 20+

---

## [0.1.0] - 2026-03-28

### Added

- Initial project structure
- Basic OAuth authentication flow
- File picker dialog
- Chat interface skeleton
- Planning documents

### Technical

- PyQt6 integration
- Token storage with OS keyring
- Basic settings management

---

## Version History

| Version | Date | Phase | Status |
|---------|------|-------|--------|
| 0.4.0 | 2026-03-28 | Phase 1-4 | ✅ Complete |
| 0.1.0 | 2026-03-28 | Phase 1 | ✅ Complete |

---

## Upcoming (v0.5.0)

- Full Phase 4 completion
- macOS testing
- Linux testing
- Performance optimizations
- Additional polish features

---

**[Unreleased]:** Compare changes at `HEAD`
**[0.4.0]:** Initial complete release with Phases 1-4
