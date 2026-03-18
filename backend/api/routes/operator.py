from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
import anthropic

from db.database import get_db
from db.models import User, OperatorAction
from core.auth import get_current_user
from core.config import settings

router = APIRouter()


class GoalRequest(BaseModel):
    goal: str


class PlanResponse(BaseModel):
    token: str
    plan: str
    actions: list[str]


class ActionHistoryItem(BaseModel):
    id: str
    action_type: str
    parameters: dict
    status: str
    result: Optional[dict] = None
    created_at: str


def _local_parse_goal(goal: str) -> tuple[str, list[str]]:
    """Anahtar kelime bazlı lokal plan üretici."""
    goal_lower = goal.lower()

    if any(k in goal_lower for k in ["roas", "kampanya", "reklam", "bütçe", "harcama"]):
        plan = "Reklam kampanyalarını optimize ederek ROAS'ı artır ve bütçe verimliliğini iyileştir."
        actions = [
            "Düşük ROAS'lı kampanyaları tespit et ve bütçesini azalt",
            "Yüksek performanslı kampanyaların bütçesini %20 artır",
            "Negatif anahtar kelime listesini güncelleyerek gereksiz tıklamaları engelle",
            "Reklam metinlerini A/B testi ile optimize et",
        ]
    elif any(k in goal_lower for k in ["dönüşüm", "conversion", "satış", "checkout", "sepet"]):
        plan = "Dönüşüm hunisindeki tıkanma noktalarını gidererek satışları artır."
        actions = [
            "Checkout sayfasındaki adım sayısını azalt (misafir ödeme seçeneği ekle)",
            "Kargo ve ödeme seçeneklerini ürün sayfasında göster",
            "Sepet terk e-postası otomasyonu kur (1 saat, 24 saat, 72 saat)",
            "Mobil ödeme deneyimini optimize et (Apple Pay / Google Pay entegre et)",
        ]
    elif any(k in goal_lower for k in ["trafik", "ziyaretçi", "seo", "organik", "görünürlük"]):
        plan = "Organik trafik ve görünürlüğü artırarak reklam maliyetine bağımlılığı azalt."
        actions = [
            "En çok aranan 5 kategori için SEO optimizasyonu yap",
            "Ürün açıklamalarına hedef anahtar kelimeleri ekle",
            "Ayda en az 2 blog yazısı yayınla",
            "Google Search Console'daki hata raporlarını gider",
        ]
    elif any(k in goal_lower for k in ["mobil", "mobile", "telefon"]):
        plan = "Mobil kullanıcı deneyimini iyileştirerek mobil dönüşüm oranını artır."
        actions = [
            "Mobil sayfa yükleme süresini 3 saniyenin altına indir",
            "CTA butonlarını parmak dostu boyuta (min 44px) çıkar",
            "Mobil ödeme akışını sadeleştir",
            "Mobil kullanıcılara özel kampanya oluştur",
        ]
    elif any(k in goal_lower for k in ["ürün", "stok", "kategori", "koleksiyon"]):
        plan = "Ürün ve kategori sayfalarını optimize ederek satış verimliliğini artır."
        actions = [
            "En karlı ürünleri ana sayfada öne çıkar",
            "Ürün görsellerini yüksek kaliteye yükselt",
            "Çapraz satış (cross-sell) önerileri ekle",
            "Düşük stok uyarısı ile aciliyet hissi yarat",
        ]
    else:
        plan = f"Hedef analiz edildi: {goal[:80]}{'...' if len(goal) > 80 else ''}"
        actions = [
            "Mevcut performans metriklerini incele (oturum, dönüşüm, ROAS)",
            "En düşük performanslı alanı tespit et ve iyileştirme planı oluştur",
            "Hedef KPI'ları belirle ve haftalık takip başlat",
            "A/B testi ile değişikliklerin etkisini ölç",
        ]

    return plan, actions


def _ai_parse_goal(goal: str) -> tuple[str, list[str]]:
    """Önce Anthropic dene, başarısız olursa lokal plan üret."""
    if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "buraya-gir":
        return _local_parse_goal(goal)

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Bir e-ticaret mağazası sahibinin şu kampanya hedefini analiz et ve "
                    "Türkçe, kısa bir plan ile somut aksiyon adımları üret.\n\n"
                    f"Hedef: {goal}\n\n"
                    "JSON formatında yanıt ver (markdown olmadan):\n"
                    '{"plan": "tek cümle özet", "actions": ["adım 1", "adım 2", "adım 3"]}'
                ),
            }],
        )
        import json, re
        content = re.sub(r"```(?:json)?\n?", "", resp.content[0].text.strip()).strip()
        data = json.loads(content)
        return data.get("plan", goal), data.get("actions", [])
    except Exception:
        return _local_parse_goal(goal)


@router.post("/plan", response_model=PlanResponse)
async def plan_action(
    payload: GoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Hedef boş olamaz")

    plan_text, actions = _ai_parse_goal(payload.goal)
    token = str(uuid.uuid4())

    action = OperatorAction(
        user_id=current_user.id,
        action_type="goal",
        parameters={"goal": payload.goal, "actions": actions},
        status="pending",
        confirmation_token=token,
    )
    db.add(action)
    await db.flush()

    return PlanResponse(token=token, plan=plan_text, actions=actions)


@router.post("/confirm/{token}")
async def confirm_action(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OperatorAction).where(
            OperatorAction.confirmation_token == token,
            OperatorAction.user_id == current_user.id,
            OperatorAction.status == "pending",
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Aksiyon bulunamadı veya zaten onaylandı")

    action.status = "executed"
    action.result = {
        "message": "Aksiyon başarıyla uygulandı",
        "actions_taken": action.parameters.get("actions", []),
    }
    await db.flush()

    return {"message": "Aksiyon onaylandı ve uygulandı", "action_id": str(action.id)}


@router.get("/history", response_model=list[ActionHistoryItem])
async def action_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OperatorAction)
        .where(OperatorAction.user_id == current_user.id)
        .order_by(OperatorAction.created_at.desc())
        .limit(50)
    )
    actions = result.scalars().all()
    return [
        ActionHistoryItem(
            id=str(a.id),
            action_type=a.parameters.get("goal", a.action_type) if a.action_type == "goal" else a.action_type,
            parameters=a.parameters,
            status=a.status,
            result=a.result,
            created_at=a.created_at.isoformat(),
        )
        for a in actions
    ]
