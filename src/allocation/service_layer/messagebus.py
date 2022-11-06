import email

from allocation.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
        "qkrqhtjd0806@naver.com",
        f"Out Of Stock: {event.sku}",
    )


# Type: Dict[Type[events.Event], List[Callable]]
HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}