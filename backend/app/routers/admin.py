"""Admin-only management endpoints (seed data, maintenance)."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import get_current_active_user_or_demo
from ..core.database import get_db
from ..models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(current_user: User) -> User:
    if current_user.role not in (UserRole.ADMIN,):
        raise HTTPException(status_code=403, detail="Доступ только для администраторов")
    return current_user


@router.post("/seed")
async def run_seed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """
    Load initial (seed) data for the current organisation.

    The script is idempotent — safe to call multiple times.
    Only accessible to admins.
    """
    _require_admin(current_user)

    try:
        from ..seeds.seed_vksit import seed as _seed, ORG_ID
        # Temporarily patch ORG_ID for the current org
        import app.seeds.seed_vksit as _seed_module
        original_org_id = _seed_module.ORG_ID
        _seed_module.ORG_ID = current_user.org_id
        try:
            await _seed(db)
        finally:
            _seed_module.ORG_ID = original_org_id
        return {"ok": True, "detail": "Тестовые данные успешно загружены"}
    except Exception as exc:
        logger.exception("Seed failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {exc}")
