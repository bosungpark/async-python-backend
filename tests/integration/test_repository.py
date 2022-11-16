from allocation.domain import models
from tests import fakes


def test_get_by_batchref():
    repo = fakes.FakeProductRepository(products=[])
    b1 = models.Batch(ref="b1", sku="sku1", qty=100, eta=None)
    b2 = models.Batch(ref="b2", sku="sku1", qty=100, eta=None)
    b3 = models.Batch(ref="b3", sku="sku2", qty=100, eta=None)
    p1 = models.Product(sku="sku1", batches=[b1, b2])
    p2 = models.Product(sku="sku2", batches=[b3])
    repo.add(p1)
    repo.add(p2)
    assert repo.get_by_batchref("b2") == p1
    assert repo.get_by_batchref("b3") == p2
