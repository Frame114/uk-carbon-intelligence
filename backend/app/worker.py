import asyncio
import logging

from app.clients.neso import NesoClient
from app.core.database import SessionFactory, engine
from app.services.ingestion import run_collector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def main() -> None:
    client = NesoClient()
    try:
        await run_collector(SessionFactory, client)
    finally:
        await client.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
