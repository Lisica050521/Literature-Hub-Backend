import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Добавляем корневую директорию в sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# Загружаем переменные окружения
load_dotenv()

# Ещё одна настройка пути для импорта моделей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Импортируем модели, чтобы Alembic мог их увидеть
from app.models.user import User
from app.models.author import Author
from app.models.literature_item import LiteratureItem
from app.models.transaction import Transaction
from app.db.base import Base

# Метаданные для Alembic
target_metadata = Base.metadata

# Загружаем конфигурацию Alembic
config = context.config

# Устанавливаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Настраиваем логирование
fileConfig(config.config_file_name)


def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Запуск миграций в онлайн-режиме."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Выбор режима запуска миграций
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()