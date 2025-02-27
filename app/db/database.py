from sqlalchemy.ext.asyncio import create_async_engine

from sqlmodel import SQLModel
from app.core import config
from sqlalchemy.engine import URL


db_url = URL.create(
    drivername="postgresql+asyncpg",
    username=config.config.db_user,
    password=config.config.db_password,
    host="127.0.0.1",
    port=5432,
    database=config.config.db_name,
)


engine = create_async_engine(db_url, echo=True, future=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
