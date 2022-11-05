import abc

from sqlalchemy.orm import Session

from allocation.domain import models


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: models.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku) -> models.Product:
        raise NotImplementedError


class SqlAlchemyProductRepository(AbstractRepository):
    def __init__(self, session):
        self.session :Session= session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(models.Product).\
            filter_by(sku=sku).\
            with_for_update().\
            first()

class SqlAlchemyBatchRepository(AbstractRepository):
    def __init__(self, session):
        self.session :Session= session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(models.Batch).\
            filter_by(reference=reference).\
            with_for_update().\
            first()