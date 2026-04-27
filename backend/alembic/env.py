import asyncio
from logging.config import fileConfig

from sqlalchemy import Column, MetaData, PrimaryKeyConstraint, String, Table, inspect, text
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from alembic.ddl.impl import DefaultImpl
from app.core.config import settings
import ssl

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Alembic stores options in ConfigParser, where "%" starts interpolation.
# Escaping keeps encoded passwords such as "%40" valid when read back.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.base_class import Base
from app.db.models import *  # noqa: F401,F403 - register all ORM models
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

ALEMBIC_VERSION_TABLE = "alembic_version"
ALEMBIC_VERSION_LENGTH = 255


def wide_version_table_impl(
    cls,
    *,
    version_table: str,
    version_table_schema: str | None,
    version_table_pk: bool,
    **kw,
) -> Table:
    """Override Alembic's default VARCHAR(32) revision column."""
    version_table_obj = Table(
        version_table,
        MetaData(),
        Column("version_num", String(ALEMBIC_VERSION_LENGTH), nullable=False),
        schema=version_table_schema,
    )
    if version_table_pk:
        version_table_obj.append_constraint(
            PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc")
        )
    return version_table_obj


DefaultImpl.version_table_impl = classmethod(wide_version_table_impl)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def ensure_alembic_version_table(connection: Connection) -> None:
    """Use a wider Alembic version column for timestamp-style revision IDs."""
    inspector = inspect(connection)
    table_names = inspector.get_table_names()

    if ALEMBIC_VERSION_TABLE not in table_names:
        return

    columns = {
        column["name"]: column
        for column in inspector.get_columns(ALEMBIC_VERSION_TABLE)
    }
    version_column = columns.get("version_num")
    column_type = getattr(version_column.get("type"), "length", None) if version_column else None

    if column_type is None or column_type < ALEMBIC_VERSION_LENGTH:
        connection.execute(
            text(
                f"""
                ALTER TABLE {ALEMBIC_VERSION_TABLE}
                ALTER COLUMN version_num TYPE VARCHAR({ALEMBIC_VERSION_LENGTH})
                """
            )
        )


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        ensure_alembic_version_table(connection)
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connect_args = {}
    if settings.database_url.startswith("postgresql+asyncpg"):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl": ssl_context, "statement_cache_size": 0}

    connectable = create_async_engine(
        settings.database_url,
        connect_args=connect_args,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
