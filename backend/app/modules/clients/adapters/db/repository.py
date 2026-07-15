# app/modules/clients/adapters/db/repository.py
import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client


class ClientsRepository(BaseRepository[ClientModel, Client, ClientFilters]):
    model = ClientModel
    filters_type = ClientFilters

    def _to_entity(self, row: ClientModel) -> Client:
        return Client(
            id=row.id,
            document=row.document,
            name=row.name,
            municipal_registration=row.municipal_registration,
            phone=row.phone,
            email=row.email,
            zip_code=row.zip_code,
            street=row.street,
            number=row.number,
            complement=row.complement,
            neighborhood=row.neighborhood,
            ibge_city_code=row.ibge_city_code,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: ClientFilters) -> sa.Select:
        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(
                sa.or_(
                    ClientModel.name.ilike(pattern),
                    ClientModel.document.ilike(pattern),
                )
            )
        return stmt

    async def get_by_document_or_none(self, document: str) -> Client | None:
        result = await self._session.execute(
            sa.select(self.model).where(self.model.document == document)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None
