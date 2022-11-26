from typing import List, TYPE_CHECKING

from allocation.domain import models, events, commands
from allocation.domain.models import SKU, Batch, OrderLine
from allocation.service_layer import unit_of_work
from allocation.service_layer.exceptions import InvalidSku
from ..domain.exceptions import OutOfStock
from ..entrypoints import redis_eventpublisher

if TYPE_CHECKING:
    from . import unit_of_work


def is_valid_sku(sku: SKU, batches: List[Batch]) -> bool:
    return sku in {b.sku for b in batches}


async def allocate(
        command: commands.Allocate,
        uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = OrderLine(command.orderid, command.sku, command.qty)
    async with uow:
        product = await uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref : str = product.allocate(line)
        await uow.commit()
    return batchref


async def add_batch(
        command: commands.CreateBatch,
        uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    async with uow:
        product = await uow.products.get(sku=command.sku)
        if product is None:
            product = models.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(models.Batch(command.ref,
                                            command.sku,
                                            command.qty,
                                            command.eta))
        await uow.commit()


async def change_batch_quantity(
        command: commands.ChangeBatchQuantity,
        uow: unit_of_work.AbstractUnitOfWork,
):
    async with uow:
        product = await uow.products.get_by_batchref(batchref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        await uow.commit()


async def send_out_of_stock_notification(event: events.OutOfStock,
                                   uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    async with uow:
        #TODO: send actual mail!
        print(f"Out Of Stock: {event.sku}")
        raise OutOfStock(f'out of stock sku {event.sku}')


async def publish_allocated_event(
        event: events.Allocated,
        uow: unit_of_work.AbstractUnitOfWork
):
    async with uow:
        redis_eventpublisher.publish("line_allocated", event)


async def add_allocation_to_read_only_model(
        event: events.Allocated,
        uow: unit_of_work.SqlAlchemyUnitOfWork
):
    async with uow:
        await uow.session.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
            """,
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref),
        )
        await uow.commit()


EVENT_HANDLERS = {
    events.Allocated: [publish_allocated_event,
                       add_allocation_to_read_only_model],
    events.OutOfStock: [send_out_of_stock_notification],
}


COMMAND_HANDLERS = {
    commands.CreateBatch: add_batch,
    commands.Allocate: allocate,
    commands.ChangeBatchQuantity: change_batch_quantity
}