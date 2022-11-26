from dataclasses import dataclass
from datetime import date
from typing import Optional

from allocation.domain.types import Reference, SKU, Quantity


class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: Reference
    sku: SKU
    qty: Quantity
    eta: Optional[date] = None


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int