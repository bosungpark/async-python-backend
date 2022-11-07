import email
from typing import List

from allocation.domain import models, events
from allocation.domain.models import SKU, Batch, OrderLine
from allocation.service_layer import unit_of_work
from allocation.service_layer.exceptions import InvalidSku


def is_valid_sku(sku: SKU, batches: List[Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_batch(
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = models.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(models.Batch(event.ref,
                                            event.sku,
                                            event.qty,
                                            event.eta))
        uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock,
                                   uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        email.send_mail(
            "qkrqhtjd0806@naver.com",
            f"Out Of Stock: {event.sku}",
        )