"""
Book dataclass with validation and ID generation.
"""
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, Tuple
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
        current = date.today().year
        if self.year < 0 or self.year > current:
            return False, f"Year should be between 0 and {current}."
        return True, None


def book_id(b: Book) -> str:
    """Stable ID from title+author+isbn."""
    combined = f"{b.title}|{b.author}|{b.isbn}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
