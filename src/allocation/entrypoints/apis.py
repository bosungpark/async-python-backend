from datetime import datetime

import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.params import Body
from starlette import status

from allocation.domain import events
from allocation.domain.exceptions import OutOfStock
from allocation.service_layer import messagebus, unit_of_work
from allocation.service_layer.handlers import InvalidSku
from allocation.adapters.orm import start_mappers


app = FastAPI()
start_mappers()


@app.post("/batch", status_code=status.HTTP_201_CREATED)
def add_batch(data=Body()) -> str:
    """
    api for add_batch
    :param data:
    :return:
    """
    eta=data["eta"]
    if eta:
        eta=datetime.fromisoformat(eta).date()

    event = events.BatchCreated(
        ref=data["ref"],
        sku=data["sku"],
        qty=data["qty"],
        eta=eta
    )
    messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    return {"message": "OK","status_code":status.HTTP_201_CREATED}


@app.post("/allocate", status_code=status.HTTP_201_CREATED)
def allocate_endpoint(data=Body()) -> dict:
    """
    - api for allocate_endpoint
    :param data:
    :return:
    """
    try:
        event = events.AllocationRequired(
            orderid=data["orderid"],
            sku=data["sku"],
            qty=data["qty"]
        )
        results = messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)
    except (InvalidSku, OutOfStock) as e:
        return {"message": str(e),"status_code":status.HTTP_400_BAD_REQUEST}
    else:
        return {"batchref" : batchref, "status_code":status.HTTP_201_CREATED}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)