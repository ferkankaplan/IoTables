import argparse
import asyncio
import getpass

from iotables.config import get_settings
from iotables.database.session import create_database_engine, create_database_sessionmaker
from iotables.modules.access.identity import IdentityAccessService


async def run(username: str, password: str) -> int:
    engine = create_database_engine(get_settings())
    session_factory = create_database_sessionmaker(engine)
    async with session_factory() as session:
        result = await IdentityAccessService(session).create_platform_owner(
            username=username,
            password=password,
        )
    await engine.dispose()

    state = "created" if result.created else "exists"
    print(f"platform_owner:{state}:{result.username}:{result.user_id}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the single IoTables Platform Owner.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Platform owner password: ")
    raise SystemExit(asyncio.run(run(username=args.username, password=password)))


if __name__ == "__main__":
    main()
