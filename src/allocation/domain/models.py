from collections import deque
from datetime import date
from typing import Optional, List

from allocation.domain import events
from allocation.domain.events import Event
from allocation.domain.exceptions import OutOfStock
from allocation.domain.types import Reference, SKU, Quantity

from dataclasses import dataclass


@dataclass
class OrderLine:
    orderid:str
    sku: str
    qty: int

    def __hash__(self):
        return hash(self.orderid)


class Batch:
    def __init__(self, ref: Reference, sku: SKU, qty: Quantity, eta: Optional[date]):
        self.reference=ref
        self.sku=sku
        self.eta=eta
        self._purchased_quantity=qty
        self._allocations=set()

    def allocate(self, line:OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    @property
    def allocated_quantity(self)->int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity-self.allocated_quantity

    def can_allocate(self,line:OrderLine)->bool:
        return self.sku==line.sku and self.available_quantity>=line.qty

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference==self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta>other.eta


class Product:
    events: deque[Event] = deque()

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next((b for b in sorted(self.batches) if b.can_allocate(line)),None)
            if not batch:
                raise OutOfStock
            batch.allocate(line)
            self.version_number += 1
        except OutOfStock:
            self.events.append(events.OutOfStock(line.sku))
        else:
            return batch.reference

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(events.AllocationRequired(line.orderid, line.sku, line.qty))
