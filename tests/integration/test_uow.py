import threading
import time
import traceback

import pytest
from sqlalchemy.orm import Session

from allocation.domain import models
from allocation.service_layer import unit_of_work
from allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from tests.helpers import random_refs


async def insert_batch(session:Session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )

async def get_allocated_batch_ref(session:Session, orderid, sku):
    [[orderlineid]]=session.execute(
        "SELECT id FROM order_lines WHERE orderid= :orderid AND sku= :sku",
        dict(orderid=orderid,sku=sku)
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE orderline_id= :orderline_id",
        dict(orderline_id=orderlineid)
    )
    return batchref

async def test_rolls_back_uncommited_work_by_default(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session,"b1", "plinth", 100, None)
        # uow.commit()
    new_sesson:Session=session_factory()
    rows=list(new_sesson.execute("SELECT * FROM 'batches'"))
    assert rows==[]

async def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session,"b1", "plinth", 100, None)
            raise MyException
    new_sesson:Session=session_factory()
    rows=list(new_sesson.execute("SELECT * FROM 'batches'"))
    assert rows==[]

async def try_to_allocate(orderid, sku, exceptions):
    line = models.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)

async def insert_batch_with_product_version(session:Session, ref, sku, qty, eta,  product_version=1):
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        dict(sku=sku, version=product_version),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )

async def test_concurrent_updates_to_version_are_not_allowed(postgres_session_factory):
    sku, batch = random_refs.random_sku(), random_refs.random_batchref()
    session = postgres_session_factory()
    insert_batch_with_product_version(session, batch, sku, 100, eta=None, product_version=1)
    session.commit()

    order1, order2 = random_refs.random_orderid(1), random_refs.random_orderid(2)
    exceptions = []  # type: List[Exception]
    try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
    try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        dict(sku=sku),
    )
    assert version == 2
    # [exception] = exceptions
    # assert "could not serialize access due to concurrent update" in str(exception)

    orders = session.execute(
        "SELECT orderid FROM allocations"
        " JOIN batches ON allocations.batch_id = batches.id"
        " JOIN order_lines ON allocations.orderline_id = order_lines.id"
        " WHERE order_lines.sku=:sku",
        dict(sku=sku),
    )
    assert orders.rowcount == 1
    with unit_of_work.SqlAlchemyUnitOfWork() as uow:
        uow.session.execute("select 1")