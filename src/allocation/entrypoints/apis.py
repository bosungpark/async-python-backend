"""
run cmd: uvicorn src.allocation.entrypoints.api:app --host=127.0.0.1 --port=8000 --reload
"""
from datetime import datetime

from fastapi import FastAPI
from fastapi.params import Body

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from allocation.service_layer import handlers
from allocation.service_layer.handlers import InvalidSku
from allocation.adapters.orm import start_mappers
from allocation.adapters.repository import SqlAlchemyBatchRepository, AbstractRepository
from allocation.config import get_postgres_uri
from allocation.domain.models import OutOfStock

start_mappers()
get_session = sessionmaker(bind=create_engine(get_postgres_uri()))
app = FastAPI()

@app.post("/allocate", status_code=201)
def allocate_endpoint(data=Body()) -> dict:
    orderid=data["orderid"]
    sku=data["sku"]
    qty=data["qty"]
    session : Session = get_session()
    repo : AbstractRepository = SqlAlchemyBatchRepository(session)
    try:
        batchref = services.allocate(orderid, sku, qty, repo, session)
    except (InvalidSku, OutOfStock) as e:
        return {"message": str(e),"status_code":400}
    else:
        return {"batchref" : batchref}

@app.post("/batch", status_code=201)
def add_batch(data=Body()) -> str:
    session : Session = get_session()
    repo : AbstractRepository = SqlAlchemyBatchRepository(session)
    eta=data["eta"]
    if eta:
        eta=datetime.fromisoformat(eta).date()

    services.add_batch(
        data["ref"],
        data["sku"],
        data["qty"],
        eta,
        repo,
        session
    )
    return "OK"