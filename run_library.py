#!/usr/bin/env python3
"""
Convenience runner for the Library DB application.

Usage:
  python run.py <database.json> [--cli]

Examples:
  python run.py library.json
  python run.py library.json --cli
"""

from library_db import main

if __name__ == "__main__":
    main()
