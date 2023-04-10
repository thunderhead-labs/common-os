"""
The base repository class
"""
import abc
import enum
import typing

from sqlalchemy.orm import Session

from ..schema import Base


class TransactionTypes(enum.IntEnum):
    NONE = 0
    COMMIT = 1
    FLUSH = 2


class DatabaseConnectionMode(enum.IntEnum):
    WRITE = 0
    READ = 1


class AbstractRepository(abc.ABC):
    @staticmethod
    def save(
        session: Session,
        o,
        transaction_type: TransactionTypes = TransactionTypes.NONE,
    ) -> bool:
        try:
            session.add(instance=o)

            if transaction_type == TransactionTypes.COMMIT:
                session.commit()

            elif transaction_type == TransactionTypes.FLUSH:
                session.flush()

            return True

        except Exception:
            if transaction_type == TransactionTypes.COMMIT:
                session.rollback()

            return False

    @staticmethod
    def save_many(
        session: Session,
        objs,
        transaction_type: TransactionTypes = TransactionTypes.NONE,
    ) -> bool:
        try:
            session.add_all(objs)

            if transaction_type == TransactionTypes.COMMIT:
                session.commit()

            elif transaction_type == TransactionTypes.FLUSH:
                session.flush()

            return True

        except Exception:
            if transaction_type == TransactionTypes.COMMIT:
                session.rollback()

            return False

    @staticmethod
    def delete(session: Session, obj) -> bool:
        try:
            session.delete(obj)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False

    @staticmethod
    def upsert(
        session: Session,
        table_object: Base,
        transaction_type: TransactionTypes = TransactionTypes.NONE,
    ) -> bool:
        try:
            session.merge(table_object)

            if transaction_type == TransactionTypes.COMMIT:
                session.commit()

            elif transaction_type == TransactionTypes.FLUSH:
                session.flush()

            return True

        except Exception:
            if transaction_type == TransactionTypes.COMMIT:
                session.rollback()

            return False

    @staticmethod
    def upsert_many(
        session: Session,
        objs: typing.Iterable[Base],
        transaction_type: TransactionTypes = TransactionTypes.NONE,
    ) -> bool:
        try:
            for obj in objs:
                session.merge(obj)

            if transaction_type == TransactionTypes.COMMIT:
                session.commit()

            elif transaction_type == TransactionTypes.FLUSH:
                session.flush()

            return True

        except Exception:
            if transaction_type == TransactionTypes.COMMIT:
                session.rollback()

            return False
