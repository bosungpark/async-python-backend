from datetime import date

from allocation.domain import commands
from allocation.service_layer import  views


def test_allocations_view(messagebus_for_test):
    messagebus_for_test.handle(message=commands.CreateBatch("sku1batch", "sku1", 50, None))
    messagebus_for_test.handle(message=commands.CreateBatch("sku2batch", "sku2", 50, date.today()))
    messagebus_for_test.handle(message=commands.Allocate("order1", "sku1", 20))
    messagebus_for_test.handle(message=commands.Allocate("order1", "sku2", 20))

    messagebus_for_test.handle(message=commands.CreateBatch("sku1batch-later", "sku1", 50, date.today()))
    messagebus_for_test.handle(message=commands.Allocate("otherorder", "sku1", 30))
    messagebus_for_test.handle(message=commands.Allocate("otherorder", "sku2", 10))

    assert views.allocations("order1", messagebus_for_test.uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]
