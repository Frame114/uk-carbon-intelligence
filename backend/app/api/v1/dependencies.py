from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.neso import NesoClient
from app.core.database import get_session


async def get_neso_client(request: Request) -> AsyncIterator[NesoClient]:
    yield request.app.state.neso_client


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session
