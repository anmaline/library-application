# Library DB

A local Python application to manage a simple **book database in JSON**.

## What it does
- Stores books in `library.json` with fields: **title, author, isbn, year**.
- Keeps the file **sorted by publishing year (ascending)** after every change.
- **Web UI (default)**: table view + **Add (with confirmation)**, **Edit**, **Delete**.
- **CLI**: menu with **1) Add**, **2) Print**, **Q) Exit**.
- **Validation**:
  - ISBN must have **10 or 13 digits** (hyphens/spaces allowed).
  - Year must be **0..current year**.
  - CLI prompts validate **immediately** and let you **cancel** (`Q/quit/exit/cancel`) at any field.
- **Seeding**: if `library.json` is **missing or empty**, a demo dataset is created on first run.
- **First run (Web UI only)**: creates a local `.venv` and installs **Flask** automatically.

## Requirements
- Python **3.10+**

## Run CLI
```bash
python my_library_db.py library.json --cli
```

## Run Web UI
```bash
python my_library_db.py library.json
# Opens automatically in http://127.0.0.1:5000
