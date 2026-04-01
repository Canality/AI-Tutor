import asyncio
from database.db import init_db
from utils.logger import logger


async def main():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
