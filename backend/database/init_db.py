import asyncio
from database.db import init_db, async_engine
from utils.logger import logger


async def main():
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialization complete!")
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
