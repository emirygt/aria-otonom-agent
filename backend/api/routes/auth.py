from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import httpx
import urllib.parse

from db.database import get_db
from db.models import User
from core.auth import hash_password, verify_password, create_access_token, get_current_user
from core.config import settings
from core.google_oauth import generate_state, verify_state

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    plan: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı",
        )

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        plan=current_user.plan,
        is_active=current_user.is_active,
    )


_GOOGLE_AUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@router.get("/google/connect")
async def google_connect():
    """Tarayıcıyı Google OAuth sayfasına yönlendirir."""
    state = generate_state("login")
    params = urllib.parse.urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_AUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(_GOOGLE_AUTH_SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Google'dan dönen code'u JWT'ye çevirir, frontend'e yönlendirir."""
    if not verify_state(state):
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=invalid_state")

    # Code → access_token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_AUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_resp.status_code != 200:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=token_exchange_failed")

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=no_access_token")

    # Kullanıcı bilgilerini al
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=userinfo_failed")

    google_user = userinfo_resp.json()
    email = google_user.get("email")
    name = google_user.get("name", email)

    if not email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=no_email")

    # Kullanıcıyı bul veya oluştur
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            hashed_password=hash_password(email + "_google_oauth"),
            full_name=name,
        )
        db.add(user)
        await db.flush()

    token = create_access_token({"sub": user.email})
    return RedirectResponse(f"{settings.FRONTEND_URL}/login?token={token}")


class GoogleTokenRequest(BaseModel):
    access_token: str  # NextAuth'tan gelen Google access_token


@router.post("/google", response_model=TokenResponse)
async def login_with_google(payload: GoogleTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    NextAuth Google access_token'ını kabul eder, Google'dan kullanıcı bilgilerini çeker,
    DB'de kullanıcıyı oluşturur/bulur ve backend JWT döndürür.

    Frontend köprüsü bu endpoint'i çağırarak localStorage'a kaydetmesi
    gereken aria_token'ı alır.
    """
    # Google'dan kullanıcı bilgilerini al
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {payload.access_token}"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Geçersiz Google token")

    google_user = resp.json()
    email = google_user.get("email")
    name = google_user.get("name", email)

    if not email:
        raise HTTPException(status_code=400, detail="Google hesabından email alınamadı")

    # Kullanıcıyı bul veya oluştur
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            hashed_password=hash_password(email + "_google_oauth"),  # şifresiz kayıt
            full_name=name,
        )
        db.add(user)
        await db.flush()

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
