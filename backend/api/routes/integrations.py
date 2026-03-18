"""
Google OAuth 2.0 entegrasyon route'ları.

Akış:
  1. GET  /google/connect   → HMAC-imzalı state üret, Google yetkilendirme URL'i dön
  2. GET  /ga4/callback     → code → token değişimi, DB'ye kaydet, frontend'e yönlendir
  3. GET  /google/tokens    → arka plan ajanı için geçerli token sağla (refresh varsa yeniler)
  4. GET  /                 → entegrasyon listesi
  5. GET  /status           → platform bağlantı durumu
  6. POST /ga4/property     → GA4 property ID kaydet
  7. DELETE /ga4            → GA4 bağlantısını kopar
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from db.database import get_db
from db.models import User, Integration
from core.auth import get_current_user
from core.config import settings
from core.google_oauth import (
    create_flow,
    generate_state,
    verify_state,
    credentials_to_dict,
    credentials_from_dict,
    refresh_credentials_if_expired,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Frontend 4000 portunda (Docker: 4000:3000), backend 3000 portunda (Docker: 3000:8080)
FRONTEND_URL = "http://localhost:4000"


# ─── Pydantic Şemaları ───────────────────────────────────────────

class IntegrationResponse(BaseModel):
    id: str
    platform: str
    status: str
    property_id: Optional[str] = None
    last_sync: Optional[str] = None

    class Config:
        from_attributes = True


class IntegrationStatusResponse(BaseModel):
    ga4: bool = False
    google_ads: bool = False
    meta: bool = False
    shopify: bool = False
    ticimax: bool = False


class PropertyRequest(BaseModel):
    property_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    scopes: list[str]
    refreshed: bool  # token bu istek sırasında yenilendi mi?


# ─── 1. Google OAuth — Yetkilendirme URL'i ──────────────────────

@router.get("/google/connect")
async def google_connect(
    current_user: User = Depends(get_current_user),
):
    """
    Kullanıcıyı Google OAuth 2.0 ekranına yönlendirecek URL'i döndürür.

    Frontend bu URL'e yönlendirmelidir (window.location.href = url).
    State parametresi HMAC ile imzalanmıştır — CSRF saldırılarına karşı güvenlidir.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth henüz yapılandırılmadı")

    flow = create_flow()
    state = generate_state(str(current_user.id))

    auth_url, _ = flow.authorization_url(
        # Kalıcı refresh_token için ZORUNLU
        access_type="offline",
        # Her girişte consent ekranı göster → refresh_token'ın kesinlikle dönmesini sağlar
        prompt="consent",
        state=state,
        # Kullanıcı iptal ederse "error=access_denied" parametresiyle callback'e döner
        include_granted_scopes="true",
    )

    logger.info("OAuth URL üretildi: user_id=%s", current_user.id)
    return {"url": auth_url}


# ─── 2. Google OAuth — Callback (Token Değişimi) ────────────────

@router.get("/ga4/callback")
async def ga4_callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Google'ın yetkilendirme kodunu token'lara çevirir ve veritabanına kaydeder.

    Güvenlik kontrolleri:
      - Kullanıcı iptalini (error parametresi) yakalar
      - State'i HMAC ile doğrular (CSRF koruması)
      - State'in 15 dakika içinde üretildiğini kontrol eder
    """
    # Kullanıcı "İzin verme" dediyse
    if error:
        logger.warning("OAuth iptal: %s", error)
        return RedirectResponse(url=f"{FRONTEND_URL}/integrations?error=cancelled")

    # Zorunlu parametreler
    if not code or not state:
        return RedirectResponse(url=f"{FRONTEND_URL}/integrations?error=missing_params")

    if not settings.GOOGLE_CLIENT_ID:
        return RedirectResponse(url=f"{FRONTEND_URL}/integrations?error=config")

    # ── HMAC State Doğrulaması ──────────────────────────────────
    user_id = verify_state(state)
    if not user_id:
        logger.warning("Geçersiz OAuth state — olası CSRF girişimi")
        return RedirectResponse(url=f"{FRONTEND_URL}/integrations?error=invalid_state")

    # ── Code → Token Değişimi ──────────────────────────────────
    try:
        flow = create_flow()
        # fetch_token senkron HTTP çağrısı yapar (google-auth-oauthlib zorunluluğu)
        # Bu işlemi thread pool'a taşıyarak event loop'u bloklamıyoruz
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: flow.fetch_token(code=code),
        )
        creds = flow.credentials
    except Exception as e:
        logger.error("Token değişimi başarısız: %s", e)
        return RedirectResponse(url=f"{FRONTEND_URL}/integrations?error=token_exchange")

    # refresh_token boşsa kullanıcı daha önce yetki vermiş demektir.
    # prompt="consent" ile her seferinde alınmalı — yine de loglayalım.
    if not creds.refresh_token:
        logger.warning(
            "refresh_token alınamadı (user_id=%s) — "
            "kullanıcı önceden yetki vermiş olabilir",
            user_id,
        )

    # ── Token'ları Veritabanına Kaydet ─────────────────────────
    # Hem GA4 hem Google Ads aynı Google hesabından geldiği için
    # tek bir "google" kaydı yeterlidir. İstersen platform="ga4" ve
    # platform="google_ads" olarak ikiye bölebilirsin.
    creds_dict = credentials_to_dict(creds)

    result = await db.execute(
        select(Integration).where(
            Integration.user_id == user_id,
            Integration.platform == "ga4",
        )
    )
    integration = result.scalar_one_or_none()

    if integration:
        integration.credentials = creds_dict
        integration.status = "active"
        logger.info("Mevcut GA4 entegrasyonu güncellendi: user_id=%s", user_id)
    else:
        integration = Integration(
            user_id=user_id,
            platform="ga4",
            credentials=creds_dict,
            status="active",
            metadata_={},
        )
        db.add(integration)
        logger.info("Yeni GA4 entegrasyonu oluşturuldu: user_id=%s", user_id)

    # Aynı token Google Ads için de geçerli — adwords scope zaten istendi
    ads_result = await db.execute(
        select(Integration).where(
            Integration.user_id == user_id,
            Integration.platform == "google_ads",
        )
    )
    ads_integration = ads_result.scalar_one_or_none()
    if ads_integration:
        ads_integration.credentials = creds_dict
        ads_integration.status = "active"
    else:
        db.add(Integration(
            user_id=user_id,
            platform="google_ads",
            credentials=creds_dict,
            status="active",
            metadata_={},
        ))
    logger.info("Google Ads entegrasyonu da kaydedildi: user_id=%s", user_id)

    await db.flush()
    return RedirectResponse(url=f"{FRONTEND_URL}/integrations?ga4=connected")


# ─── 3. Ajan İçin Token Endpoint'i ─────────────────────────────

@router.get("/google/tokens", response_model=TokenResponse)
async def get_google_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Arka plan ajanı (data_agent, operator_agent) için geçerli bir
    access_token döndürür. Token süresi dolmuşsa refresh_token ile
    otomatik yeniler ve veritabanını günceller.

    Kullanım (agent'tan HTTP isteği):
        headers = {"Authorization": f"Bearer {user_jwt}"}
        resp = httpx.get("/api/v1/integrations/google/tokens", headers=headers)
        access_token = resp.json()["access_token"]
    """
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == "ga4",
            Integration.status == "active",
        )
    )
    integration = result.scalar_one_or_none()

    if not integration or not integration.credentials:
        raise HTTPException(
            status_code=404,
            detail="Google entegrasyonu bulunamadı. Önce /google/connect ile bağlayın.",
        )

    creds = credentials_from_dict(integration.credentials)

    # Süresi dolmuşsa yenile
    import asyncio
    loop = asyncio.get_event_loop()
    creds, was_refreshed = await loop.run_in_executor(
        None,
        lambda: refresh_credentials_if_expired(creds),
    )

    # Yenilendiyse DB'yi güncelle
    if was_refreshed:
        integration.credentials = credentials_to_dict(creds)
        await db.flush()
        logger.info("Token yenilendi ve DB güncellendi: user_id=%s", current_user.id)

    if not creds.token:
        raise HTTPException(
            status_code=401,
            detail="Google token alınamadı. Lütfen yeniden bağlanın.",
        )

    return TokenResponse(
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        scopes=list(creds.scopes) if creds.scopes else [],
        refreshed=was_refreshed,
    )


# ─── 4. Entegrasyon Listesi ──────────────────────────────────────

@router.get("/", response_model=list[IntegrationResponse])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(Integration.user_id == current_user.id)
    )
    integrations = result.scalars().all()
    return [
        IntegrationResponse(
            id=str(i.id),
            platform=i.platform,
            status=i.status,
            property_id=i.metadata_.get("property_id") if i.metadata_ else None,
            last_sync=i.last_sync.isoformat() if i.last_sync else None,
        )
        for i in integrations
    ]


# ─── 5. Platform Durum Özeti ─────────────────────────────────────

@router.get("/status", response_model=IntegrationStatusResponse)
async def integration_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.status == "active",
        )
    )
    platforms = {i.platform for i in result.scalars().all()}
    return IntegrationStatusResponse(
        ga4="ga4" in platforms,
        google_ads="google_ads" in platforms,
        meta="meta" in platforms,
        shopify="shopify" in platforms,
        ticimax="ticimax" in platforms,
    )


# ─── 6. GA4 Property ID Kaydet ──────────────────────────────────

@router.post("/ga4/property")
async def save_ga4_property(
    payload: PropertyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == "ga4",
            Integration.status == "active",
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Önce GA4 hesabını bağlayın")

    integration.metadata_ = {**(integration.metadata_ or {}), "property_id": payload.property_id}
    await db.flush()
    return {"message": "Property ID kaydedildi", "property_id": payload.property_id}


# ─── 7. GA4 Bağlantısını Kopar ──────────────────────────────────

@router.post("/google_ads/customer")
async def save_ads_customer(
    payload: PropertyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == "google_ads",
            Integration.status == "active",
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Önce Google Ads hesabını bağlayın")
    integration.metadata_ = {**(integration.metadata_ or {}), "customer_id": payload.property_id}
    await db.flush()
    return {"message": "Customer ID kaydedildi", "customer_id": payload.property_id}


@router.delete("/google_ads")
async def disconnect_google_ads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == "google_ads",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        integration.status = "inactive"
        integration.credentials = {}
        await db.flush()
    return {"message": "Google Ads bağlantısı kesildi"}


@router.delete("/ga4")
async def disconnect_ga4(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == "ga4",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        integration.status = "inactive"
        integration.credentials = {}
        await db.flush()
    return {"message": "GA4 bağlantısı kesildi"}
