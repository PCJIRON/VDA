import os

replacements = [
    ("vda", "vda"),
    ("vda-desktop", "vda-desktop"),
    ("VDADesktop", "VDADesktop"),
    ("VDA", "VDA"),
    ("vda", "vda")
]

skip_dirs = {".git", "__pycache__", ".gemini", "venv", "graphify-out", ".agents", ".planning", ".pytest_cache", ".ruff_cache"}
valid_extensions = {".py", ".md", ".toml", ".json", ".txt", ".mdx", ".yml", ".yaml"}

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filepath} (unreadable: {e})")
        return

    original = content
    for old_str, new_str in replacements:
        content = content.replace(old_str, new_str)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    # 1. Replace content
    root_dir = r"c:\Users\uscha\OneDrive\Desktop\vda\VDA"
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Mutate dirnames in-place to skip
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        for file in filenames:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions:
                filepath = os.path.join(dirpath, file)
                process_file(filepath)
                
    # 2. Rename directories
    # Rename inner package: VDA\vda-desktop\vda -> VDA\vda-desktop\vda
    old_pkg = os.path.join(root_dir, "vda-desktop", "vda")
    new_pkg = os.path.join(root_dir, "vda-desktop", "vda")
    if os.path.exists(old_pkg):
        os.rename(old_pkg, new_pkg)
        print(f"Renamed {old_pkg} to {new_pkg}")
        
    # Rename outer folder: VDA\vda-desktop -> VDA\vda-desktop
    old_root = os.path.join(root_dir, "vda-desktop")
    new_root = os.path.join(root_dir, "vda-desktop")
    if os.path.exists(old_root):
        os.rename(old_root, new_root)
        print(f"Renamed {old_root} to {new_root}")

if __name__ == "__main__":
    main()
