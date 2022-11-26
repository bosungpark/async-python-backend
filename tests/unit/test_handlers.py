import pytest

from datetime import date

from allocation.domain import commands
from allocation.service_layer import messagebus
from tests.fakes import FakeUnitOfWork


class TestAddBatch:
    async def test_add_batch(self, bootstrap_for_test):
        messagebus = bootstrap_for_test
        messagebus.handle(
            commands.CreateBatch(
                "o1", "LAMP-1", 10, None
            ),
        )

        assert messagebus.uow.products.get("LAMP-1") is not None
        assert messagebus.uow.committed


class TestAllocate:
    async def test_returns_allocation(self, bootstrap_for_test):
        messagebus = bootstrap_for_test
        messagebus.handle(
            commands.CreateBatch(
                "b1", "LAMP", 100, eta=None
            ),
        )

        [result] = messagebus.handle(
            commands.Allocate(
                "b1", "LAMP", 100
            ),
        )

        assert result == "b1"


class TestChangeBatchQuantity:
    async def test_changes_available_quantity(self, bootstrap_for_test):
        messagebus = bootstrap_for_test
        messagebus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None)
        )
        [batch] = messagebus.uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        messagebus.handle(commands.ChangeBatchQuantity("batch1", 50))

        assert batch.available_quantity == 50

    async def test_reallocates_if_necessary(self, bootstrap_for_test):
        messagebus = bootstrap_for_test
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e)
        [batch1, batch2] = messagebus.uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(commands.ChangeBatchQuantity("batch1", 25))

        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30