# app/integrations/betha/counter.py
import sqlalchemy as sa
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class EmissionCounterModel(Base):
    __tablename__ = "emission_counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serie: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    last_n: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


async def next_n_dps(session: AsyncSession, serie: str) -> int:
    """Retorna o próximo nDPS e incrementa o contador atomicamente."""
    await session.execute(
        insert(EmissionCounterModel)
        .values(serie=serie, last_n=0)
        .on_conflict_do_nothing(index_elements=["serie"])
    )
    await session.flush()

    result = await session.execute(
        sa.select(EmissionCounterModel)
        .where(EmissionCounterModel.serie == serie)
        .with_for_update()
    )
    counter = result.scalar_one()
    counter.last_n += 1
    await session.flush()
    return counter.last_n
