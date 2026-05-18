import asyncio
import models.user

from database.connection import init_db, close_db


async def main():
    await init_db()
    await close_db()


asyncio.run(main())