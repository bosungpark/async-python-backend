import pytest
from starlette.testclient import TestClient

from allocation import config
from allocation.entrypoints.apis import app
from ..helpers import random_refs, api_client


client = TestClient(app)


@pytest.mark.usefixtures("postgres_db")
async def test_api_returns_allocation():
    sku, othersku=random_refs.random_sku(), random_refs.random_sku("other")
    earlybatch= random_refs.random_batchref(1)
    laterbatch = random_refs.random_batchref(2)
    otherbatch = random_refs.random_batchref(3)

    api_client.post_to_add_batch(laterbatch, sku, 100, "2022-01-02")
    api_client.post_to_add_batch(earlybatch, sku, 100, "2022-01-01")
    api_client.post_to_add_batch(otherbatch, othersku, 100, None)

    data={"orderid": random_refs.random_orderid(), "sku": sku, "qty": 3}
    url= config.get_api_url()
    r= client.post(url=f"{url}/allocate", json=data)
    assert r.status_code== 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("postgres_db")
async def test_api_returns_are_persisted():
    sku=random_refs.random_sku()
    batch1, batch2 = random_refs.random_batchref(1), random_refs.random_batchref(2)
    order1, order2 = random_refs.random_orderid(1), random_refs.random_orderid(2)

    api_client.post_to_add_batch(batch1, sku, 100, "2022-01-01")
    api_client.post_to_add_batch(batch2, sku, 100, "2022-01-02")
    # _____save_____
    line1={"orderid": order1, "sku": sku, "qty": 100}
    line2 = {"orderid": order2, "sku": sku, "qty": 100}
    url= config.get_api_url()

    r= client.post(url=f"{url}/allocate", json=line1)
    assert r.status_code== 201
    assert r.json()["batchref"] == batch1

    r = client.post(url=f"{url}/allocate", json=line2)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch2


async def test_400_for_out_of_stock():
    sku, smalll_batch, large_order= random_refs.random_sku(), random_refs.random_batchref(), random_refs.random_orderid()
    api_client.post_to_add_batch(smalll_batch, sku, 10, None)
    data={"orderid": large_order, "sku": sku, "qty": 100}
    url = config.get_api_url()

    r = client.post(url=f"{url}/allocate", json=data)
    assert r.json()["status_code"] == 400
    assert r.json()["message"] == f"out of stock sku {sku}"


@pytest.mark.usefixtures("postgres_db")
async def test_400_for_invalid_sku():
    unknown_sku, orderid= random_refs.random_sku(), random_refs.random_orderid()
    data={"orderid": orderid, "sku": unknown_sku, "qty": 100}
    url = config.get_api_url()

    r = client.post(url=f"{url}/allocate", json=data)
    assert r.json()["status_code"] == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"