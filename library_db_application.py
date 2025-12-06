#!/usr/bin/env python3
"""
my_library_db.py

Local Python app with:
- JSON storage.
- Web UI: table, Add (confirm), Edit, Delete.
- CLI (optional --cli): 1) Add  2) Print  Q) Exit.
- First-run bootstrap: creates .venv and installs Flask, then relaunches.
- Auto-seeding: if the database file is missing or empty, a demo dataset is written.

Usage:
  python my_library_db.py <database.json> [--cli]

Examples:
  python my_library_db.py library.json
  python my_library_db.py library.json --cli
"""

import json
import os
import sys
import subprocess
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

# -----------------------------
# Bootstrap: virtualenv + deps
# -----------------------------

def _is_windows() -> bool:
    return os.name == "nt"

def _venv_paths(base: str = ".venv") -> Tuple[str, str, str]:
    if _is_windows():
        py = os.path.join(base, "Scripts", "python.exe")
        pip = os.path.join(base, "Scripts", "pip.exe")
    else:
        py = os.path.join(base, "bin", "python")
        pip = os.path.join(base, "bin", "pip")
    return base, py, pip

def ensure_setup() -> None:
    """
    Ensure a virtual environment exists and Flask is installed.
    If not running inside a venv, create .venv, install Flask, and re-exec inside the venv.
    If inside a venv, make sure Flask is installed.
    """
    venv_dir, venv_python, _ = _venv_paths()
    in_venv = sys.prefix != sys.base_prefix

    def _has_package(pkg: str) -> bool:
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    if in_venv:
        if not _has_package("flask"):
            print("[setup] Installing Flask in current virtualenv ...")
            subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)
        return

    if not os.path.isdir(venv_dir):
        print("[setup] Creating virtual environment at .venv ...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    print("[setup] Ensuring Flask is installed in .venv ...")
    subprocess.run([venv_python, "-m", "pip", "install", "flask"], check=True)

    print("[setup] Re-launching inside the virtual environment ...\n")
    os.execv(venv_python, [venv_python] + sys.argv)

# -----------------------------
# Demo dataset (seed)
# -----------------------------

DEFAULT_SEED = [
    {"title": "Pride and Prejudice",          "author": "Jane Austen",            "isbn": "9780141439518", "year": 1813},
    {"title": "Moby Dick",                    "author": "Herman Melville",        "isbn": "9781503280786", "year": 1851},
    {"title": "Crime and Punishment",         "author": "Fyodor Dostoyevsky",     "isbn": "9780140449136", "year": 1866},
    {"title": "War and Peace",                "author": "Leo Tolstoy",            "isbn": "9780199232765", "year": 1869},
    {"title": "The Idiot",                    "author": "Fyodor Dostoyevsky",     "isbn": "9780140444032", "year": 1869},
    {"title": "The Great Gatsby",             "author": "F. Scott Fitzgerald",    "isbn": "9780743273565", "year": 1925},
    {"title": "Nineteen Eighty-Four",         "author": "George Orwell",          "isbn": "9780451524935", "year": 1949},
    {"title": "To Kill a Mockingbird",        "author": "Harper Lee",             "isbn": "9780061120084", "year": 1960},
    {"title": "One Hundred Years of Solitude","author": "Gabriel García Márquez", "isbn": "9780060883287", "year": 1967},
    {"title": "The Name of the Rose",         "author": "Umberto Eco",            "isbn": "9780156001311", "year": 1980},
    {"title": "The Kite Runner",              "author": "Khaled Hosseini",        "isbn": "9781594631931", "year": 2003}
]

# -----------------------------
# Data model & storage (JSON)
# -----------------------------

from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from datetime import date

@dataclass
class Book:
    title: str
    author: str
    isbn: str
    year: int

    def validate(self) -> Tuple[bool, Optional[str]]:
        if not self.title.strip():
            return False, "Title must not be empty."
        if not self.author.strip():
            return False, "Author must not be empty."
        isbn_digits = "".join(ch for ch in self.isbn if ch.isdigit())
        if len(isbn_digits) not in (10, 13):
            return False, "ISBN should have 10 or 13 digits (hyphens/spaces allowed)."
        if not isinstance(self.year, int):
            return False, "Year must be an integer."
        max_year = date.today().year
        if self.year < 0 or self.year > max_year:
            return False, f"Year must be between 0 and {max_year}."

        return True, None


import hashlib

def book_id(b: Book) -> str:
    h = hashlib.sha1(f"{b.title}\x1f{b.author}\x1f{b.isbn}\x1f{b.year}".encode("utf-8")).hexdigest()
    return h[:12]

class LibraryDB:
    def __init__(self, path: str):
        self.path = path
        self.books: List[Book] = []

    def _apply_seed(self) -> None:
        self.books = [Book(**i) for i in DEFAULT_SEED]
        self.save()
        print("[info] Demo dataset seeded.")

    def load(self) -> None:
        if not os.path.exists(self.path):
            print(f"[info] File {self.path} not found. Seeding a new database.")
            parent = os.path.dirname(os.path.abspath(self.path))
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            self._apply_seed()
            return

        with open(self.path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise SystemExit(f"[error] File is not valid JSON: {e}")

        if not isinstance(data, list):
            raise SystemExit("[error] JSON root must be a list (array).")

        if len(data) == 0:
            print("[info] Empty database detected. Seeding demo dataset.")
            self._apply_seed()
            return

        self.books = [
            Book(
                title=str(item.get("title", "")).strip(),
                author=str(item.get("author", "")).strip(),
                isbn=str(item.get("isbn", "")).strip(),
                year=int(item.get("year", 0)),
            )
            for item in (data or [])
        ]
        self._sort()

    def save(self) -> None:
        self._sort()
        data = [asdict(b) for b in self.books]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_book(self, book: Book) -> Tuple[bool, Optional[str]]:
        ok, err = book.validate()
        if not ok:
            return False, err
        self.books.append(book)
        self.save()
        return True, None

    def update_by_id(self, bid: str, new_book: Book) -> Tuple[bool, Optional[str]]:
        idx = self._find_index_by_id(bid)
        if idx is None:
            return False, "Book not found."
        ok, err = new_book.validate()
        if not ok:
            return False, err
        self.books[idx] = new_book
        self.save()
        return True, None

    def delete_by_id(self, bid: str) -> Tuple[bool, Optional[str]]:
        idx = self._find_index_by_id(bid)
        if idx is None:
            return False, "Book not found."
        self.books.pop(idx)
        self.save()
        return True, None

    def get_all_sorted(self) -> List[Book]:
        self._sort()
        return list(self.books)

    def _sort(self) -> None:
        self.books.sort(key=lambda b: (b.year, b.title.lower(), b.author.lower()))

    def _find_index_by_id(self, bid: str) -> Optional[int]:
        for i, b in enumerate(self.books):
            if book_id(b) == bid:
                return i
        return None

# -----------------------------
# CLI UI
# -----------------------------

CANCEL_WORDS = {"q", "quit", "exit", "cancel"}

def _is_cancel(s: str) -> bool:
    return (s or "").strip().lower() in CANCEL_WORDS

def prompt_non_empty(label: str) -> Optional[str]:
    """
    Prompt for a non-empty string. Allows cancel via Q/quit/exit/cancel.
    Returns the string, or None if cancelled.
    """
    while True:
        s = input(f"{label}: ").strip()
        if _is_cancel(s):
            return None
        if s:
            return s
        print(f"[error] {label} must not be empty. Enter again or type Q to cancel.")

def prompt_isbn() -> Optional[str]:
    """
    Prompt for ISBN. Accepts hyphens/spaces but requires 10 or 13 digits total.
    Allows cancel via Q/quit/exit/cancel.
    Returns the original input (not stripped to digits) or None if cancelled.
    """
    while True:
        s = input("ISBN (10 or 13 digits; hyphens allowed): ").strip()
        if _is_cancel(s):
            return None
        digits = "".join(ch for ch in s if ch.isdigit())
        if len(digits) in (10, 13):
            return s
        print("[error] ISBN should have 10 or 13 digits (hyphens/spaces allowed). Enter again or type Q to cancel.")


def prompt_year() -> Optional[int]:
    """
    Prompt for publishing year (0..current_year). Allows cancel via Q/quit/exit/cancel.
    Returns int or None if cancelled.
    """
    max_year = date.today().year  # current year
    while True:
        s = input(f"Publishing year (0–{max_year}): ").strip()
        if _is_cancel(s):
            return None
        try:
            y = int(s)
        except ValueError:
            print("[error] Year must be an integer. Enter again or type Q to cancel.")
            continue
        if 0 <= y <= max_year:
            return y
        print(f"[error] Year must be between 0 and {max_year}. Enter again or type Q to cancel.")


def prompt_book() -> Optional[Book]:
    print("\nEnter new book details (type Q to cancel at any prompt)")
    print("--------------------------------------------------------")

    title = prompt_non_empty("Title")
    if title is None:
        print("[info] Cancelled.\n")
        return None

    author = prompt_non_empty("Author")
    if author is None:
        print("[info] Cancelled.\n")
        return None

    isbn = prompt_isbn()
    if isbn is None:
        print("[info] Cancelled.\n")
        return None

    year = prompt_year()
    if year is None:
        print("[info] Cancelled.\n")
        return None

    # Final guard using the dataclass-level validation
    book = Book(title=title, author=author, isbn=isbn, year=year)
    ok, err = book.validate()
    if not ok:
        # This should almost never trigger now, but it's a safe last line of defense
        print(f"[error] {err}\n")
        return None

    print("\nYou entered:")
    print(f"  Title : {book.title}")
    print(f"  Author: {book.author}")
    print(f"  ISBN  : {book.isbn}")
    print(f"  Year  : {book.year}")

    confirm = input("\nSave this book to the database? (y/N, or Q to cancel): ").strip().lower()
    if confirm == "y":
        return book
    print("[info] Not saved.\n")
    return None


def print_db(db: LibraryDB) -> None:
    books = db.get_all_sorted()
    if not books:
        print("\n[info] Database is empty.\n")
        return
    print("\nCurrent database (ascending by publishing year)")
    print("------------------------------------------------")
    for idx, b in enumerate(books, start=1):
        print(f"{idx:02d}. {b.year} | {b.title} — {b.author} | ISBN: {b.isbn}")
    print("")


import os

def get_menu_choice_robust(prompt: str = "\nSelect an option: ") -> str | None:
    """
    Robust menu choice for Windows CMD:
    - On Windows, read a single keypress with msvcrt (no Enter needed).
    - Accept ONLY '1', '2', or 'q'/'Q'.
    - On non-Windows, fall back to input() and accept 1, 2, or q/Q.
    Returns: '1', '2', or 'q' (lowercase) if valid; else None.
    """
    if os.name == "nt":
        # Windows: use msvcrt to avoid cmd interpreting input
        try:
            import msvcrt
            print(prompt, end="", flush=True)
            while True:
                ch = msvcrt.getwch()  # wide char; works with local keyboard layout
                if ch in ("1", "2", "q", "Q"):
                    # Echo the key so the user sees it next to the prompt
                    print(ch)
                    return ch.lower()
                # Ignore other keys (arrow keys, etc. often come as multi-byte sequences)
        except Exception:
            # If msvcrt fails, fall back to input() below
            pass

    # Non-Windows or msvcrt unavailable: use input()
    raw = input(prompt).strip()
    raw = raw.strip("'\"")  # tolerate accidental quotes
    if raw in ("1", "2"):
        return raw
    if raw.lower() == "q":
        return "q"
    return None


def cli_main(db_path: str) -> None:
    db = LibraryDB(db_path)
    db.load()

    while True:
        print("Library Database")
        print("----------------")
        print("1) Add new book")
        print("2) Print current database (ascending by year)")
        print("Q) Exit")

        choice = get_menu_choice_robust()

        if choice == "1":
            new_book = prompt_book()
            if new_book:
                ok, err = db.add_book(new_book)
                if ok:
                    print("[ok] Book added and database updated.\n")
                else:
                    print(f"[error] {err}\n")

        elif choice == "2":
            print_db(db)

        elif choice == "q":
            print("\nGoodbye!")
            break

        else:
            print("[info] Invalid option. Please type 1, 2, or Q.\n")


# -----------------------------
# Web UI (Flask) with Add/Edit/Delete
# -----------------------------

import threading
import time
import webbrowser
from datetime import date
max_year = date.today().year

def web_main(db_path: str, auto_open: bool = True) -> None:
    from flask import Flask, request, redirect, url_for, Response

    app = Flask(__name__)
    db = LibraryDB(db_path)
    db.load()

    def html_page(body: str, title: str = "Library DB") -> str:
        return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>{title}</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<style>
:root {{
  --primary:#0d6efd; --muted:#6c757d; --border:#d0d7de; --bg:#f6f8fa; --text:#222;
}}
* {{ box-sizing: border-box; }}
html,body {{ margin:0; padding:0; color:var(--text); background:var(--bg); }}
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }}
.container {{ max-width: 980px; margin: 2rem auto; padding: 0 1rem; }}
.header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }}
a.button, button {{ padding: .5rem 1rem; border:1px solid var(--primary); background:var(--primary); color:#fff; border-radius:6px; text-decoration:none; cursor:pointer; }}
a.button.muted, button.muted {{ border-color:var(--muted); background:var(--muted); }}
table {{ width:100%; border-collapse: collapse; background:#fff; border:1px solid var(--border); }}
th, td {{ border-top:1px solid var(--border); padding:.6rem .5rem; text-align:left; }}
th {{ background:#f0f3f6; }}
.actions a {{ margin-right:.5rem; }}
form.grid {{ display:grid; grid-template-columns: 1fr 3fr; gap:.6rem 1rem; background:#fff; border:1px solid var(--border); padding:1rem; border-radius:6px; }}
input[type=text], input[type=number] {{ width:100%; padding:.45rem; border:1px solid var(--border); border-radius:4px; }}
.notice {{ padding:.75rem 1rem; background:#fff3cd; border:1px solid #ffec99; border-radius:6px; margin-bottom:1rem; }}
</style>
</head>
<body>
  <div class=\"container\">{body}</div>
</body>
</html>"""

    def row_actions(b: Book) -> str:
        bid = book_id(b)
        return f"""
          <span class=\"actions\">
            <a class=\"button\" href=\"{url_for('edit_form', bid=bid)}\">Edit</a>
            <a class=\"button muted\" href=\"{url_for('delete_confirm', bid=bid)}\">Delete</a>
          </span>
        """

    @app.get("/")
    def index() -> Response:
        rows = "\n".join(
            f"<tr><td>{b.year}</td><td>{b.title}</td><td>{b.author}</td><td>{b.isbn}</td><td>{row_actions(b)}</td></tr>"
            for b in db.get_all_sorted()
        )
        body = f"""
        <div class=\"header\">
          <h1>Library Database</h1>
          <div><a class=\"button\" href=\"{url_for('add_form')}\">Add new book</a></div>
        </div>
        <table>
          <thead><tr><th>Year</th><th>Title</th><th>Author</th><th>ISBN</th><th>Actions</th></tr></thead>
          <tbody>
            {rows if rows else '<tr><td colspan=\"5\">No books yet.</td></tr>'}
          </tbody>
        </table>
        """
        return html_page(body)

    # Add
    @app.get("/add")
    def add_form() -> Response:
        body = f"""
        <h2>Add new book</h2>
        <form class=\"grid\" method=\"post\" action=\"{url_for('add_preview')}\">
          <label>Title</label>  <input type=\"text\" name=\"title\" required>
          <label>Author</label> <input type=\"text\" name=\"author\" required>
          <label>ISBN</label>   <input type=\"text\" name=\"isbn\" required>
          <label>Year</label>   <input type="number" name="year" min="0" max="{max_year}" required>
          <div></div><div><button type=\"submit\">Continue</button> <a class=\"button muted\" href=\"{url_for('index')}\">Cancel</a></div>
        </form>
        """
        return html_page(body, title="Add | Library DB")

    @app.post("/add/preview")
    def add_preview() -> Response:
        from flask import request
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        year_s = (request.form.get("year") or "").strip()
        try:
            year = int(year_s)
        except ValueError:
            year = -1
        book = Book(title=title, author=author, isbn=isbn, year=year)
        ok, err = book.validate()
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + add_form().get_data(as_text=True))

        body = f"""
        <h2>Confirm new book</h2>
        <table>
          <tbody>
            <tr><th>Title</th><td>{book.title}</td></tr>
            <tr><th>Author</th><td>{book.author}</td></tr>
            <tr><th>ISBN</th><td>{book.isbn}</td></tr>
            <tr><th>Year</th><td>{book.year}</td></tr>
          </tbody>
        </table>
        <form method=\"post\" action=\"{url_for('add_submit')}\">
          <input type=\"hidden\" name=\"title\" value=\"{book.title}\">\n          <input type=\"hidden\" name=\"author\" value=\"{book.author}\">\n          <input type=\"hidden\" name=\"isbn\" value=\"{book.isbn}\">\n          <input type=\"hidden\" name=\"year\" value=\"{book.year}\">\n          <p style=\"margin-top:1rem;\">\n            <button type=\"submit\">Save</button>\n            <a class=\"button muted\" href=\"{url_for('add_form')}\">Cancel</a>\n          </p>\n        </form>
        """
        return html_page(body, title="Confirm | Library DB")

    @app.post("/add/save")
    def add_submit() -> Response:
        from flask import request, redirect, url_for
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        year_s = (request.form.get("year") or "").strip()
        try:
            year = int(year_s)
        except ValueError:
            year = -1
        book = Book(title=title, author=author, isbn=isbn, year=year)
        ok, err = book.validate()
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + add_form().get_data(as_text=True))
        ok, err = db.add_book(book)
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + add_form().get_data(as_text=True))
        return redirect(url_for("index"))

    # Edit
    @app.get("/edit/<bid>")
    def edit_form(bid: str) -> Response:
        idx = db._find_index_by_id(bid)
        if idx is None:
            return html_page("<div class='notice'>Error: Book not found.</div>" + index().get_data(as_text=True))
        b = db.books[idx]
        body = f"""
        <h2>Edit book</h2>
        <form class=\"grid\" method=\"post\" action=\"{url_for('edit_save', bid=bid)}\">
          <label>Title</label>  <input type=\"text\" name=\"title\" value=\"{b.title}\" required>
          <label>Author</label> <input type=\"text\" name=\"author\" value=\"{b.author}\" required>
          <label>ISBN</label>   <input type=\"text\" name=\"isbn\" value=\"{b.isbn}\" required>
          <label>Year</label>   <input type="number" name="year" min="0" max="{max_year}" value="{b.year}" required>
          <div></div><div><button type=\"submit\">Save</button> <a class=\"button muted\" href=\"{url_for('index')}\">Cancel</a></div>
        </form>
        """
        return html_page(body, title="Edit | Library DB")

    @app.post("/edit/<bid>/save")
    def edit_save(bid: str) -> Response:
        from flask import request, redirect, url_for
        idx = db._find_index_by_id(bid)
        if idx is None:
            return html_page("<div class='notice'>Error: Book not found.</div>" + index().get_data(as_text=True))
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        year_s = (request.form.get("year") or "").strip()
        try:
            year = int(year_s)
        except ValueError:
            year = -1
        new_book = Book(title=title, author=author, isbn=isbn, year=year)
        ok, err = db.update_by_id(bid, new_book)
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + edit_form(bid).get_data(as_text=True))
        return redirect(url_for("index"))

    # Delete
    @app.get("/delete/<bid>")
    def delete_confirm(bid: str) -> Response:
        from flask import url_for
        idx = db._find_index_by_id(bid)
        if idx is None:
            return html_page("<div class='notice'>Error: Book not found.</div>" + index().get_data(as_text=True))
        b = db.books[idx]
        body = f"""
        <h2>Delete book</h2>
        <div class=\"notice\">Are you sure you want to delete this book?</div>
        <table>
          <tbody>
            <tr><th>Title</th><td>{b.title}</td></tr>
            <tr><th>Author</th><td>{b.author}</td></tr>
            <tr><th>ISBN</th><td>{b.isbn}</td></tr>
            <tr><th>Year</th><td>{b.year}</td></tr>
          </tbody>
        </table>
        <form method=\"post\" action=\"{url_for('delete_do', bid=bid)}\">
          <p style=\"margin-top:1rem;\">\n            <button class=\"button muted\" type=\"submit\">Delete</button>\n            <a class=\"button\" href=\"{url_for('index')}\">Cancel</a>\n          </p>\n        </form>
        """
        return html_page(body, title="Delete | Library DB")

    @app.post("/delete/<bid>/confirm")
    def delete_do(bid: str) -> Response:
        from flask import redirect, url_for
        ok, err = db.delete_by_id(bid)
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + index().get_data(as_text=True))
        return redirect(url_for("index"))

    host = "127.0.0.1"
    port = 5000

    # --- NEW: open the default browser after a short delay ---
    if auto_open and not os.environ.get("LIBRARY_NO_BROWSER"):
        def _open_browser():
            # small delay so the server can bind the port before opening the page
            time.sleep(1)
            try:
                webbrowser.open(f"http://{host}:{port}")
            except Exception:
                # Non-fatal: if the OS refuses to open a browser, just continue.
                pass

        threading.Thread(target=_open_browser, daemon=True).start()

    # Start Flask
    app.run(host=host, port=port, debug=False)

# -----------------------------
# Entry point
# -----------------------------

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
        # Skip Flask/venv bootstrap entirely in CLI mode
        cli_main(db_path)
    else:
        # Only bootstrap when starting the web UI
        try:
            ensure_setup()
        except Exception as e:
            print(f"[setup] Warning: bootstrap failed ({e}). Continuing; CLI may still work.")
        web_main(db_path)


if __name__ == "__main__":
    main()
