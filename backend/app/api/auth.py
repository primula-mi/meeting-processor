"""OAuth endpoints.

Two auth providers are supported:

- **Yandex** (primary, visible in UI) — with corporate email domain allowlist.
- **Bitrix24** (kept functional but hidden in UI) — enable by showing the button
  in the frontend once a paid Bitrix24 plan is available.

Flow (both providers):
1. Frontend calls `GET /auth/{provider}/login` and gets an authorize URL.
2. Browser redirects to the provider, user grants access.
3. Provider redirects to `/auth/{provider}/callback?code=...` on the backend.
4. Backend exchanges the code for a provider access token, fetches the profile,
   validates domain (Yandex only), creates/updates the user, issues a JWT and
   redirects the browser to `{FRONTEND_URL}/login?access_token={jwt}`.
5. The frontend LoginPage reads `access_token` from the query string and stores it.
"""
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import DEFAULT_SYSTEM_PROMPT, User
from app.schemas.auth import AuthURL

router = APIRouter(prefix="/auth", tags=["auth"])

YANDEX_AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_INFO_URL = "https://login.yandex.ru/info"


def _frontend_redirect(access_token: str | None = None, error: str | None = None) -> RedirectResponse:
    """Redirect the browser back to the frontend login page with a token or error."""
    base = f"{settings.FRONTEND_URL}/login"
    if access_token:
        return RedirectResponse(url=f"{base}?access_token={quote(access_token)}")
    return RedirectResponse(url=f"{base}?error={quote(error or 'unknown')}")


def _issue_jwt_for_user(user: User) -> str:
    return create_access_token(data={"sub": str(user.id)})


def _email_domain_allowed(email: str) -> bool:
    """Return True if the email's domain is in the allowlist (or the allowlist is empty)."""
    allowed = settings.allowed_domains_list
    if not allowed:
        return True
    if "@" not in email:
        return False
    return email.rsplit("@", 1)[1].lower() in allowed


# ---------------------------------------------------------------------------
# Yandex OAuth
# ---------------------------------------------------------------------------


@router.get("/yandex/login", response_model=AuthURL)
def yandex_login():
    """Return Yandex OAuth authorization URL."""
    params = urlencode({
        "response_type": "code",
        "client_id": settings.YANDEX_CLIENT_ID,
        "redirect_uri": settings.YANDEX_REDIRECT_URI,
    })
    return AuthURL(url=f"{YANDEX_AUTHORIZE_URL}?{params}")


@router.get("/yandex/callback")
async def yandex_callback(code: str, db: Session = Depends(get_db)):
    """Handle Yandex OAuth callback: validate domain, upsert user, issue JWT."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            YANDEX_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_CLIENT_ID,
                "client_secret": settings.YANDEX_CLIENT_SECRET,
            },
        )

    if token_resp.status_code != 200:
        return _frontend_redirect(error="Не удалось получить токен от Яндекса")

    yandex_access_token = token_resp.json().get("access_token")
    if not yandex_access_token:
        return _frontend_redirect(error="Неверный ответ Яндекс OAuth")

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            YANDEX_INFO_URL,
            headers={"Authorization": f"OAuth {yandex_access_token}"},
            params={"format": "json"},
        )

    if profile_resp.status_code != 200:
        return _frontend_redirect(error="Не удалось получить профиль пользователя")

    profile = profile_resp.json()
    yandex_id = str(profile.get("id", ""))
    email = profile.get("default_email") or ""
    name = (
        profile.get("real_name")
        or profile.get("display_name")
        or profile.get("login")
        or ""
    )

    if not yandex_id or not email:
        return _frontend_redirect(error="Яндекс не вернул идентификатор или email пользователя")

    if not _email_domain_allowed(email):
        allowed_list = ", ".join(settings.allowed_domains_list)
        return _frontend_redirect(
            error=(
                "Доступ разрешён только сотрудникам компании. "
                f"Разрешённые домены: {allowed_list}"
            )
        )

    user = db.query(User).filter(User.yandex_id == yandex_id).first()
    if user is None:
        user = User(
            yandex_id=yandex_id,
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

    return _frontend_redirect(access_token=_issue_jwt_for_user(user))


# ---------------------------------------------------------------------------
# Bitrix24 OAuth (disabled in UI — backend is kept functional for future use)
# ---------------------------------------------------------------------------


@router.get("/bitrix24/login", response_model=AuthURL)
def bitrix24_login():
    """Return Bitrix24 OAuth authorization URL."""
    if not settings.BITRIX24_DOMAIN or not settings.BITRIX24_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Авторизация через Bitrix24 не настроена",
        )
    params = urlencode({
        "client_id": settings.BITRIX24_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.BITRIX24_REDIRECT_URI,
    })
    url = f"https://{settings.BITRIX24_DOMAIN}/oauth/authorize/?{params}"
    return AuthURL(url=url)


@router.get("/bitrix24/callback")
async def bitrix24_callback(code: str, db: Session = Depends(get_db)):
    """Handle Bitrix24 OAuth callback: upsert user, issue JWT."""
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
        return _frontend_redirect(error="Не удалось получить токен от Bitrix24")

    b24_access_token = token_resp.json().get("access_token")
    if not b24_access_token:
        return _frontend_redirect(error="Неверный ответ Bitrix24 OAuth")

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"https://{settings.BITRIX24_DOMAIN}/rest/user.current.json",
            params={"auth": b24_access_token},
        )

    if profile_resp.status_code != 200:
        return _frontend_redirect(error="Не удалось получить профиль пользователя")

    profile = profile_resp.json().get("result", {})
    bitrix24_id = str(profile.get("ID", ""))
    email = profile.get("EMAIL", "") or ""
    name = f"{profile.get('NAME', '')} {profile.get('LAST_NAME', '')}".strip()

    if not bitrix24_id:
        return _frontend_redirect(error="Bitrix24 не вернул идентификатор пользователя")

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

    return _frontend_redirect(access_token=_issue_jwt_for_user(user))
