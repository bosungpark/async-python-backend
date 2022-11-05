from allocation.adapters.repository import AbstractRepository
from allocation.domain.models import Batch
from allocation.service_layer.unit_of_work import AbstractUnitOfWork

class FakeBatchRepository(AbstractRepository):
    def __init__(self,batches):
        self._batches=set(batches)


    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference==reference)

    def list(self):
        return list(self._batches)

    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeBatchRepository([
            Batch(ref, sku, qty, eta=None)
        ])


class FakeProductRepository(AbstractRepository):
    def __init__(self, products):
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next(p for p in self._products if p.sku == sku)

    def list(self):
        return list(self._products)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeBatchRepository([])
        self.products = FakeProductRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
