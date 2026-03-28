"""
Qwen OAuth authentication using qwen-code CLI.

This delegates OAuth to the qwen-code extension which already works.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class QwenCLIAuth:
    """Authenticate using qwen-code CLI."""
    
    def __init__(self):
        self.qwen_path = self._find_qwen_cli()
    
    def _find_qwen_cli(self) -> Optional[Path]:
        """Find qwen-code CLI executable."""
        # Try common locations
        possible_paths = [
            Path(sys.executable).parent / "qwen",
            Path(sys.executable).parent / "qwen.exe",
            Path.home() / ".local" / "bin" / "qwen",
            Path("/usr/local/bin/qwen"),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                return path
        
        # Try PATH
        import shutil
        qwen_in_path = shutil.which("qwen")
        if qwen_in_path:
            return Path(qwen_in_path)
        
        return None
    
    def is_available(self) -> bool:
        """Check if qwen-code CLI is available."""
        return self.qwen_path is not None
    
    def login(self) -> bool:
        """Run qwen-code login command."""
        if not self.qwen_path:
            print("❌ qwen-code CLI not found")
            print("Install it: pip install @qwen-code/qwen-code")
            return False
        
        try:
            print(f"🔐 Running: {self.qwen_path} auth qwen-oauth")
            result = subprocess.run(
                [str(self.qwen_path), "auth", "qwen-oauth"],
                capture_output=False,
                text=True,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def get_token(self) -> Optional[str]:
        """Get current access token from qwen-code credentials."""
        # qwen-code stores credentials in ~/.qwen/oauth_creds.json
        import json
        
        creds_path = Path.home() / ".qwen" / "oauth_creds.json"
        if not creds_path.exists():
            return None
        
        try:
            with open(creds_path, "r") as f:
                creds = json.load(f)
            
            return creds.get("access_token")
        except Exception as e:
            print(f"❌ Failed to read credentials: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if already authenticated."""
        return self.get_token() is not None


if __name__ == "__main__":
    auth = QwenCLIAuth()
    
    if not auth.is_available():
        print("❌ qwen-code CLI not found")
        print("\nInstall it:")
        print("  pip install @qwen-code/qwen-code")
        sys.exit(1)
    
    print(f"✅ Found qwen-code CLI at: {auth.qwen_path}")
    
    if auth.is_authenticated():
        print("✅ Already authenticated")
        token = auth.get_token()
        print(f"Token: {token[:20]}...")
    else:
        print("🔐 Not authenticated")
        if auth.login():
            print("✅ Login successful!")
        else:
            print("❌ Login failed")
            sys.exit(1)
