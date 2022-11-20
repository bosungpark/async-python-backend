import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ArgumentError
from sqlalchemy.orm import sessionmaker, clear_mappers

from allocation import config, bootstrap
from allocation.adapters.orm import metadata, start_mappers
from allocation.service_layer import unit_of_work
from tests import fakes


@pytest.fixture()
def bootstrap_for_test():
    return bootstrap.bootstrap(
        start_orm=False,
        uow= fakes.FakeUnitOfWork(), # not using session just []
        publish= lambda *args: None # noops
    )


@pytest.fixture()
def messagebus_for_test(session_factory):
    bus = bootstrap.bootstrap(
        start_orm=False,
        uow= unit_of_work.SqlAlchemyUnitOfWork(session_factory), # in memory session
        publish= lambda *args: None # noops
    )
    yield bus
    clear_mappers()


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture(scope="function")
def session(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    try:
        start_mappers()
        yield sessionmaker(bind=postgres_db)
        clear_mappers()
    except ArgumentError:
        yield sessionmaker(bind=postgres_db)
        clear_mappers()


@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()


# TODO: deprecate
# def wait_for_webapp_to_come_up():
#     deadline = time.time() + 10
#     url = config.get_api_url()
#     while time.time() < deadline:
#         try:
#             return requests.get(url)
#         except ConnectionError:
#             time.sleep(0.5)
#     pytest.fail("API never came up")


# TODO: deprecate
# @pytest.fixture
# def restart_api():
#     (Path(__file__).parent.parent / "src/allocation/entrypoints/apis.py").touch()
#     time.sleep(1)
#     wait_for_webapp_to_come_up()


# TODO: deprecate
# @pytest.fixture
# def add_stock(postgres_session):
#     batches_added = set()
#     skus_added = set()
#
#     def _add_stock(lines):
#         for ref, sku, qty, eta in lines:
#             postgres_session.execute(
#                 "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
#                 " VALUES (:ref, :sku, :qty, :eta)",
#                 dict(ref=ref, sku=sku, qty=qty, eta=eta),
#             )
#             [[batch_id]] = postgres_session.execute(
#                 "SELECT id FROM batches WHERE reference=:ref AND sku=:sku",
#                 dict(ref=ref, sku=sku),
#             )
#             batches_added.add(batch_id)
#             skus_added.add(sku)
#         postgres_session.commit()
#
#     yield _add_stock
#
#     for batch_id in batches_added:
#         postgres_session.execute(
#             "DELETE FROM allocations WHERE batch_id=:batch_id",
#             dict(batch_id=batch_id),
#         )
#         postgres_session.execute(
#             "DELETE FROM batches WHERE id=:batch_id", dict(batch_id=batch_id),
#         )
#     for sku in skus_added:
#         postgres_session.execute(
#             "DELETE FROM order_lines WHERE sku=:sku", dict(sku=sku),
#         )
#         postgres_session.commit()