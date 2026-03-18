"""
Google OAuth 2.0 yardımcı modülü.

Sorumluluklar:
  - google-auth-oauthlib Flow oluşturma
  - HMAC-imzalı state üretme / doğrulama (CSRF koruması)
  - Credential'ları veritabanına uygun formata dönüştürme
  - Süresi dolmuş token'ları refresh etme
"""

import hmac
import hashlib
import secrets
import time
import json
import logging
from typing import Optional

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from core.config import settings

logger = logging.getLogger(__name__)

# ─── Scope'lar ───────────────────────────────────────────────────

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    # GA4 — salt okunur
    "https://www.googleapis.com/auth/analytics.readonly",
    # Google Ads — kampanya yönetimi
    "https://www.googleapis.com/auth/adwords",
]

# ─── Flow Factory ────────────────────────────────────────────────

def create_flow() -> Flow:
    """
    google-auth-oauthlib Flow nesnesi döndürür.
    redirect_uri .env dosyasındaki sabit değerden gelir.
    """
    # ── Diagnostic: boş değer varsa hemen hata ver ──────────────
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError(
            "GOOGLE_CLIENT_ID boş! .env dosyasını ve Docker env_file ayarını kontrol et."
        )
    if not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_CLIENT_SECRET boş! .env dosyasını ve Docker env_file ayarını kontrol et."
        )

    logger.info(
        "OAuth flow oluşturuluyor | client_id=%s...%s | redirect_uri=%s",
        settings.GOOGLE_CLIENT_ID[:12],   # ilk 12 karakter (güvenli)
        settings.GOOGLE_CLIENT_ID[-8:],   # son 8 karakter
        settings.GOOGLE_REDIRECT_URI,
    )

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


# ─── HMAC State — CSRF Koruması ─────────────────────────────────

_STATE_TTL_SECONDS = 900  # 15 dakika


def generate_state(user_id: str) -> str:
    """
    State parametresi oluştur: '{user_id}:{timestamp}:{nonce}:{hmac}'

    - timestamp: geçerlilik süresi kontrolü için
    - nonce: aynı saniye içinde üretilen state'leri birbirinden ayırır
    - hmac: imza, state'in değiştirilmediğini kanıtlar
    """
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(8)
    payload = f"{user_id}:{timestamp}:{nonce}"
    signature = _sign(payload)
    return f"{payload}:{signature}"


def verify_state(state: str) -> Optional[str]:
    """
    State'i doğrular ve user_id döndürür.
    Geçersiz, süresi dolmuş veya manipüle edilmişse None döner.
    """
    parts = state.split(":")
    if len(parts) != 4:
        logger.warning("Geçersiz state formatı")
        return None

    user_id, timestamp, nonce, received_sig = parts
    payload = f"{user_id}:{timestamp}:{nonce}"

    # HMAC imzasını sabit-zamanlı karşılaştırma ile doğrula (timing attack'a karşı)
    expected_sig = _sign(payload)
    if not hmac.compare_digest(expected_sig, received_sig):
        logger.warning("State HMAC doğrulaması başarısız")
        return None

    # Zaman aşımı kontrolü
    try:
        issued_at = int(timestamp)
    except ValueError:
        return None

    if time.time() - issued_at > _STATE_TTL_SECONDS:
        logger.warning("State süresi dolmuş (>15 dakika)")
        return None

    return user_id


def _sign(payload: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


# ─── Credential Dönüştürme ───────────────────────────────────────

def credentials_to_dict(creds: Credentials) -> dict:
    """
    google.oauth2.credentials.Credentials nesnesini
    veritabanındaki JSON sütununa kaydedilecek dict'e çevirir.

    Google'ın kendi to_json() formatını kullanır — ilerleyen aşamada
    from_dict() ile geri yüklenebilir.
    """
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else GOOGLE_SCOPES,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def credentials_from_dict(data: dict) -> Credentials:
    """
    Veritabanından okunan dict'i Credentials nesnesine çevirir.
    data_agent ve operator_agent bu fonksiyonu kullanır.
    """
    from datetime import datetime

    expiry = None
    if data.get("expiry"):
        try:
            expiry = datetime.fromisoformat(data["expiry"])
        except (ValueError, TypeError):
            pass

    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id", settings.GOOGLE_CLIENT_ID),
        client_secret=data.get("client_secret", settings.GOOGLE_CLIENT_SECRET),
        scopes=data.get("scopes", GOOGLE_SCOPES),
        expiry=expiry,
    )


# ─── Token Yenileme (Ajan kullanımı için) ────────────────────────

def refresh_credentials_if_expired(creds: Credentials) -> tuple[Credentials, bool]:
    """
    Token süresi dolmuşsa veya dolmak üzereyse yeniler.

    Döndürür: (güncel_creds, yenilendi_mi)
    Hata durumunda orijinal creds + False döner.
    """
    if not creds.expired and creds.token:
        return creds, False

    try:
        creds.refresh(Request())
        logger.info("Google token başarıyla yenilendi")
        return creds, True
    except Exception as e:
        logger.error("Token yenileme hatası: %s", e)
        return creds, False
