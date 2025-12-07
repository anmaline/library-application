"""
Flask web application factory and routes.
Provides Add, Edit, and Delete functionality with confirmation.
"""
import os
import time
import webbrowser
import threading
from html import escape
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Response

from ..storage import LibraryDB
from ..models import Book, book_id


def web_main(db_path: str, auto_open: bool = True) -> None:
    """
    Start the Flask web UI.
    Loads the database and serves a simple HTML table with Add/Edit/Delete.
    """
    try:
        from flask import Flask, request, redirect, url_for
    except ImportError:
        print("Flask is not installed. Please install it first:")
        print("  pip install flask")
        import sys
        sys.exit(1)

    db = LibraryDB(db_path)
    db.load()

    app = Flask(__name__)

    def html_page(body: str, title: str = "Library DB") -> "Response":
        from flask import Response
        max_year = date.today().year
        html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>{title}</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 2rem 1rem;
    }}
    .container {{
      max-width: 1000px;
      margin: 0 auto;
      background: white;
      border-radius: 1rem;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      overflow: hidden;
    }}
    header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
      text-align: center;
    }}
    header h1 {{
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }}
    header p {{
      opacity: 0.9;
      font-size: 0.95rem;
    }}
    main {{
      padding: 2rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    thead {{
      background: #f8f9fa;
    }}
    th {{
      text-align: left;
      padding: 0.75rem 1rem;
      font-weight: 600;
      color: #495057;
      border-bottom: 2px solid #dee2e6;
    }}
    td {{
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #dee2e6;
    }}
    tbody tr:hover {{
      background: #f8f9fa;
    }}
    .actions {{
      white-space: nowrap;
    }}
    .actions a {{
      margin-right: 0.5rem;
      text-decoration: none;
      color: #667eea;
      font-weight: 500;
      transition: color 0.2s;
    }}
    .actions a:hover {{
      color: #764ba2;
      text-decoration: underline;
    }}
    .actions a.delete {{
      color: #dc3545;
    }}
    .actions a.delete:hover {{
      color: #c82333;
    }}
    .button, button {{
      display: inline-block;
      padding: 0.5rem 1rem;
      background: #667eea;
      color: white;
      text-decoration: none;
      border-radius: 0.375rem;
      font-weight: 500;
      border: none;
      cursor: pointer;
      transition: background 0.2s;
      font-size: 0.95rem;
    }}
    .button:hover, button:hover {{
      background: #764ba2;
    }}
    .button.muted {{
      background: #6c757d;
    }}
    .button.muted:hover {{
      background: #5a6268;
    }}
    form {{
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 1rem;
      max-width: 600px;
      margin-top: 1rem;
    }}
    label {{
      font-weight: 600;
      padding-top: 0.5rem;
      color: #495057;
    }}
    input[type=\"text\"],
    input[type=\"number\"] {{
      padding: 0.5rem;
      border: 1px solid #ced4da;
      border-radius: 0.375rem;
      font-size: 0.95rem;
    }}
    input:focus {{
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }}
    .notice {{
      background: #fff3cd;
      border: 1px solid #ffc107;
      color: #856404;
      padding: 1rem;
      border-radius: 0.375rem;
      margin-bottom: 1rem;
    }}
    h2 {{
      margin-bottom: 1rem;
      color: #212529;
    }}
  </style>
</head>
<body>
  <div class=\"container\">
    <header>
      <h1>📚 Library Database</h1>
      <p>Manage your book collection</p>
    </header>
    <main>
      {body}
    </main>
  </div>
</body>
</html>
        """
        return Response(html, mimetype="text/html")

    @app.get("/")
    def index() -> "Response":
        from flask import url_for
        rows = ""
        for b in db.books:
            bid = book_id(b)
            rows += f"""
        <tr>
          <td>{b.title}</td>
          <td>{b.author}</td>
          <td>{b.isbn}</td>
          <td>{b.year}</td>
          <td class=\"actions\">
            <a href=\"{url_for('edit_form', bid=bid)}\">Edit</a>
            <a href=\"{url_for('delete_confirm', bid=bid)}\" class=\"delete\">Delete</a>
          </td>
        </tr>
            """
        if not rows:
            rows = "<tr><td colspan='5' style='text-align:center; padding:2rem; color:#6c757d;'>No books yet. Add one below!</td></tr>"

        body = f"""
      <div style=\"margin-bottom: 1rem;\">
        <a class=\"button\" href=\"{url_for('add_form')}\">+ Add New Book</a>
      </div>
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Author</th>
            <th>ISBN</th>
            <th>Year</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
        """
        return html_page(body)

    @app.get("/add")
    def add_form() -> "Response":
        from flask import url_for
        max_year = date.today().year
        body = f"""
        <h2>Add a new book</h2>
        <form method=\"post\" action=\"{url_for('add_submit')}\">
          <label>Title</label>   <input type=\"text\" name=\"title\" required>
          <label>Author</label>  <input type=\"text\" name=\"author\" required>
          <label>ISBN</label>    <input type=\"text\" name=\"isbn\" pattern=\"[0-9\\-\\s]{{10,17}}\" title=\"ISBN must have 10 or 13 digits (hyphens/spaces allowed)\" required>
          <label>Year</label>    <input type=\"number\" name=\"year\" min=\"0\" max=\"{max_year}\" required>
          <div></div><div><button type=\"submit\">Add Book</button> <a class=\"button muted\" href=\"{url_for('index')}\">Cancel</a></div>
        </form>
        """
        return html_page(body, title="Add Book | Library DB")

    @app.post("/add")
    def add_submit() -> "Response":
        from flask import request, redirect, url_for
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        year_s = (request.form.get("year") or "").strip()
        try:
            year = int(year_s)
        except ValueError:
            year = -1
        new_book = Book(title=title, author=author, isbn=isbn, year=year)
        ok, err = new_book.validate()
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + add_form().get_data(as_text=True))
        
        # Show confirmation page
        max_year = date.today().year
        body = f"""
        <h2>Confirm adding book</h2>
        <div class=\"notice\">Please review the book details before adding:</div>
        <table>
          <tbody>
            <tr><th>Title</th><td>{escape(new_book.title)}</td></tr>
            <tr><th>Author</th><td>{escape(new_book.author)}</td></tr>
            <tr><th>ISBN</th><td>{escape(new_book.isbn)}</td></tr>
            <tr><th>Year</th><td>{new_book.year}</td></tr>
          </tbody>
        </table>
        <form method=\"post\" action=\"{url_for('add_confirm')}\">
          <input type=\"hidden\" name=\"title\" value=\"{escape(new_book.title)}\">
          <input type=\"hidden\" name=\"author\" value=\"{escape(new_book.author)}\">
          <input type=\"hidden\" name=\"isbn\" value=\"{escape(new_book.isbn)}\">
          <input type=\"hidden\" name=\"year\" value=\"{new_book.year}\">
          <p style=\"margin-top:1rem;\">
            <button type=\"submit\">Confirm & Add</button>
            <a class=\"button muted\" href=\"{url_for('index')}\">Cancel</a>
          </p>
        </form>
        """
        return html_page(body, title="Confirm Add | Library DB")
    
    @app.post("/add/confirm")
    def add_confirm() -> "Response":
        from flask import request, redirect, url_for
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        year_s = (request.form.get("year") or "").strip()
        try:
            year = int(year_s)
        except ValueError:
            year = -1
        new_book = Book(title=title, author=author, isbn=isbn, year=year)
        ok, err = db.add(new_book)
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + index().get_data(as_text=True))
        return redirect(url_for("index"))

    @app.get("/edit/<bid>")
    def edit_form(bid: str) -> "Response":
        from flask import url_for
        idx = db._find_index_by_id(bid)
        if idx is None:
            return html_page("<div class='notice'>Error: Book not found.</div>" + index().get_data(as_text=True))
        b = db.books[idx]
        max_year = date.today().year
        body = f"""
        <h2>Edit book</h2>
        <form method=\"post\" action=\"{url_for('edit_save', bid=bid)}\">
          <label>Title</label>  <input type=\"text\" name=\"title\" value=\"{b.title}\" required>
          <label>Author</label> <input type=\"text\" name=\"author\" value=\"{b.author}\" required>
          <label>ISBN</label>   <input type=\"text\" name=\"isbn\" value=\"{b.isbn}\" pattern=\"[0-9\\-\\s]{{10,17}}\" title=\"ISBN must have 10 or 13 digits (hyphens/spaces allowed)\" required>
          <label>Year</label>   <input type="number" name="year" min="0" max="{max_year}" value="{b.year}" required>
          <div></div><div><button type=\"submit\">Save</button> <a class=\"button muted\" href=\"{url_for('index')}\">Cancel</a></div>
        </form>
        """
        return html_page(body, title="Edit | Library DB")

    @app.post("/edit/<bid>/save")
    def edit_save(bid: str) -> "Response":
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

    @app.get("/delete/<bid>")
    def delete_confirm(bid: str) -> "Response":
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
    def delete_do(bid: str) -> "Response":
        from flask import redirect, url_for
        ok, err = db.delete_by_id(bid)
        if not ok:
            return html_page(f"<div class='notice'>Error: {err}</div>" + index().get_data(as_text=True))
        return redirect(url_for("index"))

    host = "127.0.0.1"
    port = 5000

    if auto_open and not os.environ.get("LIBRARY_NO_BROWSER"):
        def _open_browser():
            time.sleep(1)
            try:
                webbrowser.open(f"http://{host}:{port}")
            except Exception:
                pass

        threading.Thread(target=_open_browser, daemon=True).start()

    app.run(host=host, port=port, debug=False)
