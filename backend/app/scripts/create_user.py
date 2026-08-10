import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError

from app.core.security import hash_password
from app.infra.db.base import async_session_maker
from app.infra.db.models import UserModel


async def create_user(username: str, password: str) -> None:
    async with async_session_maker() as session:
        try:
            existing = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
        except ProgrammingError as exc:
            if "UndefinedTableError" not in str(exc.orig):
                raise
            print(
                "Database schema isn't set up yet (table 'users' is missing).\n"
                "Run: scripts/migrate.sh <dev|prod> --apply",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc

        if existing.scalar_one_or_none() is not None:
            print(f"User '{username}' already exists.", file=sys.stderr)
            raise SystemExit(1)

        session.add(UserModel(username=username, password_hash=hash_password(password)))
        await session.commit()
    print(f"User '{username}' created.")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.create_user <username>", file=sys.stderr)
        raise SystemExit(1)
    username = sys.argv[1]
    password = getpass.getpass("Password: ")
    if not password:
        print("Password must not be empty.", file=sys.stderr)
        raise SystemExit(1)
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(1)
    asyncio.run(create_user(username, password))


if __name__ == "__main__":
    main()
