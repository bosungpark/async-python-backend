import asyncio

from allocation.service_layer import unit_of_work


async def allocations(orderid: str,
                uow: unit_of_work.SqlAlchemyUnitOfWork):
    async with uow:
        results_task = list(uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
            """,
            dict(orderid=orderid),
        ))
        results = await asyncio.gather(results_task)
    return [dict(r) for r in results]