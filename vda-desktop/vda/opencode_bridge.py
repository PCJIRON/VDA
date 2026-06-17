"""Bridge between VDA (Python) and the opencode Go engine via subprocess.

Spans persistent toolserver processes for stateful tool execution (file_edit
read-before-edit tracking) with fallback to one-shot mode.
Also provides an agentd subprocess that runs the full opencode agent loop.
"""

import json
import logging
import os
import subprocess
import threading
from pathlib import Path
from collections.abc import Iterator
from typing import Any, Optional

logger = logging.getLogger(__name__)

ENGINE_DIR = Path(__file__).resolve().parent.parent / "opencode-engine"
TOOLSERVER_BIN = ENGINE_DIR / "toolserver.exe"
AGENTD_BIN = ENGINE_DIR / "agentd.exe"

_lock = threading.Lock()
_client: Optional["ToolServerClient"] = None


def _ensure_binary(name: str = "toolserver") -> Path:
    bin_map = {
        "toolserver": (TOOLSERVER_BIN, "./cmd/toolserver/"),
        "agentd": (AGENTD_BIN, "./cmd/agentd/"),
    }
    if name not in bin_map:
        raise ValueError(f"unknown binary: {name}")
    bin_path, build_target = bin_map[name]
    if bin_path.exists():
        return bin_path
    logger.info("Building opencode %s binary...", name)
    result = subprocess.run(
        ["go", "build", "-o", str(bin_path), build_target],
        cwd=str(ENGINE_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if not bin_path.exists():
        out = result.stdout + result.stderr
        logger.error("Build failed: %s", out[:500])
        raise RuntimeError(
            f"{name} binary not found and build failed.\n"
            f"Install Go and run: cd opencode-engine && go build -o {bin_path.name} {build_target}"
        )
    logger.info("%s binary built at %s", name, bin_path)
    return bin_path


# ---------------------------------------------------------------------------
# Persistent toolserver client
# ---------------------------------------------------------------------------


class ToolServerClient:
    """Manages a persistent toolserver subprocess for stateful tool execution.

    The process reads JSON-line requests from stdin and writes JSON-line
    responses to stdout. State (file tracking for edit safety) persists
    across calls within the same process.
    """

    def __init__(self, cwd: Optional[str] = None) -> None:
        binary = _ensure_binary()
        self._cwd = cwd or os.getcwd()
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._start(binary)

    def _start(self, binary: Path) -> None:
        logger.debug("[opencode] Starting persistent toolserver...")
        self._proc = subprocess.Popen(
            [str(binary), "--persist"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._cwd,
            text=True,
            encoding="utf-8",
        )

    def call(self, tool_name: str, params: dict) -> dict[str, Any]:
        if self._proc is None or self._proc.poll() is not None:
            logger.warning("[opencode] Toolserver not running, restarting...")
            self._start(_ensure_binary())

        req = json.dumps({"tool": tool_name, "params": params})
        logger.debug("[opencode] persistent tool=%s params=%s", tool_name, str(params)[:200])

        with self._lock:
            assert self._proc is not None and self._proc.stdin is not None
            self._proc.stdin.write(req + "\n")
            self._proc.stdin.flush()

            line = self._proc.stdout.readline() if self._proc.stdout else ""
            if not line:
                err = self._proc.stderr.read().decode("utf-8", errors="replace") if self._proc.stderr else ""
                raise RuntimeError(f"Toolserver closed: {err.strip()}")

            resp = json.loads(line)

        if resp.get("is_error"):
            return {"type": "text", "content": f"Error: {resp['content']}", "is_error": True}

        try:
            return json.loads(resp["content"])
        except (json.JSONDecodeError, KeyError):
            return {"type": "text", "content": resp.get("content", ""), "is_error": False}

    def close(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                self._proc = None

    def __del__(self) -> None:
        self.close()


def get_client(cwd: Optional[str] = None) -> ToolServerClient:
    """Get or create the global persistent toolserver client."""
    global _client
    if _client is None:
        _client = ToolServerClient(cwd=cwd)
    return _client


def call_tool(tool_name: str, params: dict, cwd: Optional[str] = None) -> dict[str, Any]:
    """Call an opencode Go tool, preferring persistent mode with fallback.

    Args:
        tool_name: Tool name (view, glob, grep, ls, edit, write, patch, diagnostics, sourcegraph)
        params: Tool parameters as a dict
        cwd: Working directory

    Returns:
        Parsed JSON response dict with keys: type, content, metadata, is_error
    """
    # Auto-inject session/message IDs for tools that need them
    if tool_name in ("edit", "write", "patch"):
        params.setdefault("session_id", "vda-session")
        params.setdefault("message_id", "vda-msg-1")

    try:
        client = get_client(cwd=cwd)
        return client.call(tool_name, params)
    except Exception as e:
        logger.warning("[opencode] Persistent call failed, falling back to one-shot: %s", e)
        return _call_tool_oneshot(tool_name, params, cwd=cwd)


def _call_tool_oneshot(tool_name: str, params: dict, cwd: Optional[str] = None) -> dict[str, Any]:
    """Fallback: spawn a fresh subprocess per call."""
    binary = _ensure_binary("toolserver")
    cmd = [str(binary), tool_name]
    input_bytes = json.dumps(params).encode("utf-8")

    result = subprocess.run(
        cmd,
        input=input_bytes,
        capture_output=True,
        cwd=cwd or os.getcwd(),
        timeout=60,
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    if result.returncode != 0:
        err = stderr.strip()
        return {"type": "text", "content": f"Error: {err}", "is_error": True}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        return {"type": "text", "content": f"Error: failed to parse response: {e}", "is_error": True}


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def view(file_path: str, offset: int = 0, limit: int = 2000) -> dict:
    return call_tool("view", {"file_path": file_path, "offset": offset, "limit": limit})


def glob(pattern: str, path: Optional[str] = None) -> dict:
    p: dict[str, Any] = {"pattern": pattern}
    if path:
        p["path"] = path
    return call_tool("glob", p)


def grep(pattern: str, path: Optional[str] = None,
         include: Optional[str] = None, literal_text: bool = False) -> dict:
    p: dict[str, Any] = {"pattern": pattern, "literal_text": literal_text}
    if path:
        p["path"] = path
    if include:
        p["include"] = include
    return call_tool("grep", p)


def ls(path: Optional[str] = None, ignore: Optional[list[str]] = None) -> dict:
    p: dict[str, Any] = {"path": path or "."}
    if ignore:
        p["ignore"] = ignore
    return call_tool("ls", p)


def edit(file_path: str, old_string: str, new_string: str) -> dict:
    return call_tool("edit", {"file_path": file_path, "old_string": old_string, "new_string": new_string})


def file_write(file_path: str, content: str) -> dict:
    return call_tool("write", {"file_path": file_path, "content": content})


def patch(patch_text: str) -> dict:
    return call_tool("patch", {"patch_text": patch_text})


def diagnostics(file_path: str) -> dict:
    return call_tool("diagnostics", {"file_path": file_path})


def sourcegraph(query: str, count: int = 10, context_window: int = 5, timeout: int = 15) -> dict:
    return call_tool("sourcegraph", {
        "query": query, "count": count,
        "context_window": context_window, "timeout": timeout,
    })


# ---------------------------------------------------------------------------
# AgentD — full opencode agent loop as subprocess
# ---------------------------------------------------------------------------

def run_agentd(
    task: str,
    provider: str,
    model: str,
    api_key: str,
    base_url: str,
    working_dir: str = "",
    system_prompt: str = "",
) -> Iterator[dict[str, Any]]:
    """Run the opencode agent loop as a subprocess, yielding streaming events.

    Each yielded dict has keys: type, content, tool_name, tool_input,
    tool_result, session_id, done.

    Yields:
        Streaming events from the Go agent.
    """
    binary = _ensure_binary("agentd")
    req_payload: dict[str, Any] = {
        "task": task,
        "config": {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
        },
    }
    if working_dir:
        req_payload["working_dir"] = working_dir
    if system_prompt:
        req_payload["system_prompt"] = system_prompt
    req = json.dumps(req_payload)

    proc = subprocess.Popen(
        [str(binary)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_dir or os.path.expanduser("~"),
        text=True,
        encoding="utf-8",
    )

    assert proc.stdin is not None
    proc.stdin.write(req + "\n")
    proc.stdin.flush()
    proc.stdin.close()

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            yield event
            if event.get("done"):
                break
        except json.JSONDecodeError:
            logger.warning("[agentd] Failed to parse event line: %s", line[:200])
            continue

    proc.wait(timeout=10)
    if proc.returncode != 0:
        stderr_output = proc.stderr.read() if proc.stderr else ""
        if stderr_output:
            logger.error("[agentd] stderr: %s", stderr_output[:500])
            yield {"type": "error", "content": stderr_output[:500], "done": True}
