# Debug Session 3: Critical Code Review Fixes

**Date:** 2026-03-28  
**Issue:** 5 critical issues from code review blocking v0.4.0 release

---

## Critical Issues to Fix

### P0: Security & Functionality Blockers

1. **Plaintext OAuth Credential Storage**
   - **File:** `qwen_desktop/auth/qwen_auth_gui.py:327-330`
   - **Issue:** Tokens saved to plaintext JSON instead of keyring
   - **Risk:** Token theft via filesystem access

2. **Rate Limiter Bypass via Restart**
   - **File:** `qwen_desktop/utils/rate_limiter.py:27-32`
   - **Issue:** State resets on app restart
   - **Risk:** Unlimited requests via restarts

3. **Rate Limiter Algorithm Incorrect**
   - **File:** `qwen_desktop/utils/rate_limiter.py:66-72`
   - **Issue:** Continuous refill allows 10x quota
   - **Risk:** API quota violations

4. **Syntax Error in Error Handling**
   - **File:** `qwen_desktop/auth/qwen_device_flow.py:177-202`
   - **Issue:** Error handling block outside try block
   - **Risk:** NameError crashes

5. **Bare except Clause**
   - **File:** `qwen_desktop/auth/qwen_auth_gui.py:279-287`
   - **Issue:** Silent exception swallowing
   - **Risk:** Undebuggable failures

---

## Fix Plan

### Fix 1: Use Secure Credential Storage

**File:** `qwen_desktop/auth/qwen_auth_gui.py`

**Changes:**
1. Remove `_save_credentials()` method
2. Use `Credentials` class from `qwen_desktop.auth.credentials`
3. Update `_on_auth_success()` to use secure storage

**Code:**
```python
from qwen_desktop.auth.credentials import Credentials

def _on_auth_success(self, credentials: dict):
    # Save to keyring instead of plaintext file
    creds = Credentials()
    creds.save_access_token(credentials["access_token"])
    creds.save_refresh_token(credentials["refresh_token"])
    creds.save_token_expiry(datetime.fromisoformat(credentials["token_expiry"]))
```

---

### Fix 2: Persist Rate Limiter State

**File:** `qwen_desktop/utils/rate_limiter.py`

**Changes:**
1. Add `_state_path` attribute
2. Implement `_load_state()` and `_save_state()` methods
3. Call `_load_state()` in `__init__`
4. Call `_save_state()` after token changes

**Code:**
```python
def __init__(self, ...):
    self._state_path = Path.home() / ".qwen-desktop" / "rate_limit.json"
    self._load_state()

def _load_state(self):
    if self._state_path.exists():
        with open(self._state_path) as f:
            state = json.load(f)
            self.tokens = state["tokens"]
            self.last_refill = datetime.fromisoformat(state["last_refill"])

def _save_state(self):
    self._state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(self._state_path, "w") as f:
        json.dump({
            "tokens": self.tokens,
            "last_refill": self.last_refill.isoformat()
        }, f)
```

---

### Fix 3: Fix Rate Limiter Algorithm

**File:** `qwen_desktop/utils/rate_limiter.py`

**Changes:**
1. Replace continuous refill with fixed window reset
2. Reset at midnight UTC

**Code:**
```python
def _refill(self) -> None:
    now = datetime.now()
    # Reset at midnight UTC (fixed window)
    if now.date() > self.last_refill.date():
        self.tokens = float(self.max_requests)
        self.last_refill = now
```

---

### Fix 4: Fix Indentation Error

**File:** `qwen_desktop/auth/qwen_device_flow.py`

**Changes:**
1. Indent lines 177-202 to be inside try block

**Code:**
```python
try:
    response = client.post(...)
    
    if response.status_code != 200:
        # ... error handling
        return
    
    data = response.json()
    
    # Check for error - NOW INSIDE TRY BLOCK
    if "error" in data:
        error = data["error"]
        # ... error handling
        return
    
    # Success handling
    # ...
    
except Exception as e:
    print(f"Polling failed: {e}")
    continue
```

---

### Fix 5: Fix Bare except Clause

**File:** `qwen_desktop/auth/qwen_auth_gui.py`

**Changes:**
1. Replace bare `except:` with `except Exception as e:`
2. Call `_on_auth_failed()` with error message

**Code:**
```python
try:
    # ... polling logic
except Exception as e:
    self._on_auth_failed(f"Polling error: {e}")
    return
```

---

## Test Plan

After all fixes:
1. Run `py -m pytest tests/ -v` - expect 63 tests passing
2. Manual OAuth test - verify tokens saved to keyring
3. Manual rate limit test - verify persists across restart
4. Manual rate limit test - verify daily quota enforced
5. Manual OAuth test - verify no crashes on polling errors

---

**Status:** Ready to execute fixes
