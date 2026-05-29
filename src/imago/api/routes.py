from fastapi import APIRouter

from imago import __version__

router = APIRouter(prefix="/api/v1", tags=["imago"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}
