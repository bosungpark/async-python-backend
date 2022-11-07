from collections import deque
from typing import List

from allocation.domain import events
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import send_out_of_stock_notification


def handle(event: events.Event,
           uow: unit_of_work.AbstractUnitOfWork):
    queue : deque[events.Event] = deque([event])
    while queue:
        event = queue.popleft()
        for handler in HANDLERS[type(event)]:
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())


# Type: Dict[Type[events.Event], List[Callable]]
HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}