from collections import deque

from allocation.domain import events
from allocation.service_layer import unit_of_work
from allocation.service_layer import handlers


def handle(event: events.Event,
           uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue : deque[events.Event] = deque([event])
    while queue:
        event = queue.popleft()
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow=uow))
            queue.extend(uow.collect_new_events())
    return results


# Type: Dict[Type[events.Event], List[Callable]]
HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
    events.BatchQuantityChanged: [handlers.change_batch_quantity]
}