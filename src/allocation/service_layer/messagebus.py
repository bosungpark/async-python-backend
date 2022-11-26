from collections import deque
from typing import Union, Callable

from allocation.domain import events, commands
from allocation.service_layer import unit_of_work

import logging


Message = Union[commands.Command, events.Event]
logger = logging.getLogger(__name__)

class MessageBus:
    queue: deque[Message] #TODO: make it thread safe

    def __init__(self,
                 uow: unit_of_work.AbstractUnitOfWork,
                 event_handlers: dict[type[events.Event], list[Callable]], # DI handler
                 command_handlers: dict[type[commands.Command], Callable], # DI handler
                 ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    async def handle(self, message: Message):
        results = [] # results of command or list of events
        self.queue : deque[Message] = deque([message])
        while self.queue:
            message = self.queue.popleft()
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message)
                results.append(cmd_result)
            else:
                raise Exception(f"{message} was not any of Event or Command!")
        return results


    async def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug(f"Handling {event} with handler {handler}")
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception as e:
                logger.exception(f"Failed to handle exception in {event}: {e}!")
                continue


    async def handle_command(self, command: commands.Command):
        logger.debug(f"Handling command {command}!")
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            self.queue.extend(self.uow.collect_new_events())
            return result
        except Exception:
            logger.exception(f"Exception handling command: {command}")
            raise