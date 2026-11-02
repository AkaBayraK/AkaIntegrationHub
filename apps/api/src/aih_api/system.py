from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, Request
from pydantic import BaseModel

PRODUCT = "Aka Integration Hub"

router = APIRouter(prefix="/v1/system", tags=["system"])


class SystemInfo(BaseModel):
    product: str
    version: str
    environment: str


def _version() -> str:
    try:
        return version("aih-api")
    except PackageNotFoundError:
        return "dev"


@router.get("/info", response_model=SystemInfo)
async def info(request: Request) -> SystemInfo:
    return SystemInfo(product=PRODUCT, version=_version(), environment=request.app.state.settings.environment)
