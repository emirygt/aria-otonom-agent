from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta

from db.models import User, Integration
from db.database import get_db
from core.auth import get_current_user
from agents.data_agent import DataAgent

router = APIRouter()


class MetricValue(BaseModel):
    value: float
    change_pct: float
    trend: str


class HealthScoreSummary(BaseModel):
    score: int
    trend: str
    top_issues: list[str]


class OverviewResponse(BaseModel):
    health_score: HealthScoreSummary
    revenue_tl: MetricValue
    sessions: MetricValue
    conversion_rate: MetricValue
    roas: MetricValue
    data_source: str = "mock"


class Campaign(BaseModel):
    name: str
    spend_tl: float
    revenue_tl: float
    roas: float
    status: str
    trend: str


class TrendPoint(BaseModel):
    date: str
    revenue: float
    sessions: int


class TrendsResponse(BaseModel):
    weekly: list[TrendPoint]
    data_source: str = "mock"


async def _get_ga4_integration(user_id, db: AsyncSession):
    """Kullanıcının aktif GA4 entegrasyonunu ve property ID'sini döndür."""
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == user_id,
            Integration.platform == "ga4",
            Integration.status == "active",
        )
    )
    integration = result.scalar_one_or_none()
    if not integration or not integration.credentials:
        return None, None
    property_id = (integration.metadata_ or {}).get("property_id")
    return integration.credentials, property_id


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tokens, property_id = await _get_ga4_integration(current_user.id, db)
    agent = DataAgent()
    data = await agent.get_ga4_overview(
        str(current_user.id), days=30, tokens=tokens, property_id=property_id
    )

    source = data.get("data_source", "mock")
    sessions = data["sessions"]
    revenue = data["revenue_tl"]
    conv_rate = data["conversion_rate"] * 100  # yüzdeye çevir

    # Cihaz verisi — mobil/masaüstü farkı için
    device_data = await agent.get_device_breakdown(
        str(current_user.id), tokens=tokens, property_id=property_id
    )
    mobile_conv = device_data.get("mobile", {}).get("conversion_rate", 0.012) * 100
    desktop_conv = device_data.get("desktop", {}).get("conversion_rate", 0.028) * 100
    mobile_gap_pct = round((desktop_conv - mobile_conv) / desktop_conv * 100) if desktop_conv > 0 else 45

    issues = [
        f"Mobil dönüşüm masaüstünden %{mobile_gap_pct} düşük",
        f"Son 30 günde {sessions:,} oturum, %{conv_rate:.1f} dönüşüm oranı",
        "Checkout terk oranını kontrol edin",
    ]

    score = min(100, max(0, int(conv_rate * 25 + (revenue / 100_000))))

    return OverviewResponse(
        health_score=HealthScoreSummary(score=score, trend="up", top_issues=issues),
        revenue_tl=MetricValue(value=revenue, change_pct=0.0, trend="stable"),
        sessions=MetricValue(value=float(sessions), change_pct=0.0, trend="stable"),
        conversion_rate=MetricValue(value=round(conv_rate, 2), change_pct=0.0, trend="stable"),
        roas=MetricValue(value=4.2, change_pct=-0.6, trend="down"),
        data_source=source,
    )


@router.get("/campaigns", response_model=list[Campaign])
async def campaigns(current_user: User = Depends(get_current_user)):
    return [
        Campaign(name="Yaz Koleksiyonu - Google", spend_tl=45_200, revenue_tl=198_400, roas=4.39, status="active", trend="up"),
        Campaign(name="Retargeting - Meta", spend_tl=18_700, revenue_tl=67_300, roas=3.60, status="active", trend="stable"),
        Campaign(name="Marka Bilinirlik - Google", spend_tl=12_400, revenue_tl=28_100, roas=2.27, status="active", trend="down"),
        Campaign(name="Dinamik Ürün - Meta", spend_tl=32_100, revenue_tl=154_080, roas=4.80, status="active", trend="up"),
        Campaign(name="Arama Ağı - Genel", spend_tl=8_900, revenue_tl=14_200, roas=1.60, status="paused", trend="down"),
    ]


@router.get("/trends", response_model=TrendsResponse)
async def trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tokens, property_id = await _get_ga4_integration(current_user.id, db)
    agent = DataAgent()
    points = await agent.get_ga4_trends(
        str(current_user.id), days=14, tokens=tokens, property_id=property_id
    )
    source = points[0].get("data_source", "mock") if points else "mock"
    return TrendsResponse(
        weekly=[TrendPoint(date=p["date"], revenue=p["revenue"], sessions=p["sessions"]) for p in points],
        data_source=source,
    )
