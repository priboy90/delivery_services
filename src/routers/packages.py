from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.core.database import get_db
from src.models.models import Packages
from src.models.schemas import PackageCreate, PackageResponse
from src.services.package_service import create_package

router = APIRouter(prefix="/api/packages", tags=["packages"])


@router.post("/", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def register_package(
        package_data: PackageCreate,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Регистрация новой посылки
    """
    try:
        created_package = await create_package(db, package_data)
        return created_package
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
