from dataclasses import dataclass


@dataclass
class OrderLine:
    orderid:str
    sku: str
    qty: int

    def __hash__(self):
        return hash(self.orderid)