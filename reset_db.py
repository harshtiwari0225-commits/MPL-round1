#!/usr/bin/env python3
"""Drop and recreate every table. Use during development when the schema changes.

    python reset_db.py
    python seed.py

WARNING: this deletes all teams, questions, submissions and scores.
"""
import asyncio
import sys

from app.core.config import settings
from app.database import engine, Base
from app import models  # noqa: F401  (registers the tables)


async def main():
    url = settings.DATABASE_URL.split("@")[-1]
    if "sqlite" not in settings.DATABASE_URL:
        answer = input(f"About to DROP ALL TABLES in {url}. Type 'yes' to continue: ")
        if answer.strip().lower() != "yes":
            print("Aborted.")
            return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)
