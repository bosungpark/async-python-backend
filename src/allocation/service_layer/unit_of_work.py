import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from allocation import config
from allocation.adapters.repository import AbstractRepository, SqlAlchemyProductRepository, SqlAlchemyBatchRepository


DEFAULT_SESSION_FACTORY=sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ",
))


class AbstractUnitOfWork(abc.ABC):
    products: AbstractRepository
    batches: AbstractRepository

    def __exit__(self, *args):
        self.rollback()

    def __enter__(self):
        return self

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory=session_factory

    def __enter__(self):
        self.session : Session= self.session_factory()
        self.products = SqlAlchemyProductRepository(self.session)
        self.batches = SqlAlchemyBatchRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()