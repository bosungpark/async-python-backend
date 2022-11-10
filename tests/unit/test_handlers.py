import pytest

from allocation.domain import events
from allocation.service_layer import messagebus
from tests.fakes import FakeUnitOfWork

class TestAddBatch:
    def test_add_batch(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated(
                "o1", "LAMP-1", 10, None
            ),
            uow = uow
        )

        assert uow.products.get("LAMP-1") is not None
        assert uow.committed

class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated(
                "b1", "LAMP", 100, eta=None
            ),
            uow=uow
        )

        [result] = messagebus.handle(
            events.AllocationRequired(
                "b1", "LAMP", 100
            ),
            uow=uow
        )

        assert result == "b1"