import os
import subprocess
import threading
import time
import uuid
import tempfile
import logging

logger = logging.getLogger(__name__)

class PersistentShell:
    """A persistent shell session that maintains state across commands.
    Mimics opencode/internal/llm/tools/shell/shell.go logic.
    """
    def __init__(self, cwd=None):
        self.cwd = cwd or os.getcwd()
        self.process = None
        self.is_windows = os.name == 'nt'
        self.lock = threading.Lock()
        self.start_shell()

    def start_shell(self):
        """Spawns the background shell process."""
        try:
            if self.is_windows:
                self.process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, # We won't read this directly
                    stderr=subprocess.PIPE, # We won't read this directly
                    cwd=self.cwd,
                    text=True,
                    bufsize=1
                )
            else:
                self.process = subprocess.Popen(
                    ["bash"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    text=True,
                    bufsize=1
                )
            logger.info("[PersistentShell] Started background shell at %s", self.cwd)
        except Exception as e:
            logger.error("[PersistentShell] Failed to start shell: %s", e)

    def execute(self, command: str, timeout: int = 30) -> str:
        """Executes a command in the persistent shell sequentially."""
        with self.lock:
            return self._exec_command(command, timeout)

    def _exec_command(self, command: str, timeout: int) -> str:
        if not self.process or self.process.poll() is not None:
            logger.info("[PersistentShell] Shell was dead. Restarting.")
            self.start_shell()

        uid = str(uuid.uuid4())
        tmp_dir = tempfile.gettempdir()
        
        stdout_file = os.path.join(tmp_dir, f"vda-stdout-{uid}.txt")
        stderr_file = os.path.join(tmp_dir, f"vda-stderr-{uid}.txt")
        status_file = os.path.join(tmp_dir, f"vda-status-{uid}.txt")
        cwd_file = os.path.join(tmp_dir, f"vda-cwd-{uid}.txt")
        cmd_file = ""

        try:
            if self.is_windows:
                cmd_file = os.path.join(tmp_dir, f"vda-cmd-{uid}.ps1")
                with open(cmd_file, "w", encoding="utf-8") as f:
                    f.write(command)
                
                # Use dot-sourcing to run in the current scope
                script = f"""
. "{cmd_file}" > "{stdout_file}" 2> "{stderr_file}"
$exitCode = $LASTEXITCODE
if ($exitCode -eq $null) {{ if ($?) {{ $exitCode = 0 }} else {{ $exitCode = 1 }} }}
(Get-Location).Path > "{cwd_file}"
$exitCode > "{status_file}"
"""
            else:
                cmd_file = os.path.join(tmp_dir, f"vda-cmd-{uid}.sh")
                with open(cmd_file, "w", encoding="utf-8") as f:
                    f.write(command)
                
                script = f"""
source "{cmd_file}" > "{stdout_file}" 2> "{stderr_file}"
EXEC_EXIT_CODE=$?
pwd > "{cwd_file}"
echo $EXEC_EXIT_CODE > "{status_file}"
"""

            # Write the wrapper script to the shell's stdin
            self.process.stdin.write(script + "\n")
            self.process.stdin.flush()

            start_time = time.time()
            done = False
            while time.time() - start_time < timeout:
                if os.path.exists(status_file) and os.path.getsize(status_file) > 0:
                    done = True
                    break
                time.sleep(0.05)

            if not done:
                logger.warning("[PersistentShell] Command timed out after %s seconds. Killing shell.", timeout)
                self.process.kill()
                return f"Error: Command timed out after {timeout} seconds."

            # Read outputs
            def read_file(path):
                if os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read().strip()
                    except UnicodeError:
                        with open(path, "r", encoding="utf-16") as f:
                            return f.read().strip()
                return ""

            stdout = read_file(stdout_file)
            stderr = read_file(stderr_file)
            status = read_file(status_file)
            new_cwd = read_file(cwd_file)

            if new_cwd:
                self.cwd = new_cwd

            output = ""
            if stdout:
                output += stdout
            if stderr:
                output += f"\nSTDERR:\n{stderr}"
            if not output:
                output = f"Command executed successfully (exit code {status}), no output."

            return output

        except Exception as e:
            return f"Error executing command: {str(e)}"
        finally:
            # Cleanup all temporary files
            for f in [stdout_file, stderr_file, status_file, cwd_file, cmd_file]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
