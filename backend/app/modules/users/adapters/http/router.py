import uuid

from fastapi import APIRouter, Depends

from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.users.adapters.http.dependencies import (
    PaginationFiltersDep,
    UserActorDep,
    UsersUnitOfWorkDep,
    get_current_actor,
)
from app.modules.users.adapters.http.schemas import (
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.users.application.dtos.commands import (
    CreateUserCommand,
    UpdateUserCommand,
)
from app.modules.users.application.use_cases.activate import UsersActivator
from app.modules.users.application.use_cases.create import UsersCreator
from app.modules.users.application.use_cases.delete import UsersDeleter
from app.modules.users.application.use_cases.paginator import UsersPaginator
from app.modules.users.application.use_cases.read import UsersReader
from app.modules.users.application.use_cases.update import UsersUpdater

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("/me", response_model=UserRead)
async def get_me(
    actor: UserActorDep,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Retorna os dados do usuário autenticado."""

    reader = UsersReader(uow=uow)
    user = await reader.get_by_id(actor.user_id)
    return UserRead(**user.to_dict())


@router.patch("/me", response_model=UserRead)
async def update_me(
    actor: UserActorDep,
    user_update: UserUpdate,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Atualiza os dados do usuário autenticado."""

    updater = UsersUpdater(uow=uow)
    user = await updater.update(
        id_=actor.user_id,
        data=UpdateUserCommand(**user_update.model_dump(exclude_unset=True)),
    )
    return UserRead(**user.to_dict())


@router.get("")
async def paginate_users(
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: UsersUnitOfWorkDep,
) -> PaginatedResponse[UserRead]:
    """Lista os usuários do sistema, com suporte a filtros e paginação."""

    paginator = UsersPaginator(uow=uow)
    users = await paginator.paginate(
        page_params=page_params,
        filters=filters,
    )
    return build_paginated_response(
        items=[UserRead.model_validate(user.to_dict()) for user in users.items],
        total=users.total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Retorna os dados de um usuário específico."""

    use_case = UsersReader(uow=uow)
    user = await use_case.get_by_id(user_id)
    return UserRead(**user.to_dict())


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Cria um novo usuário. Restrito a establishment_admin e global_admin."""

    creator = UsersCreator(uow=uow)
    user = await creator.create(
        data=CreateUserCommand(**data.model_dump(exclude_unset=True))
    )
    return UserRead.model_validate(user.to_dict())


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """
    Atualiza os dados de um usuário específico. Restrito a establishment_admin e
    global_admin.
    """

    updater = UsersUpdater(uow=uow)
    user = await updater.update(
        id_=user_id,
        data=UpdateUserCommand(**data.model_dump(exclude_unset=True)),
    )
    return UserRead(**user.to_dict())


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    uow: UsersUnitOfWorkDep,
) -> None:
    """Deleta um usuário específico. Restrito a establishment_admin e global_admin."""

    use_case = UsersDeleter(uow=uow)
    await use_case.delete(user_id)


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    actor: UserActorDep,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Ativa um usuário específico. Restrito a establishment_admin e global_admin."""

    activator = UsersActivator(uow=uow)
    user = await activator.activate(user_id, actor)
    return UserRead(**user.to_dict())


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    actor: UserActorDep,
    uow: UsersUnitOfWorkDep,
) -> UserRead:
    """Desativa um usuário específico. Restrito a establishment_admin e global_admin."""

    activator = UsersActivator(uow=uow)
    user = await activator.deactivate(user_id, actor)
    return UserRead(**user.to_dict())
