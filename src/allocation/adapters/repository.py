import abc

from sqlalchemy.orm import Session

from allocation.adapters import orm
from allocation.domain import models


class AbstractRepository(abc.ABC):

    def __init__(self):
        self.seen = set()

    def add(self, product: models.Product):
        self._add(product)
        self.seen.add(product)

    async def get(self, sku) -> models.Product:
        product = await self._get(sku)
        if product:
            self.seen.add(product)
        return product

    async def get_by_batchref(self, batchref) -> models.Product:
        product = await self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: models.Product):
        raise NotImplementedError

    @abc.abstractmethod
    async def _get(self, sku) -> models.Product:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_by_batchref(self, batchref) -> models.Product:
        raise NotImplementedError


class SqlAlchemyProductRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session :Session= session

    def _add(self, product):
        self.session.add(product)

    async def _get(self, sku):
        return await self.session.query(models.Product).\
            filter_by(sku=sku).\
            with_for_update().\
            first()

    async def _get_by_batchref(self, batchref) -> models.Product:
        return await (
            self.session.query(models.Product)
                .join(models.Batch)
                .filter(orm.batches.c.reference == batchref)
                .first()
        )