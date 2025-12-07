"""
All input prompts and validation for the CLI.
"""
from typing import Tuple
from datetime import date

from ..models import Book


def prompt_for_book() -> Tuple[bool, Book]:
    """
    Prompt user for book details with robust validation and confirmation.
    Returns (success: bool, book: Book).
    If user cancels (empty title), success is False.
    """
    title = input("  Title (or empty to cancel): ").strip()
    if not title:
        return False, None
    
    author = input("  Author: ").strip()
    
    # ISBN validation loop
    while True:
        isbn = input("  ISBN: ").strip()
        isbn_digits = "".join(ch for ch in isbn if ch.isdigit())
        if len(isbn_digits) in (10, 13):
            break
        print("    Invalid. ISBN must have 10 or 13 digits (hyphens/spaces allowed). Try again.")
    
    # Year validation loop
    current_year = date.today().year
    while True:
        year_str = input(f"  Year (0-{current_year}): ").strip()
        try:
            year = int(year_str)
            if 0 <= year <= current_year:
                break
            print(f"    Invalid. Year must be between 0 and {current_year}. Try again.")
        except ValueError:
            print("    Invalid. Please enter a number. Try again.")
    
    book = Book(title=title, author=author, isbn=isbn, year=year)
    
    # Confirmation prompt
    print("\n  Book details:")
    print(f"    Title:  {book.title}")
    print(f"    Author: {book.author}")
    print(f"    ISBN:   {book.isbn}")
    print(f"    Year:   {book.year}")
    
    confirm = input("\n  Add this book? (y/n): ").strip().lower()
    if confirm != 'y':
        return False, None
    
    return True, book
