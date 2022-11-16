from datetime import date

from allocation.domain import commands
from allocation.service_layer import unit_of_work, messagebus, views


def test_allocations_view(session):
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    messagebus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)
    messagebus.handle(commands.CreateBatch("sku2batch", "sku2", 50, date.today()), uow)
    messagebus.handle(commands.Allocate("order1", "sku1", 20), uow)
    messagebus.handle(commands.Allocate("order1", "sku2", 20), uow)

    messagebus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, date.today()), uow)
    messagebus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
    messagebus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

    assert views.allocations("order1", uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]
