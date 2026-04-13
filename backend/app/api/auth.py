from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User, DEFAULT_SYSTEM_PROMPT
from app.schemas.auth import AuthURL, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_model=AuthURL)
def get_login_url():
    """Return Bitrix24 OAuth authorization URL."""
    params = urlencode({
        "client_id": settings.BITRIX24_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.BITRIX24_REDIRECT_URI,
    })
    url = f"https://{settings.BITRIX24_DOMAIN}/oauth/authorize/?{params}"
    return AuthURL(url=url)


@router.get("/callback", response_model=TokenResponse)
async def auth_callback(code: str, db: Session = Depends(get_db)):
    """Handle Bitrix24 OAuth callback, create/update user, return JWT."""
    # Exchange code for token
    token_url = f"https://{settings.BITRIX24_DOMAIN}/oauth/token/"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data={
            "grant_type": "authorization_code",
            "client_id": settings.BITRIX24_CLIENT_ID,
            "client_secret": settings.BITRIX24_CLIENT_SECRET,
            "redirect_uri": settings.BITRIX24_REDIRECT_URI,
            "code": code,
        })

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось получить токен от Bitrix24",
        )

    token_data = token_resp.json()
    b24_access_token = token_data["access_token"]

    # Fetch user profile from Bitrix24
    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"https://{settings.BITRIX24_DOMAIN}/rest/user.current.json",
            params={"auth": b24_access_token},
        )

    if profile_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось получить профиль пользователя",
        )

    profile = profile_resp.json().get("result", {})
    bitrix24_id = str(profile.get("ID", ""))
    email = profile.get("EMAIL", "")
    name = f"{profile.get('NAME', '')} {profile.get('LAST_NAME', '')}".strip()

    # Find or create user
    user = db.query(User).filter(User.bitrix24_id == bitrix24_id).first()
    if user is None:
        user = User(
            bitrix24_id=bitrix24_id,
            email=email,
            name=name,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = email
        user.name = name
        db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)
