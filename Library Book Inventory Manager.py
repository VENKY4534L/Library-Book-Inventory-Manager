#!/usr/bin/env python3

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set

DATA_FILE = "library_data.json"

@dataclass
class Book:
    isbn: str
    title: str
    author: str
    total_copies: int = 1
    issued_copies: int = 0
    added_on: str = None

    def __post_init__(self):
        if self.added_on is None:
            self.added_on = datetime.utcnow().isoformat()

    def available_copies(self) -> int:
        return self.total_copies - self.issued_copies

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Book":
        return Book(
            isbn=d["isbn"],
            title=d["title"],
            author=d["author"],
            total_copies=int(d.get("total_copies", 1)),
            issued_copies=int(d.get("issued_copies", 0)),
            added_on=d.get("added_on"),
        )

class Library:
    def __init__(self, data_path: str = DATA_FILE):
        self.data_path = data_path
        self.books: Dict[str, Book] = {}
        self.title_index: Dict[str, Set[str]] = {}
        self.author_index: Dict[str, Set[str]] = {}
        self.load()

    def _index_book(self, book: Book):
        tkey = book.title.lower()
        akey = book.author.lower()
        self.title_index.setdefault(tkey, set()).add(book.isbn)
        self.author_index.setdefault(akey, set()).add(book.isbn)

    def _deindex_book(self, book: Book):
        tkey = book.title.lower()
        akey = book.author.lower()
        if tkey in self.title_index:
            self.title_index[tkey].discard(book.isbn)
            if not self.title_index[tkey]:
                del self.title_index[tkey]
        if akey in self.author_index:
            self.author_index[akey].discard(book.isbn)
            if not self.author_index[akey]:
                del self.author_index[akey]

    def add_book(self, book: Book, overwrite: bool = False) -> Book:
        if book.isbn in self.books and not overwrite:
            existing = self.books[book.isbn]
            existing.total_copies += book.total_copies
            return existing
        if book.isbn in self.books:
            self._deindex_book(self.books[book.isbn])
        self.books[book.isbn] = book
        self._index_book(book)
        return book

    def remove_book(self, isbn: str) -> bool:
        if isbn not in self.books:
            return False
        book = self.books.pop(isbn)
        self._deindex_book(book)
        return True

    def search_by_title(self, query: str) -> List[Book]:
        q = query.lower()
        results = []
        for tkey, isbns in self.title_index.items():
            if q in tkey:
                for isbn in isbns:
                    results.append(self.books[isbn])
        unique = {b.isbn: b for b in results}
        return sorted(unique.values(), key=lambda b: b.title.lower())

    def search_by_author(self, query: str) -> List[Book]:
        q = query.lower()
        results = []
        for akey, isbns in self.author_index.items():
            if q in akey:
                for isbn in isbns:
                    results.append(self.books[isbn])
        unique = {b.isbn: b for b in results}
        return sorted(unique.values(), key=lambda b: b.author.lower())

    def get_book(self, isbn: str) -> Optional[Book]:
        return self.books.get(isbn)

    def issue_book(self, isbn: str) -> bool:
        book = self.get_book(isbn)
        if not book or book.available_copies() <= 0:
            return False
        book.issued_copies += 1
        return True

    def return_book(self, isbn: str) -> bool:
        book = self.get_book(isbn)
        if not book or book.issued_copies <= 0:
            return False
        book.issued_copies -= 1
        return True

    def total_books_count(self) -> int:
        return sum(b.total_copies for b in self.books.values())

    def total_unique_titles(self) -> int:
        return len(self.books)

    def total_issued_count(self) -> int:
        return sum(b.issued_copies for b in self.books.values())

    def save(self):
        data = {
            "books": {isbn: b.to_dict() for isbn, b in self.books.items()},
            "title_index": {k: list(v) for k, v in self.title_index.items()},
            "author_index": {k: list(v) for k, v in self.author_index.items()},
        }
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(self.data_path):
            return
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.books = {isbn: Book.from_dict(d) for isbn, d in data.get("books", {}).items()}
        self.title_index = {k: set(v) for k, v in data.get("title_index", {}).items()}
        self.author_index = {k: set(v) for k, v in data.get("author_index", {}).items()}

def print_book(book: Book):
    print(f"ISBN: {book.isbn}")
    print(f"Title: {book.title}")
    print(f"Author: {book.author}")
    print(f"Total copies: {book.total_copies}")
    print(f"Issued copies: {book.issued_copies}")
    print(f"Available copies: {book.available_copies()}")
    print(f"Added on: {book.added_on}")

def add_book_cli(library: Library):
    isbn = input("Enter ISBN: ").strip()
    title = input("Enter Title: ").strip()
    author = input("Enter Author: ").strip()
    try:
        total = int(input("Enter number of copies: ").strip() or "1")
    except ValueError:
        total = 1
    b = Book(isbn=isbn, title=title, author=author, total_copies=total)
    library.add_book(b)
    library.save()
    print("Book added.")

def search_title_cli(library: Library):
    q = input("Search title: ").strip()
    results = library.search_by_title(q)
    if not results:
        print("No books found.")
        return
    for i, b in enumerate(results, 1):
        print(f"\n[{i}]")
        print_book(b)

def search_author_cli(library: Library):
    q = input("Search author: ").strip()
    results = library.search_by_author(q)
    if not results:
        print("No books found.")
        return
    for i, b in enumerate(results, 1):
        print(f"\n[{i}]")
        print_book(b)

def issue_cli(library: Library):
    isbn = input("Enter ISBN to issue: ").strip()
    if library.issue_book(isbn):
        library.save()
        print("Book issued.")
    else:
        print("Issue failed.")

def return_cli(library: Library):
    isbn = input("Enter ISBN to return: ").strip()
    if library.return_book(isbn):
        library.save()
        print("Book returned.")
    else:
        print("Return failed.")

def remove_cli(library: Library):
    isbn = input("Enter ISBN to remove: ").strip()
    if library.remove_book(isbn):
        library.save()
        print("Book removed.")
    else:
        print("Remove failed.")

def report_cli(library: Library):
    print("=== Library Report ===")
    print("Total unique titles:", library.total_unique_titles())
    print("Total copies:", library.total_books_count())
    print("Total issued:", library.total_issued_count())
    print("\nAll books:")
    for isbn, b in library.books.items():
        print(f"{b.title} | {b.author} | ISBN:{isbn} | Total:{b.total_copies} | Issued:{b.issued_copies}")

def seed_demo(library: Library):
    if library.total_unique_titles() == 0:
        demo = [
            Book("9780140449136", "The Odyssey", "Homer", 3),
            Book("9780261103573", "The Lord of the Rings", "J. R. R. Tolkien", 5),
            Book("9780131103627", "The C Programming Language", "Brian W. Kernighan", 2),
        ]
        for b in demo:
            library.add_book(b)
        library.save()
        print("Demo books added.")

def main():
    lib = Library()
    seed_demo(lib)
    menu = """
Library Manager
1) Add book
2) Search by title
3) Search by author
4) Issue book
5) Return book
6) Remove book
7) Report
8) Save
9) Exit
"""
    while True:
        print(menu)
        choice = input("Choose (1-9): ").strip()
        if choice == "1":
            add_book_cli(lib)
        elif choice == "2":
            search_title_cli(lib)
        elif choice == "3":
            search_author_cli(lib)
        elif choice == "4":
            issue_cli(lib)
        elif choice == "5":
            return_cli(lib)
        elif choice == "6":
            remove_cli(lib)
        elif choice == "7":
            report_cli(lib)
        elif choice == "8":
            lib.save()
            print("Saved.")
        elif choice == "9":
            lib.save()
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()