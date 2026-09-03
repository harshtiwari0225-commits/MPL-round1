import asyncio
import argparse
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models import Team


async def create_team(name: str, passcode: str, points: int = 1000):
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(Team).where(Team.name == name))).scalars().first()
        if existing:
            print(f"[-] Error: Team '{name}' already exists (ID: {existing.id}).")
            return

        new_team = Team(name=name, passcode=passcode, points=points)
        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)
        print("[+] Successfully created team!")
        print(f"    - ID: {new_team.id}")
        print(f"    - Name: {new_team.name}")
        print(f"    - Passcode: {new_team.passcode}")
        print(f"    - Starting Points: {new_team.points}")


def main():
    parser = argparse.ArgumentParser(description="Create a new team in the MPL database.")
    parser.add_argument("--name", type=str, default="Team Delta", help="Name of the team")
    parser.add_argument("--passcode", type=str, default="delta123", help="Passcode for login")
    parser.add_argument("--points", type=int, default=1000, help="Initial points")
    args = parser.parse_args()
    asyncio.run(create_team(args.name, args.passcode, args.points))


if __name__ == "__main__":
    main()
