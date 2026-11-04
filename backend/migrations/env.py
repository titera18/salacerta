from alembic import context

from salacerta.infrastructure.database import Base, build_engine
from salacerta.infrastructure.settings import Settings

url = context.config.get_main_option("sqlalchemy.url") or Settings().database_url


def run_migrations() -> None:
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return

    with build_engine(url).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
