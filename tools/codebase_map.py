# tools/codebase_map.py
import os, sys, io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "project_code_dump.md"

INCLUDE_EXT = {
    ".py", ".html", ".css", ".js", ".txt", ".md", ".json", ".yml", ".yaml", ".ini", ".cfg"
}
EXCLUDE_DIRS = {".git", ".github", "venv", ".venv", "__pycache__", "node_modules", "registered_faces", ".idea", ".vscode"}
EXCLUDE_FILES = {"database.db", "database.sqlite", ".env"}
MAX_FILE_BYTES = 200_000

def language_hint(p: Path) -> str:
    ext = p.suffix.lower()
    return {
        ".py": "python",
        ".html": "html",
        ".css": "css",
        ".js": "javascript",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".ini": "",
        ".cfg": "",
        ".md": "md",
        ".txt": ""
    }.get(ext, "")

def should_include(p: Path) -> bool:
    if p.is_dir():
        return False
    if p.name in EXCLUDE_FILES:
        return False
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return False
    if p.suffix.lower() not in INCLUDE_EXT:
        return False
    try:
        if p.stat().st_size > MAX_FILE_BYTES:
            return False
    except Exception:
        return False
    return True

def main():
    files = []
    for dp, dn, fn in os.walk(ROOT):
        dp_path = Path(dp)
        dn[:] = [d for d in dn if d not in EXCLUDE_DIRS]
        for name in fn:
            p = dp_path / name
            if should_include(p):
                files.append(p)

    files = sorted(files, key=lambda x: str(x).lower())

    with io.open(OUT, "w", encoding="utf-8", errors="ignore") as f:
        f.write("# Project Code Dump\n\n")
        for p in files:
            rel = p.relative_to(ROOT).as_posix()
            lang = language_hint(p)
            f.write(f"\n---\n\n## {rel}\n\n")
            if lang:
                f.write(f"```{lang}\n")
            else:
                f.write("```\n")
            try:
                f.write(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception as e:
                f.write(f"<< error reading file: {e} >>")
            f.write("\n```\n")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
