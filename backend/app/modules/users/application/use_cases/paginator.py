from app.core.pagination.params import Page, PageParams
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import User


class UsersPaginator:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um paginador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: UserFilters | None = None,
    ) -> Page[User]:
        """
        Pagina usuários com filtros opcionais.

        Args:
            page_params (PageParams):
                Parâmetros de paginação.
            filters (UsersFilters):
                Filtros a serem aplicados.
        """

        async with self._uow as uow:
            return await uow.users.paginate(
                page_params=page_params,
                filters=filters,
            )
