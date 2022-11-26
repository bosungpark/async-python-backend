from datetime import datetime

import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.params import Body, Query
from starlette import status

from allocation import bootstrap
from allocation.domain import commands
from allocation.domain.exceptions import OutOfStock
from allocation.service_layer import views
from allocation.service_layer.handlers import InvalidSku


app = FastAPI()
bus = bootstrap.bootstrap()


@app.post("/batch", status_code=status.HTTP_201_CREATED)
async def creat_batch(data=Body()) -> dict:
    """
    api for creat_batch
    :param data:
    :return:
    """
    eta=data["eta"]
    if eta:
        eta=datetime.fromisoformat(eta).date()

    command = commands.CreateBatch(
        ref=data["ref"],
        sku=data["sku"],
        qty=data["qty"],
        eta=eta
    )
    await bus.handle(command)
    return {"message": "OK","status_code":status.HTTP_201_CREATED}


@app.post("/allocate", status_code=status.HTTP_201_CREATED)
async def allocate(data=Body()) -> dict:
    """
    - api for allocate
    :param data:
    :return:
    """
    try:
        command = commands.Allocate(
            orderid=data["orderid"],
            sku=data["sku"],
            qty=data["qty"]
        )
        results = await bus.handle(command)
        batchref = results.pop(0)
    except (InvalidSku, OutOfStock) as e:
        return {"message": str(e),"status_code":status.HTTP_400_BAD_REQUEST}
    else:
        return {"batchref" : batchref, "status_code":status.HTTP_201_CREATED}


@app.get("/allocations/", status_code=status.HTTP_202_ACCEPTED)
async def allocations_view_endpoint(orderid: str = Query()) -> dict:
    """
    - api for getting view table
    :param orderid:
    :return:
    """
    result = await views.allocations(orderid, bus.uow)
    if not result:
        return {"message": "not found","status_code":status.HTTP_404_NOT_FOUND}
    return {"result" : result, "status_code":status.HTTP_202_ACCEPTED}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)