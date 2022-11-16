from datetime import datetime

import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.params import Body, Query
from starlette import status

from allocation.domain import commands
from allocation.domain.exceptions import OutOfStock
from allocation.service_layer import messagebus, unit_of_work, views
from allocation.service_layer.handlers import InvalidSku
from allocation.adapters.orm import start_mappers


app = FastAPI()
start_mappers()


@app.post("/batch", status_code=status.HTTP_201_CREATED)
def creat_batch(data=Body()) -> str:
    """
    api for creat_batch
    :param data:
    :return:
    """
    eta=data["eta"]
    if eta:
        eta=datetime.fromisoformat(eta).date()

    uow = unit_of_work.SqlAlchemyUnitOfWork()
    command = commands.CreateBatch(
        ref=data["ref"],
        sku=data["sku"],
        qty=data["qty"],
        eta=eta
    )
    messagebus.handle(command, uow)
    return {"message": "OK","status_code":status.HTTP_201_CREATED}


@app.post("/allocate", status_code=status.HTTP_201_CREATED)
def allocate(data=Body()) -> dict:
    """
    - api for allocate
    :param data:
    :return:
    """
    try:
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        command = commands.Allocate(
            orderid=data["orderid"],
            sku=data["sku"],
            qty=data["qty"]
        )
        results = messagebus.handle(command, uow)
        batchref = results.pop(0)
    except (InvalidSku, OutOfStock) as e:
        return {"message": str(e),"status_code":status.HTTP_400_BAD_REQUEST}
    else:
        return {"batchref" : batchref, "status_code":status.HTTP_201_CREATED}


@app.get("/allocations/", status_code=status.HTTP_202_ACCEPTED)
def allocations_view_endpoint(orderid: str = Query()) -> dict:
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return {"message": "not found","status_code":status.HTTP_404_NOT_FOUND}
    return {"result" : result, "status_code":status.HTTP_202_ACCEPTED}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)