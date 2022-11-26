import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from allocation import config
from allocation.adapters.repository import AbstractRepository, SqlAlchemyProductRepository


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ",
))


class AbstractUnitOfWork(abc.ABC):
    products: AbstractRepository

    async def __aexit__(self, *args):
        self.rollback()

    async def __aenter__(self):
        return self

    async def commit(self):
        self._commit()

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.popleft()

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory=session_factory

    async def __aenter__(self):
        self.session : Session= self.session_factory()
        self.products = SqlAlchemyProductRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self.session.close()

    async def _commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()