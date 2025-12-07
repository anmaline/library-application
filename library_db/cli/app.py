"""
CLI main loop (add/print/quit).
"""
from ..storage import LibraryDB
from .menu import get_keypress
from .prompts import prompt_for_book


def cli_main(db_path: str) -> None:
    """
    Select option from the menu:
    1) Add book
    2) Print all books
    Q) Quit
    """
    db = LibraryDB(db_path)
    db.load()

    while True:
        print("\n--- Library DB (CLI) ---")
        print("1) Add a book")
        print("2) Show all books")
        print("Q) Quit")
        print("\nPress a key: ", end="", flush=True)

        choice = get_keypress()
        print(choice)

        if choice == "1":
            print("\nAdd a new book:")
            success, book = prompt_for_book()
            if not success:
                print("  (cancelled)")
                continue
            ok, err = db.add(book)
            if ok:
                print("  Book added successfully!")
            else:
                print(f"  Error: {err}")

        elif choice == "2":
            print("\nAll books:")
            if not db.books:
                print("  (no books)")
            else:
                for i, b in enumerate(db.books, start=1):
                    print(f"  {i}. {b.title} by {b.author} (ISBN: {b.isbn}, Year: {b.year})")

        elif choice in ("q", "\x1b"):
            print("Goodbye!")
            break

        else:
            print(f"  (unknown choice: '{choice}')")
