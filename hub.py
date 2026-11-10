#!/usr/bin/env python3
"""Personal terminal file manager. Configure the workspace in config.json."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "HubFileManager"
CONFIG = APP_DIR / "config.json"
DEFAULT_ROOT = str(Path.home() / "Documents")

def load_root() -> Path:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps({"workspace": DEFAULT_ROOT}, indent=2), encoding="utf-8")
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        root = Path(data.get("workspace", DEFAULT_ROOT)).expanduser()
    except Exception:
        root = Path(DEFAULT_ROOT)
    return root

def save_root(root: Path) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"workspace": str(root)}, indent=2), encoding="utf-8")

def pause():
    input("\nPress Enter to continue...")

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return str(n)

def entries(folder: Path):
    try:
        return sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return []

def copy_item(src: Path, dest: Path):
    dest = dest.expanduser()
    if dest.exists() and dest.is_dir():
        dest = dest / src.name
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return dest

def open_item(path: Path):
    try:
        if os.name == "nt":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as e:
        print(f"Could not open: {e}")
        pause()

def file_actions(path: Path):
    while True:
        clear()
        print(f"HUB  /  {path.name}\n")
        print(f"Path: {path}\n")
        print("1. Open with default application")
        print("2. Copy full path")
        print("3. Export / copy to another location")
        print("4. Save a copy inside workspace")
        print("5. Rename")
        print("6. Delete")
        print("0. Back")
        choice = input("\nChoose: ").strip()
        if choice == "1":
            open_item(path); pause()
        elif choice == "2":
            try:
                import pyperclip
                pyperclip.copy(str(path))
                print("Path copied to clipboard.")
            except Exception:
                print("Clipboard helper is unavailable. Copy this path:")
                print(path)
            pause()
        elif choice in ("3", "4"):
            if choice == "3":
                raw = input("Destination folder or full destination path: ").strip().strip('"')
                if not raw: continue
                dest = Path(raw)
            else:
                dest = load_root() / "saved_copies"
            try:
                result = copy_item(path, dest)
                print(f"Copied to: {result}")
            except Exception as e:
                print(f"Copy failed: {e}")
            pause()
        elif choice == "5":
            name = input("New name (include extension if needed): ").strip()
            if name:
                target = path.with_name(name)
                try:
                    path.rename(target)
                    return target
                except Exception as e:
                    print(f"Rename failed: {e}"); pause()
        elif choice == "6":
            confirm = input(f"Type DELETE to permanently delete '{path.name}': ")
            if confirm == "DELETE":
                try:
                    if path.is_dir(): shutil.rmtree(path)
                    else: path.unlink()
                    print("Deleted.")
                    return None
                except Exception as e:
                    print(f"Delete failed: {e}"); pause()
        elif choice == "0":
            return path

def browse(start: Path):
    current = start
    while True:
        clear()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    HUB  •  WORKSPACE                         ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"\nWorkspace: {start}")
        print(f"Current:   {current}\n")
        items = entries(current)
        if not items:
            print("(This folder is empty or cannot be read.)")
        for i, item in enumerate(items, 1):
            kind = "[DIR] " if item.is_dir() else "[FILE]"
            extra = ""
            if item.is_file():
                try: extra = f"  ({human_size(item.stat().st_size)})"
                except OSError: pass
            print(f"{i:>3}. {kind} {item.name}{extra}")
        print("\nCommands: number = open/select | .. = back | / = workspace | s = search")
        print("          c = copy path | o = open current folder | q = quit")
        raw = input("\n hub> ").strip()
        if raw.lower() == "q":
            return
        if raw == "..":
            if current != start and start in current.parents:
                current = current.parent
            continue
        if raw == "/":
            current = start; continue
        if raw.lower() == "o":
            open_item(current); continue
        if raw.lower() == "c":
            try:
                import pyperclip
                pyperclip.copy(str(current))
                print("Current folder path copied."); pause()
            except Exception:
                print(f"Path: {current}"); pause()
            continue
        if raw.lower() == "s":
            term = input("Search name contains: ").strip().lower()
            if term:
                matches = [p for p in start.rglob("*") if term in p.name.lower()]
                clear()
                print(f"Matches for '{term}':\n")
                for i, p in enumerate(matches[:200], 1):
                    print(f"{i:>3}. {p.relative_to(start)}")
                if len(matches) > 200: print("...showing first 200")
                pick = input("\nEnter result number to open, or Enter to return: ").strip()
                if pick.isdigit() and 1 <= int(pick) <= min(200, len(matches)):
                    selected = matches[int(pick)-1]
                    if selected.is_dir(): current = selected
                    else: file_actions(selected)
            continue
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(items):
                selected = items[idx]
                if selected.is_dir():
                    current = selected
                else:
                    file_actions(selected)
            continue
        print("Unknown command."); pause()

def main():
    root = load_root()
    if len(sys.argv) > 1 and sys.argv[1] in ("--set-workspace", "config"):
        raw = input(f"Workspace path [{root}]: ").strip().strip('"')
        if raw:
            new_root = Path(raw).expanduser()
            if not new_root.exists() or not new_root.is_dir():
                print("That folder does not exist."); return
            save_root(new_root)
            print(f"Workspace saved: {new_root}")
        return
    if not root.exists():
        print(f"Workspace folder not found:\n{root}")
        print("Run: hub config")
        return
    browse(root)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nExiting HUB.")
