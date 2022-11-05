from datetime import date
from typing import List, Optional

from allocation.domain import models
from allocation.domain.models import SKU, Batch, OrderLine
from allocation.service_layer import unit_of_work
from allocation.service_layer.exceptions import InvalidSku


def is_valid_sku(sku: SKU, batches: List[Batch]):
    return sku in {b.sku for b in batches}


def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = models.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(models.Batch(ref, sku, qty, eta))
        uow.commit()