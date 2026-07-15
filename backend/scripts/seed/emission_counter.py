# scripts/seed/emission_counter.py
import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.core.db.session import db
from app.integrations.betha.counter import EmissionCounterModel


async def seed() -> None:
    session_factory = db.create_session
    async with session_factory() as session:
        await session.execute(
            insert(EmissionCounterModel)
            .values(serie="900", last_n=0)
            .on_conflict_do_nothing(index_elements=["serie"])
        )
        await session.commit()
    print("Seed emission_counter concluído.")


if __name__ == "__main__":
    asyncio.run(seed())
