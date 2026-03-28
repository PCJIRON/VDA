# Phase 5 Plan: Release Preparation

**Phase:** 5  
**Title:** Release Preparation  
**Duration:** 1 week  
**Start Date:** 2026-03-28  
**Target End Date:** 2026-04-04

---

## 🎯 Phase Goal

Prepare Qwen Desktop v0.4.0 for public release with proper versioning, packaging, and distribution.

---

## 📋 Task Breakdown

### Wave 1: Version & Packaging (High Priority)

#### Task 5.1: Version Bump to 0.4.0
**File:** `qwen_desktop/__init__.py`

**Implementation:**
```python
__version__ = "0.4.0"
```

**Estimated Time:** 0.5 hours

---

#### Task 5.2: Update pyproject.toml
**File:** `pyproject.toml`

**Changes:**
- Update version to 0.4.0
- Add entry point script
- Add package metadata

**Estimated Time:** 1 hour

---

#### Task 5.3: Create Setup Script
**File:** `setup.py` (optional)

**Purpose:** Alternative installation method

**Estimated Time:** 1 hour

---

### Wave 2: Distribution (High Priority)

#### Task 5.4: Build Distribution Package
**Commands:**
```bash
py -m pip install build
py -m build
```

**Output:**
- `dist/qwen_desktop-0.4.0.tar.gz`
- `dist/qwen_desktop-0.4.0-py3-none-any.whl`

**Estimated Time:** 1 hour

---

#### Task 5.5: Create Windows Executable (Optional)
**Tool:** PyInstaller or cx_Freeze

**Implementation:**
```bash
py -m pip install pyinstaller
pyinstaller --onefile --windowed --name "Qwen Desktop" run.py
```

**Estimated Time:** 3 hours

---

#### Task 5.6: Create Installer (Optional)
**Tool:** Inno Setup (Windows)

**Estimated Time:** 4 hours

---

### Wave 3: Documentation Finalization (High Priority)

#### Task 5.7: Final README Review
**File:** `README.md`

**Checklist:**
- [ ] Installation instructions complete
- [ ] Usage examples working
- [ ] Screenshots added
- [ ] Badges working
- [ ] Links valid

**Estimated Time:** 2 hours

---

#### Task 5.8: Create Quick Start Guide
**File:** `docs/QUICKSTART.md`

**Sections:**
- 5-minute setup
- First login
- Send first message
- Attach first file

**Estimated Time:** 2 hours

---

#### Task 5.9: Create Troubleshooting Guide
**File:** `docs/TROUBLESHOOTING.md`

**Sections:**
- Common errors
- OAuth issues
- File attachment problems
- Platform-specific issues

**Estimated Time:** 2 hours

---

### Wave 4: Testing & Validation (High Priority)

#### Task 5.10: Final Test Run
**Command:**
```bash
py -m pytest tests/ -v --tb=short
```

**Expected:** 63/63 tests passing

**Estimated Time:** 1 hour

---

#### Task 5.11: Manual Testing Checklist
**Test Scenarios:**
- [ ] Application launches
- [ ] OAuth login works
- [ ] File attachments work
- [ ] Chat sends/receives messages
- [ ] Conversations save/load
- [ ] Keyboard shortcuts work
- [ ] Rate limit displays

**Estimated Time:** 2 hours

---

#### Task 5.12: Cross-Platform Smoke Test
**Platforms:**
- Windows 10/11 ✅ (tested)
- macOS 11+ ⏳ (documented)
- Linux Ubuntu 20.04+ ⏳ (documented)

**Estimated Time:** 2 hours

---

### Wave 5: Release (High Priority)

#### Task 5.13: Create GitHub Release
**Steps:**
1. Push to main branch
2. Create tag v0.4.0
3. Create GitHub release
4. Add release notes
5. Attach binaries (if created)

**Estimated Time:** 1 hour

---

#### Task 5.14: Publish to PyPI (Optional)
**Commands:**
```bash
py -m pip install twine
py -m twine upload dist/*
```

**Estimated Time:** 1 hour

---

#### Task 5.15: Announce Release
**Channels:**
- GitHub Discussions
- README update
- Social media (optional)

**Estimated Time:** 1 hour

---

## 📅 Timeline

| Week | Waves | Deliverables |
|------|-------|--------------|
| **Week 1** | Wave 1-5 | Version bump, build, docs, testing, release |

---

## 🎯 Success Criteria

```bash
# Version is 0.4.0
py -c "import qwen_desktop; print(qwen_desktop.__version__)"
# → 0.4.0

# All tests pass
py -m pytest tests/ -v
# → 63 passed

# Package builds
py -m build
# → dist/qwen_desktop-0.4.0.*

# Application runs
py run.py
# → Application launches successfully
```

### Metrics

| Metric | Target |
|--------|--------|
| Version | 0.4.0 |
| Tests | 63/63 passing |
| Documentation | Complete |
| Distribution | Wheel + Tarball |
| Release | GitHub + Optional PyPI |

---

## 📦 Files to Create/Update

### Version Updates
- `qwen_desktop/__init__.py` - `__version__ = "0.4.0"`
- `pyproject.toml` - version field
- `docs/RELEASE-0.4.0.md` - Already created

### New Files (Optional)
- `setup.py` - Alternative setup
- `docs/QUICKSTART.md` - Quick start guide
- `docs/TROUBLESHOOTING.md` - Troubleshooting guide
- `.github/workflows/release.yml` - CI/CD for releases

---

## 🔗 Dependencies

### Internal
- Phases 1-4 complete ✅
- All tests passing ✅
- Documentation complete ✅

### External
- None (no new dependencies needed)

---

## ⚠️ Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Build fails | High | Test build process before release |
| Tests fail on clean install | High | Test in fresh virtualenv |
| PyPI publish fails | Medium | Test with TestPyPI first |
| Windows exe size too large | Low | Document size, provide alternatives |

---

## 📝 Notes

1. **Priority Order:** Version bump → Build → Docs → Test → Release
2. **PyPI Publishing:** Optional for first release, can do later
3. **Windows Executable:** Nice to have, not required for v0.4.0
4. **Release Notes:** Already created in `docs/RELEASE-0.4.0.md`

---

## ✅ Phase 5 Checklist

- [ ] Task 5.1: Version Bump to 0.4.0
- [ ] Task 5.2: Update pyproject.toml
- [ ] Task 5.3: Create Setup Script (optional)
- [ ] Task 5.4: Build Distribution Package
- [ ] Task 5.5: Create Windows Executable (optional)
- [ ] Task 5.6: Create Installer (optional)
- [ ] Task 5.7: Final README Review
- [ ] Task 5.8: Create Quick Start Guide
- [ ] Task 5.9: Create Troubleshooting Guide
- [ ] Task 5.10: Final Test Run
- [ ] Task 5.11: Manual Testing Checklist
- [ ] Task 5.12: Cross-Platform Smoke Test
- [ ] Task 5.13: Create GitHub Release
- [ ] Task 5.14: Publish to PyPI (optional)
- [ ] Task 5.15: Announce Release

**Total Tasks:** 15  
**Estimated Time:** 25 hours  
**Duration:** 1 week

---

**Ready to Execute:** Run `/gsd:execute-phase 5` to start Phase 5.
