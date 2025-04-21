import ssl

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core import config

# this constructs a connection string to our database
db_url = URL.create(
    drivername="postgresql+asyncpg",
    username=config.config.db_user,
    password=config.config.db_password,
    host=config.config.db_host,
    port=config.config.db_port,
    database=config.config.db_name,
)

# configuration for asynchronous connection to database
# it handles connection pooling and creating connections
# Engine does not work directly with a database it requires a session
# (sessionmaker)

# upgrade connection to use SSL
connect_args = {}
if config.config.render_env == config.Environment.PRODUCTION:
    ssl_ctx = ssl.create_default_context()
    connect_args["ssl"] = ssl_ctx

ssl_ctx = ssl.create_default_context()

engine = create_async_engine(
    db_url,
    echo=True,
    future=True,
    connect_args=connect_args,
)

print(db_url)

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
