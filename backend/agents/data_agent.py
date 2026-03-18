"""
Data Agent — GA4'ten gerçek veri çeker, bağlantı yoksa mock döndürür.

Sprint 2: get_ga4_sprint2() → ga4_service üzerinden gerçek veri.
"""
from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from core.config import settings

logger = logging.getLogger(__name__)


def _build_ga4_client(tokens: dict):
    """OAuth token'lardan GA4 istemcisi oluştur."""
    from google.oauth2.credentials import Credentials
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    creds = Credentials(
        token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    return BetaAnalyticsDataClient(credentials=creds)


class DataAgent:
    """GA4 API'den veri çeken agent. tokens verilirse gerçek, yoksa mock döner."""

    async def get_ga4_overview(
        self,
        user_id: str,
        days: int = 30,
        tokens: Optional[dict] = None,
        property_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if tokens and property_id and settings.GOOGLE_CLIENT_ID:
            try:
                return await self._real_ga4_overview(tokens, property_id, days)
            except Exception as e:
                print(f"GA4 API hatası (overview): {e}")

        return {
            "sessions": 48_230,
            "users": 38_642,
            "new_users": 32_481,
            "bounce_rate": 0.42,
            "avg_session_duration": 187,
            "conversion_rate": 0.028,
            "revenue_tl": 1_847_320.0,
            "period_days": days,
            "data_source": "mock",
        }

    async def _real_ga4_overview(self, tokens: dict, property_id: str, days: int) -> dict[str, Any]:
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric
        )

        client = _build_ga4_client(tokens)

        # Temel metrikler — e-ticaret kurulmamış hesaplarda da çalışır
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="newUsers"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        )
        resp = client.run_report(request)

        sessions = users = new_users = 0
        bounce_rate = avg_duration = 0.0

        if resp.rows:
            row = resp.rows[0].metric_values
            sessions = int(float(row[0].value or 0))
            users = int(float(row[1].value or 0))
            new_users = int(float(row[2].value or 0))
            bounce_rate = float(row[3].value or 0)
            avg_duration = float(row[4].value or 0)

        # Gelir/dönüşüm — e-ticaret varsa ayrıca dene
        revenue = 0.0
        conversion_rate = 0.0
        try:
            rev_req = RunReportRequest(
                property=f"properties/{property_id}",
                metrics=[Metric(name="totalRevenue"), Metric(name="conversions")],
                date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
            )
            rev_resp = client.run_report(rev_req)
            if rev_resp.rows:
                revenue = float(rev_resp.rows[0].metric_values[0].value or 0)
                conversions = int(float(rev_resp.rows[0].metric_values[1].value or 0))
                conversion_rate = conversions / sessions if sessions > 0 else 0
        except Exception:
            pass

        return {
            "sessions": sessions,
            "users": users,
            "new_users": new_users,
            "bounce_rate": round(bounce_rate, 4),
            "avg_session_duration": round(avg_duration),
            "conversion_rate": round(conversion_rate, 4),
            "revenue_tl": round(revenue, 2),
            "period_days": days,
            "data_source": "ga4",
        }

    async def get_ga4_trends(
        self,
        user_id: str,
        days: int = 14,
        tokens: Optional[dict] = None,
        property_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if tokens and property_id and settings.GOOGLE_CLIENT_ID:
            try:
                return await self._real_ga4_trends(tokens, property_id, days)
            except Exception as e:
                print(f"GA4 API hatası (trends): {e}")

        # Mock fallback
        import random
        from datetime import date
        random.seed(42)
        today = date.today()
        base_revenue = 58_000
        base_sessions = 1_550
        points = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            weekend_factor = 0.75 if d.weekday() >= 5 else 1.0
            noise_r = random.uniform(0.88, 1.14)
            noise_s = random.uniform(0.90, 1.12)
            trend_factor = 1 + (days - 1 - i) * 0.008
            points.append({
                "date": d.strftime("%d %b"),
                "revenue": round(base_revenue * weekend_factor * noise_r * trend_factor),
                "sessions": round(base_sessions * weekend_factor * noise_s * trend_factor),
                "data_source": "mock",
            })
        return points

    async def _real_ga4_trends(self, tokens: dict, property_id: str, days: int) -> list[dict[str, Any]]:
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric, Dimension, OrderBy
        )

        client = _build_ga4_client(tokens)
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalRevenue"),
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="yesterday")],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
        )
        resp = client.run_report(request)
        points = []
        for row in resp.rows:
            raw_date = row.dimension_values[0].value  # 20240315
            dt = datetime.strptime(raw_date, "%Y%m%d")
            points.append({
                "date": dt.strftime("%d %b"),
                "sessions": int(row.metric_values[0].value or 0),
                "revenue": round(float(row.metric_values[1].value or 0), 2),
                "data_source": "ga4",
            })
        return points

    async def get_funnel_data(self, user_id: str, tokens: Optional[dict] = None, property_id: Optional[str] = None) -> dict[str, Any]:
        return {
            "product_view": 48_230,
            "add_to_cart": 12_057,
            "checkout_start": 7_234,
            "checkout_complete": 4_485,
            "checkout_drop_rate": 0.38,
            "add_to_cart_rate": 0.25,
            "data_source": "mock",
        }

    async def get_device_breakdown(self, user_id: str, tokens: Optional[dict] = None, property_id: Optional[str] = None) -> dict[str, Any]:
        if tokens and property_id and settings.GOOGLE_CLIENT_ID:
            try:
                return await self._real_device_breakdown(tokens, property_id)
            except Exception as e:
                print(f"GA4 API hatası (device): {e}")

        return {
            "mobile": {"sessions": 29_819, "conversion_rate": 0.012, "revenue_tl": 428_400},
            "desktop": {"sessions": 15_434, "conversion_rate": 0.028, "revenue_tl": 1_247_900},
            "tablet": {"sessions": 2_977, "conversion_rate": 0.019, "revenue_tl": 171_020},
            "data_source": "mock",
        }

    async def _real_device_breakdown(self, tokens: dict, property_id: str) -> dict[str, Any]:
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric, Dimension
        )

        client = _build_ga4_client(tokens)
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="totalRevenue"),
            ],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        )
        resp = client.run_report(request)
        result = {}
        for row in resp.rows:
            device = row.dimension_values[0].value.lower()
            sessions = int(row.metric_values[0].value or 0)
            conversions = int(row.metric_values[1].value or 0)
            revenue = float(row.metric_values[2].value or 0)
            result[device] = {
                "sessions": sessions,
                "conversion_rate": round(conversions / sessions, 4) if sessions > 0 else 0,
                "revenue_tl": round(revenue, 2),
            }
        result["data_source"] = "ga4"
        return result

    async def get_traffic_sources(self, user_id: str, tokens: Optional[dict] = None, property_id: Optional[str] = None) -> dict[str, Any]:
        return {
            "organic_search": {"sessions": 6_752, "share": 0.14},
            "paid_search": {"sessions": 18_489, "share": 0.38},
            "paid_social": {"sessions": 12_538, "share": 0.26},
            "direct": {"sessions": 5_785, "share": 0.12},
            "referral": {"sessions": 4_666, "share": 0.10},
            "data_source": "mock",
        }

    async def get_campaigns(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {"name": "Yaz Koleksiyonu - Google", "spend_tl": 45_200, "revenue_tl": 198_400, "roas": 4.39, "status": "active", "trend": "up"},
            {"name": "Retargeting - Meta", "spend_tl": 18_700, "revenue_tl": 67_300, "roas": 3.60, "status": "active", "trend": "stable"},
            {"name": "Marka Bilinirlik - Google", "spend_tl": 12_400, "revenue_tl": 28_100, "roas": 2.27, "status": "active", "trend": "down"},
            {"name": "Dinamik Ürün - Meta", "spend_tl": 32_100, "revenue_tl": 154_080, "roas": 4.80, "status": "active", "trend": "up"},
            {"name": "Arama Ağı - Genel", "spend_tl": 8_900, "revenue_tl": 14_200, "roas": 1.60, "status": "paused", "trend": "down"},
        ]

    async def get_weekly_comparison(self, user_id: str) -> dict[str, Any]:
        return {
            "current_week": {"sessions": 11_200, "revenue_tl": 412_000},
            "previous_week": {"sessions": 8_700, "revenue_tl": 358_000},
            "change_sessions_pct": 28.7,
            "change_revenue_pct": 15.1,
            "data_source": "mock",
        }

    async def get_product_performance(self, user_id: str) -> dict[str, Any]:
        return {
            "top_by_revenue": [
                {"name": "Koton Yazlık Elbise", "revenue_tl": 284_600, "units": 1_423, "margin_pct": 0.28},
                {"name": "Nike Air Max 270", "revenue_tl": 198_400, "units": 496, "margin_pct": 0.41},
                {"name": "Mango Denim Ceket", "revenue_tl": 142_700, "units": 714, "margin_pct": 0.22},
            ],
            "top_by_margin": [
                {"name": "Aksesuar Seti Premium", "revenue_tl": 38_200, "units": 382, "margin_pct": 0.68},
                {"name": "Nike Air Max 270", "revenue_tl": 198_400, "units": 496, "margin_pct": 0.41},
                {"name": "Parfüm Koleksiyonu", "revenue_tl": 61_400, "units": 307, "margin_pct": 0.38},
            ],
            "data_source": "mock",
        }

    async def get_returning_users(self, user_id: str) -> dict[str, Any]:
        return {
            "total_users": 38_642,
            "new_users": 32_481,
            "returning_users": 6_161,
            "returning_pct": 0.159,
            "data_source": "mock",
        }

    async def get_budget_status(self, user_id: str) -> dict[str, Any]:
        from datetime import date
        today = date.today()
        days_elapsed = today.day
        days_remaining = 30 - days_elapsed
        return {
            "monthly_budget_tl": 150_000,
            "spent_tl": 117_300,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "daily_avg_spend_tl": 117_300 / days_elapsed if days_elapsed > 0 else 0,
            "projected_total_tl": (117_300 / days_elapsed * 30) if days_elapsed > 0 else 0,
            "data_source": "mock",
        }

    async def get_landing_pages(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {"page": "/yaz-koleksiyonu", "sessions": 8_420, "bounce_rate": 0.74, "avg_session_duration": 42},
            {"page": "/erkek-spor-ayakkabi", "sessions": 6_180, "bounce_rate": 0.58, "avg_session_duration": 98},
            {"page": "/kadin-elbise", "sessions": 5_910, "bounce_rate": 0.31, "avg_session_duration": 187},
            {"page": "/indirim", "sessions": 4_270, "bounce_rate": 0.71, "avg_session_duration": 55},
            {"page": "/yeni-gelenler", "sessions": 3_440, "bounce_rate": 0.45, "avg_session_duration": 134},
        ]

    # ── Sprint 2: Gerçek GA4 verisi (ga4_service üzerinden) ──────

    async def get_ga4_sprint2(
        self,
        user_id: str,
        property_id: str,
        db,
        include_daily: bool = False,
    ) -> dict[str, Any]:
        """
        Insight Agent için temiz GA4 özeti.

        Parametreler:
            user_id     — JWT'den gelen kullanıcı UUID (str)
            property_id — GA4 mülk ID (ör: "123456789")
            db          — AsyncSession (route'dan Depends ile gelir)
            include_daily — True ise günlük seri de eklenir

        Döndürür:
        {
            "summary": { active_users, sessions, conversions, ... },
            "daily":   [ { date, active_users, sessions, conversions }, ... ]  # include_daily=True ise
            "error":   None | "revoked" | "quota" | "property_not_found" | "unknown"
        }
        """
        from uuid import UUID as _UUID
        from services.ga4_service import (
            load_ga4_credentials,
            fetch_7day_metrics,
            fetch_daily_series,
            GA4AuthRevokedError,
            GA4QuotaExceededError,
            GA4PropertyNotFoundError,
        )

        try:
            creds = await load_ga4_credentials(_UUID(user_id), db)
            summary = await fetch_7day_metrics(property_id, creds)
            daily = await fetch_daily_series(property_id, creds, days=7) if include_daily else []
            return {"summary": summary, "daily": daily, "error": None}

        except GA4AuthRevokedError as e:
            logger.warning("GA4 yetki iptali | user_id=%s | %s", user_id, e)
            return {"summary": None, "daily": [], "error": "revoked"}
        except GA4QuotaExceededError as e:
            logger.warning("GA4 kota aşımı | user_id=%s | %s", user_id, e)
            return {"summary": None, "daily": [], "error": "quota"}
        except GA4PropertyNotFoundError as e:
            logger.warning("GA4 property bulunamadı | user_id=%s | %s", user_id, e)
            return {"summary": None, "daily": [], "error": "property_not_found"}
        except ValueError as e:
            # Entegrasyon yok → mock fallback
            logger.info("GA4 entegrasyonu yok, mock döndürülüyor | %s", e)
            return {"summary": None, "daily": [], "error": "not_connected"}
        except Exception as e:
            logger.error("GA4 bilinmeyen hata | user_id=%s | %s", user_id, e)
            return {"summary": None, "daily": [], "error": "unknown"}
