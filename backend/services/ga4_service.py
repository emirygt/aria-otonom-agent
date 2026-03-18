"""
GA4 Service — Sprint 2
Gerçek Google Analytics Data API v1beta çağrıları.

Kullanım:
    creds = await load_ga4_credentials(user_id, db)
    data  = await fetch_7day_metrics(property_id, creds)
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.google_oauth import credentials_from_dict, refresh_credentials_if_expired
from db.models import Integration

logger = logging.getLogger(__name__)


# ─── Özel Hatalar ────────────────────────────────────────────────

class GA4AuthRevokedError(Exception):
    """Kullanıcı Google iznini iptal etti — yeniden bağlanması gerekiyor."""

class GA4QuotaExceededError(Exception):
    """Google Analytics API günlük kotası doldu."""

class GA4PropertyNotFoundError(Exception):
    """Verilen property_id bu hesapta bulunamadı."""


# ─── DB'den Credentials Yükle ────────────────────────────────────

async def load_ga4_credentials(user_id: UUID, db: AsyncSession):
    """
    Veritabanındaki ga4 Integration kaydından Credentials nesnesi döndürür.
    Token süresi dolmuşsa otomatik yeniler ve DB'yi günceller.

    Returns:
        google.oauth2.credentials.Credentials

    Raises:
        ValueError: GA4 entegrasyonu bulunamazsa
        GA4AuthRevokedError: Refresh token geçersizse
    """
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == user_id,
            Integration.platform == "ga4",
            Integration.status == "active",
        )
    )
    integration = result.scalar_one_or_none()

    if not integration or not integration.credentials:
        raise ValueError("Aktif GA4 entegrasyonu bulunamadı. Lütfen önce GA4 hesabınızı bağlayın.")

    try:
        creds = credentials_from_dict(integration.credentials)
    except Exception as e:
        raise ValueError(f"Credentials oluşturulamadı: {e}") from e

    # Süresi dolmuşsa yenile
    try:
        creds, refreshed = refresh_credentials_if_expired(creds)
    except Exception as e:
        err_str = str(e).lower()
        if "revoked" in err_str or "invalid_grant" in err_str:
            # DB'de entegrasyonu devre dışı bırak
            integration.status = "revoked"
            await db.commit()
            raise GA4AuthRevokedError(
                "Google yetkilendirmesi iptal edilmiş. Lütfen GA4 entegrasyonunu yenileyin."
            ) from e
        raise

    # Token yenilendiyse DB'yi güncelle
    if refreshed:
        from core.google_oauth import credentials_to_dict
        integration.credentials = credentials_to_dict(creds)
        integration.last_sync = datetime.utcnow()
        await db.commit()
        logger.info("GA4 token yenilendi ve DB güncellendi | user_id=%s", user_id)

    return creds


# ─── 7 Günlük Temel Metrikler ────────────────────────────────────

async def fetch_7day_metrics(property_id: str, creds) -> dict:
    """
    Son 7 günün temel GA4 metriklerini çeker.

    Döndürür:
    {
        "active_users": int,
        "sessions": int,
        "conversions": int,
        "event_count": int,
        "bounce_rate": float,
        "avg_session_duration_sec": float,
        "period_days": 7,
        "data_source": "ga4",
        "fetched_at": "ISO8601"
    }
    """
    def _sync_call():
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric
        )
        from google.api_core.exceptions import (
            PermissionDenied, ResourceExhausted, NotFound
        )

        client = BetaAnalyticsDataClient(credentials=creds)
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="eventCount"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        )

        try:
            return client.run_report(request)
        except PermissionDenied as e:
            raise GA4AuthRevokedError(str(e)) from e
        except ResourceExhausted as e:
            raise GA4QuotaExceededError(str(e)) from e
        except NotFound as e:
            raise GA4PropertyNotFoundError(
                f"Property ID '{property_id}' bulunamadı. Google Analytics'te doğru mülkü seçtiğinizden emin olun."
            ) from e

    resp = await asyncio.to_thread(_sync_call)

    active_users = sessions = conversions = event_count = 0
    bounce_rate = avg_duration = 0.0

    if resp.rows:
        vals = resp.rows[0].metric_values
        active_users  = int(float(vals[0].value or 0))
        sessions      = int(float(vals[1].value or 0))
        conversions   = int(float(vals[2].value or 0))
        event_count   = int(float(vals[3].value or 0))
        bounce_rate   = round(float(vals[4].value or 0), 4)
        avg_duration  = round(float(vals[5].value or 0), 1)

    return {
        "active_users": active_users,
        "sessions": sessions,
        "conversions": conversions,
        "event_count": event_count,
        "bounce_rate": bounce_rate,
        "avg_session_duration_sec": avg_duration,
        "period_days": 7,
        "data_source": "ga4",
        "fetched_at": datetime.utcnow().isoformat(),
    }


# ─── Günlük Seri (Insight Agent için trend analizi) ──────────────

async def fetch_daily_series(property_id: str, creds, days: int = 7) -> list[dict]:
    """
    Her gün için ayrı satır döndürür — Insight Agent trend hesaplarken kullanır.

    Döndürür:
    [
        {"date": "2025-03-11", "active_users": 1240, "sessions": 1580, "conversions": 42},
        ...
    ]
    """
    def _sync_call():
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric, Dimension, OrderBy
        )
        from google.api_core.exceptions import PermissionDenied, ResourceExhausted

        client = BetaAnalyticsDataClient(credentials=creds)
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="conversions"),
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
        )

        try:
            return client.run_report(request)
        except PermissionDenied as e:
            raise GA4AuthRevokedError(str(e)) from e
        except ResourceExhausted as e:
            raise GA4QuotaExceededError(str(e)) from e

    resp = await asyncio.to_thread(_sync_call)

    rows = []
    for row in resp.rows:
        raw_date = row.dimension_values[0].value  # "20250311"
        dt = datetime.strptime(raw_date, "%Y%m%d")
        vals = row.metric_values
        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "active_users": int(float(vals[0].value or 0)),
            "sessions": int(float(vals[1].value or 0)),
            "conversions": int(float(vals[2].value or 0)),
        })

    return rows
