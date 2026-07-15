from typing import Annotated

from fastapi import Depends

from app.core.actors.user import UserActor
from app.core.exceptions import UnauthorizedError
from app.core.security.dependencies import SubjectDep
from app.modules.users.adapters.db.factories import make_unit_of_work
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork
from app.modules.users.adapters.http.schemas import UsersPaginationFilters
from app.modules.users.application.dtos.filters import UserFilters

UsersFiltersDep = Annotated[UsersPaginationFilters, Depends()]
UsersUnitOfWorkDep = Annotated[UsersUnitOfWork, Depends(make_unit_of_work)]


async def get_current_actor(
    user_id: SubjectDep,
    uow: UsersUnitOfWorkDep,
) -> UserActor:
    """Resolve o ator atual a partir do `sub` do token, validando o usuário."""

    async with uow:
        user = await uow.users.get_by_id_or_none(user_id)

    if user is None or not user.is_active:
        raise UnauthorizedError("Usuário inativo ou não encontrado.")

    return UserActor(user_id=user.id)


def get_pagination_filters(
    query_params: Annotated[UsersPaginationFilters, Depends()],
) -> UserFilters:
    """
    Dependência para obter os filtros de paginação nos query params.
    """

    return UserFilters(
        q=query_params.q,
        is_active=query_params.is_active,
    )


UserActorDep = Annotated[UserActor, Depends(get_current_actor)]
PaginationFiltersDep = Annotated[UserFilters, Depends(get_pagination_filters)]
