from typing import List, TYPE_CHECKING

from allocation.domain import models, events, commands
from allocation.domain.models import SKU, Batch, OrderLine
from allocation.service_layer import unit_of_work
from allocation.service_layer.exceptions import InvalidSku
from ..domain.exceptions import OutOfStock
from ..entrypoints import redis_eventconsumer

if TYPE_CHECKING:
    from . import unit_of_work


def is_valid_sku(sku: SKU, batches: List[Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(
        command: commands.Allocate,
        uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_batch(
        command: commands.CreateBatch,
        uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = models.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(models.Batch(command.ref,
                                            command.sku,
                                            command.qty,
                                            command.eta))
        uow.commit()


def change_batch_quantity(
        command: commands.ChangeBatchQuantity,
        uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock,
                                   uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        #TODO: send actual mail!
        print(f"Out Of Stock: {event.sku}")
        raise OutOfStock(f'out of stock sku {event.sku}')


def publish_allocated_event(
        event: events.Allocated,
        uow: unit_of_work.AbstractUnitOfWork
):
    with uow:
        redis_eventconsumer.publish("line_allocated", event)


def add_allocation_to_read_model(
        event: events.Allocated,
        uow: unit_of_work.SqlAlchemyUnitOfWork
):
    with uow:
        uow.session.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
            """,
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref),
        )
        uow.commit()