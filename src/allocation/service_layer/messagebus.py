from collections import deque
from typing import Union, List

from allocation.domain import events, commands
from allocation.service_layer import unit_of_work
from allocation.service_layer import handlers

import logging

Message = Union[commands.Command, events.Event]
logger = logging.getLogger(__name__)


def handle(message: Message,
           uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue : deque[Message] = deque([message])
    while queue:
        message = queue.popleft()
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} was not any of Event or Command!")
    return results


def handle_event(event: events.Event,
                 queue: List[Message],
                 uow: unit_of_work.AbstractUnitOfWork):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug(f"Handling {event} with handler {handler}")
            handler(event,uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception(f"Exception handling event: {event}")
            continue


def handle_command(command: commands.Command,
                   queue: List[Message],
                   uow: unit_of_work.AbstractUnitOfWork):
    logger.debug(f"Handling command {command}!")
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception(f"Exception handling command: {command}")
        raise


EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}


COMMAND_HANDLERS = {
    commands.CreateBatch: handlers.add_batch,
    commands.Allocate: handlers.allocate,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity
}