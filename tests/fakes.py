from allocation.adapters.repository import AbstractRepository
from allocation.domain import models
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class FakeProductRepository(AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref) -> models.Product:
        return next((p for p in self._products for b in p.batches if b.reference == batchref), None)
    def list(self):
        return list(self._products)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeProductRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass
