"""
LibraryDB JSON persistence layer.
Handles loading, saving, adding, updating, and deleting books.
"""
import json
import os
from dataclasses import asdict
from typing import List, Optional, Tuple

from .models import Book, book_id
from .seed import DEFAULT_SEED


class LibraryDB:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.books: List[Book] = []

    def load(self) -> None:
        if not os.path.isfile(self.json_path):
            self._seed()
            return
        with open(self.json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not raw:
            self._seed()
            return
        self.books = [Book(**item) for item in raw]

    def save(self) -> None:
        with open(self.json_path, "w", encoding="utf-8") as f:
            data = [asdict(b) for b in self.books]
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _seed(self) -> None:
        self.books = [Book(**rec) for rec in DEFAULT_SEED]
        self.save()

    def add(self, b: Book) -> Tuple[bool, Optional[str]]:
        ok, err = b.validate()
        if not ok:
            return False, err
        self.books.append(b)
        self.save()
        return True, None

    def update_by_id(self, bid: str, new_book: Book) -> Tuple[bool, Optional[str]]:
        ok, err = new_book.validate()
        if not ok:
            return False, err
        idx = self._find_index_by_id(bid)
        if idx is None:
            return False, "Book not found."
        self.books[idx] = new_book
        self.save()
        return True, None

    def delete_by_id(self, bid: str) -> Tuple[bool, Optional[str]]:
        idx = self._find_index_by_id(bid)
        if idx is None:
            return False, "Book not found."
        del self.books[idx]
        self.save()
        return True, None

    def _find_index_by_id(self, bid: str) -> Optional[int]:
        for i, b in enumerate(self.books):
            if book_id(b) == bid:
                return i
        return None
