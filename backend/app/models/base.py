from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

convention: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata: MetaData = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей приложения."""

    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Имя таблицы по умолчанию - имя класса в нижнем регистре."""
        return cls.__name__.lower()
