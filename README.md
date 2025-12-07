# Library DB Application

A local Python library management application with CLI and Web UI interfaces.

## Features

- **JSON storage** - Books are persisted in a JSON file
- **Web UI** - Beautiful responsive interface with Add, Edit, and Delete operations
- **CLI mode** - Simple command-line interface for terminal users
- **Auto-seeding** - Comes with demo data if database is empty
- **Virtual environment bootstrap** - Automatically creates .venv and installs Flask

## Folder Structure

```
library_db_modular/
  library_db/
    __init__.py          # Package exports
    app.py               # Entry-point helpers (parse args, main)
    bootstrap.py         # Optional venv+Flask bootstrap (relaunch into .venv)
    models.py            # Book dataclass + validation + book_id()
    seed.py              # DEFAULT_SEED demo data
    storage.py           # LibraryDB JSON persistence (load/save/add/update/delete)
    cli/
      __init__.py
      app.py             # CLI main loop (add/print/quit)
      menu.py            # Robust keypress menu for Windows/non-Windows
      prompts.py         # All input prompts & validation
    web/
      __init__.py
      app.py             # Flask app factory + helpers (Add/Edit/Delete with confirm)
  library.json           # An example data set of books (If not found, automatically created)
  README.md              # This file
  requirements.txt       # flask>=2.2,<4
  run.py                 # Convenience runner
```

## Usage

```bash
# CLI mode
python run_library.py library.json --cli

# Web UI
python run_library.py library.json
```