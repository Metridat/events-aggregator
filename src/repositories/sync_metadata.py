from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import SyncMetadata


class SyncMetadataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_singleton(self) -> SyncMetadata:
        result = await self.session.execute(
            select(SyncMetadata).where(SyncMetadata.id == 1)
        )
        meta = result.scalar_one_or_none()
        if meta is not None:
            return meta
        meta = SyncMetadata(id=1)
        self.session.add(meta)
        await self.session.flush()
        return meta
