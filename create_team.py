import asyncio
import sys
import argparse
from sqlalchemy.future import select
from app.database import async_session
from app.models import Team

async def create_team(name: str, passcode: str, points: int = 1000):
    async with async_session() as db:
        # Check if team name already exists
        result = await db.execute(select(Team).where(Team.name == name))
        existing_team = result.scalars().first()
        if existing_team:
            print(f"[-] Error: Team with name '{name}' already exists (ID: {existing_team.id}).")
            return

        new_team = Team(
            name=name,
            passcode=passcode,
            points=points
        )
        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)
        print(f"[+] Successfully created team!")
        print(f"    - ID: {new_team.id}")
        print(f"    - Name: {new_team.name}")
        print(f"    - Passcode: {new_team.passcode}")
        print(f"    - Starting Points: {new_team.points}")

def main():
    parser = argparse.ArgumentParser(description="Create a new team in MPL database.")
    parser.add_argument("--name", type=str, default="Team Delta", help="Name of the team")
    parser.add_argument("--passcode", type=str, default="delta123", help="Passcode for team login")
    parser.add_argument("--points", type=int, default=1000, help="Initial points for the team")
    
    args = parser.parse_args()
    asyncio.run(create_team(args.name, args.passcode, args.points))

if __name__ == "__main__":
    main()
