from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional
import uuid

from db.database import get_db
from db.models import User, Insight
from core.auth import get_current_user
from agents.insight_agent import InsightAgent

router = APIRouter()


class InsightResponse(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    finding: str
    cause: str
    action: str
    impact_tl: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


DEMO_INSIGHTS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": "Checkout sayfasında kritik düşüş tespit edildi",
        "category": "funnel",
        "severity": "critical",
        "finding": "Son 7 günde checkout sayfasına gelen kullanıcıların %38'i sepeti terk etti.",
        "cause": "Mobil ödeme adımında form hataları ve yavaş yükleme süresi kullanıcıları kaçırıyor.",
        "action": "Mobil checkout akışını optimize et, form validasyonlarını gözden geçir ve sayfa yükleme süresini 2 saniyenin altına indir.",
        "impact_tl": 287_400.0,
        "status": "active",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "title": "Mobil dönüşüm oranı masaüstünün çok altında",
        "category": "traffic",
        "severity": "warning",
        "finding": "Mobil cihazlarda dönüşüm oranı %1.2, masaüstünde %2.8. Fark %57.",
        "cause": "Mobil kullanıcı deneyimi masaüstü kadar optimize edilmemiş; buton boyutları ve görseller sorun yaratıyor.",
        "action": "Mobil UX testleri yap, CTA butonlarını büyüt, ürün görsellerini lazy-load ile yükle.",
        "impact_tl": 124_800.0,
        "status": "active",
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "title": "3 kampanyanın ROAS trendi negatife döndü",
        "category": "campaign",
        "severity": "warning",
        "finding": "Marka Bilinirlik, Arama Ağı Genel ve bir Meta kampanyasının 7 günlük ROAS ortalaması hedefin altına düştü.",
        "cause": "Rakiplerin teklif artışı ve mevsimsel rekabet artışı tıklama maliyetlerini yükseltti.",
        "action": "Düşük performanslı anahtar kelimeleri duraklat, bütçeyi yüksek ROAS'lı kampanyalara kaydır.",
        "impact_tl": 67_200.0,
        "status": "active",
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "title": "Organik trafik payı çok düşük — büyüme fırsatı var",
        "category": "traffic",
        "severity": "opportunity",
        "finding": "Organik arama trafiğin toplam ziyaretin yalnızca %14'ünü oluşturuyor.",
        "cause": "Blog içerikleri ve SEO çalışmaları yetersiz kalmış.",
        "action": "Yüksek arama hacimli 5 kategori sayfası için SEO optimizasyonu yap, ayda 2 blog içeriği üret.",
        "impact_tl": None,
        "status": "active",
    },
]


@router.get("/", response_model=list[InsightResponse])
async def list_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Insight).where(
            Insight.user_id == current_user.id,
            Insight.status == "active",
        )
    )
    db_insights = result.scalars().all()

    if db_insights:
        return [
            InsightResponse(
                id=str(i.id),
                title=i.title,
                category=i.category,
                severity=i.severity,
                finding=i.finding,
                cause=i.cause,
                action=i.action,
                impact_tl=i.impact_tl,
                status=i.status,
            )
            for i in db_insights
        ]

    # DB boşsa demo data döndür
    return [InsightResponse(**i) for i in DEMO_INSIGHTS]


@router.patch("/{insight_id}/dismiss", response_model=InsightResponse)
async def dismiss_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Insight).where(
            Insight.id == insight_id,
            Insight.user_id == current_user.id,
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight bulunamadı")

    insight.status = "dismissed"
    await db.flush()
    return InsightResponse(
        id=str(insight.id),
        title=insight.title,
        category=insight.category,
        severity=insight.severity,
        finding=insight.finding,
        cause=insight.cause,
        action=insight.action,
        impact_tl=insight.impact_tl,
        status=insight.status,
    )


@router.post("/generate", response_model=list[InsightResponse])
async def generate_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """InsightAgent'ı çalıştır, sonuçları DB'ye kaydet ve döndür."""
    agent = InsightAgent()
    raw_insights = await agent.analyze(str(current_user.id))

    # Mevcut aktif insight'ları temizle
    await db.execute(
        delete(Insight).where(
            Insight.user_id == current_user.id,
            Insight.status == "active",
        )
    )

    # Yeni insight'ları DB'ye kaydet
    saved = []
    for raw in raw_insights:
        insight = Insight(
            id=uuid.uuid4(),
            user_id=current_user.id,
            title=raw.get("title", ""),
            category=raw.get("category", "revenue"),
            severity=raw.get("severity", "warning"),
            finding=raw.get("finding", raw.get("title", "")),
            cause=raw.get("cause", ""),
            action=raw.get("action", ""),
            impact_tl=raw.get("impact_tl"),
            status="active",
        )
        db.add(insight)
        saved.append(insight)

    await db.flush()

    return [
        InsightResponse(
            id=str(i.id),
            title=i.title,
            category=i.category,
            severity=i.severity,
            finding=i.finding,
            cause=i.cause,
            action=i.action,
            impact_tl=i.impact_tl,
            status=i.status,
        )
        for i in saved
    ]
