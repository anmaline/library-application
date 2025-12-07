"""
Entry-point helpers: argument parsing and main function.
"""
import os
import sys
from typing import List, Optional, Tuple

from .bootstrap import ensure_setup
from .cli import cli_main
from .web import web_main


def parse_args(argv: List[str]) -> Tuple[Optional[str], bool]:
    """Returns (db_path, use_cli). Default is web UI."""
    if len(argv) < 2:
        return None, False
    db_path = argv[1]
    use_cli = False
    if len(argv) >= 3 and argv[2].strip().lower() == "--cli":
        use_cli = True
    return db_path, use_cli


def main() -> None:
    db_path, use_cli = parse_args(sys.argv)
    if not db_path:
        print("Usage:\n  python my_library_db.py <database.json> [--cli]")
        ...
        sys.exit(1)

    parent = os.path.dirname(os.path.abspath(db_path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    if use_cli:
        cli_main(db_path)
    else:
        try:
            ensure_setup()
        except Exception as e:
            print(f"[setup] Warning: bootstrap failed ({e}). Continuing; CLI may still work.")
        web_main(db_path)
