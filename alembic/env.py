from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.core.config import settings
from app.db.session import Base

# Import all models here
from app.models.user import User
from app.models.location import Country, State
from app.models.vendor import Vendor
from app.models.category import Category
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.order import Order, OrderLine
from app.models.attribute import ProductAttribute
from app.models.attribute_value import ProductAttributeValue
from app.models.basket import Basket, BasketItem

def get_url():
    return settings.SQLALCHEMY_DATABASE_URI

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = str(get_url())
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
