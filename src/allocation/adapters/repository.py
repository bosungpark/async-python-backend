import abc

from sqlalchemy.orm import Session

from allocation.domain import models


class AbstractRepository(abc.ABC):

    def __init__(self):
        self.seen = set()

    def add(self, product: models.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku) -> models.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: models.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> models.Product:
        raise NotImplementedError


class SqlAlchemyProductRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session :Session= session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(models.Product).\
            filter_by(sku=sku).\
            with_for_update().\
            first()