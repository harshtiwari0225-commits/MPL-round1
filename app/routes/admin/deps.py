"""Shared admin dependency: the admin-passcode header check."""
from fastapi import HTTPException, Header

from app.core.config import settings


def verify_admin(admin_passcode: str = Header(...)):
    if admin_passcode != settings.ADMIN_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized")
