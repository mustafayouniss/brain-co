"""
Create the first admin user.

Usage
-----
    python -m app.scripts.create_admin --email admin@example.com --full-name "Alice Smith"

The command prompts for the password twice with getpass (no terminal echo).
The password is NEVER passed as a CLI argument or read from .env.
If the email already exists, the command prints a message and exits without
making any changes.

Design note: main() accepts injectable session_factory and ask_password
parameters so tests can drive it without hitting the real database or
the real terminal.
"""
import argparse
import getpass
import sys
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.services.user_service import EmailAlreadyExistsError, create_user


def main(
    argv: list[str] | None = None,
    session_factory: Callable[[], Any] | None = None,
    ask_password: Callable[[str], str] | None = None,
) -> int:
    """Entry point.  Returns exit code (0 = success, 1 = error)."""
    if session_factory is None:
        # Import here so the module can be imported without loading settings
        from app.db.session import SessionLocal
        session_factory = SessionLocal

    if ask_password is None:
        ask_password = getpass.getpass

    parser = argparse.ArgumentParser(
        description="Create the first admin user for Organizational Brain."
    )
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--full-name", required=True, dest="full_name", help="Admin full name")
    args = parser.parse_args(argv)

    password = ask_password("Password: ")
    confirm = ask_password("Confirm password: ")

    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        return 1

    if len(password) < 12:
        print("Error: password must be at least 12 characters.", file=sys.stderr)
        return 1

    db: Session = session_factory()
    try:
        create_user(
            db,
            email=args.email,
            full_name=args.full_name,
            password=password,
            role="admin",
        )
        db.commit()
        print(f"Admin account created for {args.email}.")
        return 0
    except EmailAlreadyExistsError:
        print(f"An account with email {args.email} already exists. No changes made.")
        return 1
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
