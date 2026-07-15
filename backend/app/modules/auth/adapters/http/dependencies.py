from typing import Annotated

from fastapi import Depends

from app.modules.auth.adapters.db.factories import make_unit_of_work
from app.modules.auth.adapters.db.unit_of_work import AuthUnitOfWork

AuthUnitOfWorkDep = Annotated[AuthUnitOfWork, Depends(make_unit_of_work)]
