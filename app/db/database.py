from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core import config

# this constructs a connection string to our database
db_url = URL.create(
    drivername="postgresql+asyncpg",
    username=config.config.db_user,
    password=config.config.db_password,
    host="127.0.0.1",
    port=5432,
    database=config.config.db_name,
)

# configuration for asynchronous connection to database
# it handles connection pooling and creating connections
# Engine does not work directly with a database it requires a session
# (sessionmaker)
engine = create_async_engine(db_url, echo=True, future=True)

# factory for creating  asynchronous sessions (AsyncSession)
async_session = sessionmaker(
    # connection configuration0     -
    bind=engine,
    # connection type
    class_=AsyncSession,
    # objects remain available after committing a transaction
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
