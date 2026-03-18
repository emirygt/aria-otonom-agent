"""
Insight Agent — Veriyi analiz eder, 10 kural motoru çalıştırır,
Anthropic API ile Türkçe KOBİ dostu açıklama üretir.
"""
from typing import Any
import anthropic

from core.config import settings
from agents.data_agent import DataAgent


class InsightAgent:
    def __init__(self):
        self.data_agent = DataAgent()
        self._anthropic = None

    @property
    def anthropic(self) -> anthropic.Anthropic:
        if self._anthropic is None:
            self._anthropic = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    async def analyze(self, user_id: str) -> list[dict[str, Any]]:
        """Tüm kuralları çalıştır, Anthropic ile açıklamaları zenginleştir."""
        funnel = await self.data_agent.get_funnel_data(user_id)
        devices = await self.data_agent.get_device_breakdown(user_id)
        sources = await self.data_agent.get_traffic_sources(user_id)
        campaigns = await self.data_agent.get_campaigns(user_id)
        weekly = await self.data_agent.get_weekly_comparison(user_id)

        products = await self.data_agent.get_product_performance(user_id)
        returning = await self.data_agent.get_returning_users(user_id)
        budget = await self.data_agent.get_budget_status(user_id)
        landing_pages = await self.data_agent.get_landing_pages(user_id)

        raw_insights = []
        raw_insights.extend(self._rule_checkout_drop(funnel))
        raw_insights.extend(self._rule_mobile_conversion(devices))
        raw_insights.extend(self._rule_high_bounce_landing(landing_pages))
        raw_insights.extend(self._rule_campaign_roas_declining(campaigns))
        raw_insights.extend(self._rule_organic_opportunity(sources))
        raw_insights.extend(self._rule_top_performing_channel(campaigns))
        raw_insights.extend(self._rule_product_performance_gap(products))
        raw_insights.extend(self._rule_weekly_traffic_anomaly(weekly))
        raw_insights.extend(self._rule_low_returning_users(returning))
        raw_insights.extend(self._rule_budget_exhaustion_risk(budget))

        # Kural motoru basit insight'ları halletti; karmaşıkları AI'a gönder
        enriched = []
        for insight in raw_insights:
            enriched.append(await self._enrich_with_ai(insight))

        return enriched

    # ─── 10 Kural ──────────────────────────────────────────────────────────────

    def _rule_checkout_drop(self, funnel: dict) -> list[dict]:
        """Kural 1: checkout_drop > %30 → critical"""
        drop = funnel.get("checkout_drop_rate", 0)
        if drop > 0.30:
            return [{
                "rule": "checkout_drop",
                "category": "funnel",
                "severity": "critical",
                "title": f"Checkout sayfasında %{drop*100:.0f} terk oranı tespit edildi",
                "data": {"drop_rate": drop},
            }]
        return []

    def _rule_mobile_conversion(self, devices: dict) -> list[dict]:
        """Kural 2: mobile/desktop dönüşüm farkı > %40 → warning"""
        mobile_cr = devices.get("mobile", {}).get("conversion_rate", 0)
        desktop_cr = devices.get("desktop", {}).get("conversion_rate", 1)
        if desktop_cr > 0:
            gap = (desktop_cr - mobile_cr) / desktop_cr
            if gap > 0.40:
                return [{
                    "rule": "mobile_conversion_low",
                    "category": "traffic",
                    "severity": "warning",
                    "title": f"Mobil dönüşüm masaüstünün %{gap*100:.0f} gerisinde",
                    "data": {"mobile_cr": mobile_cr, "desktop_cr": desktop_cr, "gap_pct": gap},
                }]
        return []

    def _rule_campaign_roas_declining(self, campaigns: list) -> list[dict]:
        """Kural 4: Kampanya ROAS trendi negatifse → warning"""
        declining = [c for c in campaigns if c.get("trend") == "down" and c.get("roas", 0) < 3.0]
        if declining:
            return [{
                "rule": "campaign_roas_declining",
                "category": "campaign",
                "severity": "warning",
                "title": f"{len(declining)} kampanyanın ROAS trendi negatife döndü",
                "data": {"campaigns": [c["name"] for c in declining]},
            }]
        return []

    def _rule_organic_opportunity(self, sources: dict) -> list[dict]:
        """Kural 5: organic share < %20 → opportunity"""
        organic_share = sources.get("organic_search", {}).get("share", 0)
        if organic_share < 0.20:
            return [{
                "rule": "organic_opportunity",
                "category": "traffic",
                "severity": "opportunity",
                "title": f"Organik trafik payı yalnızca %{organic_share*100:.0f} — büyüme fırsatı var",
                "data": {"organic_share": organic_share},
            }]
        return []

    def _rule_top_performing_channel(self, campaigns: list) -> list[dict]:
        """Kural 6: En yüksek ROAS kaynağını bul → opportunity"""
        active = [c for c in campaigns if c.get("status") == "active" and c.get("roas", 0) > 4.0]
        if active:
            best = max(active, key=lambda c: c["roas"])
            return [{
                "rule": "top_performing_channel",
                "category": "campaign",
                "severity": "opportunity",
                "title": f"'{best['name']}' kampanyası {best['roas']:.1f}x ROAS ile öne çıkıyor",
                "data": {"campaign": best["name"], "roas": best["roas"]},
            }]
        return []

    def _rule_high_bounce_landing(self, landing_pages: list) -> list[dict]:
        """Kural 3: bounce > %70 ve yüksek trafikli landing page → warning"""
        problematic = [
            p for p in landing_pages
            if p.get("bounce_rate", 0) > 0.70 and p.get("sessions", 0) > 3_000
        ]
        if problematic:
            worst = max(problematic, key=lambda p: p["bounce_rate"])
            return [{
                "rule": "high_bounce_landing",
                "category": "traffic",
                "severity": "warning",
                "title": f"'{worst['page']}' sayfasında %{worst['bounce_rate']*100:.0f} hemen çıkma oranı",
                "data": {
                    "page": worst["page"],
                    "bounce_rate": worst["bounce_rate"],
                    "sessions": worst["sessions"],
                    "affected_pages": len(problematic),
                },
            }]
        return []

    def _rule_weekly_traffic_anomaly(self, weekly: dict) -> list[dict]:
        """Kural 8: Haftalık trafik %25+ sapma → warning"""
        change = weekly.get("change_sessions_pct", 0)
        if abs(change) > 25:
            direction = "artış" if change > 0 else "düşüş"
            return [{
                "rule": "weekly_traffic_anomaly",
                "category": "traffic",
                "severity": "warning",
                "title": f"Geçen haftaya göre %{abs(change):.0f} trafik {direction}ı",
                "data": {"change_pct": change},
            }]
        return []

    def _rule_product_performance_gap(self, products: dict) -> list[dict]:
        """Kural 7: En çok satan vs en karlı ürün arasında büyük fark → insight"""
        top_revenue = products.get("top_by_revenue", [])
        top_margin = products.get("top_by_margin", [])
        if not top_revenue or not top_margin:
            return []
        best_seller = top_revenue[0]
        best_margin = top_margin[0]
        # En çok satan ile en karlı farklı ürünse ve marjin farkı büyükse
        if (best_seller["name"] != best_margin["name"] and
                best_margin["margin_pct"] - best_seller["margin_pct"] > 0.20):
            return [{
                "rule": "product_performance_gap",
                "category": "product",
                "severity": "opportunity",
                "title": f"En çok satan ürün en karlı değil — %{(best_margin['margin_pct'] - best_seller['margin_pct'])*100:.0f} marj farkı",
                "data": {
                    "top_seller": best_seller["name"],
                    "top_seller_margin": best_seller["margin_pct"],
                    "top_margin_product": best_margin["name"],
                    "top_margin_pct": best_margin["margin_pct"],
                    "gap_pct": best_margin["margin_pct"] - best_seller["margin_pct"],
                },
            }]
        return []

    def _rule_low_returning_users(self, returning: dict) -> list[dict]:
        """Kural 9: Geri dönen kullanıcı < %15 → warning"""
        returning_pct = returning.get("returning_pct", 1.0)
        if returning_pct < 0.15:
            return [{
                "rule": "low_returning_users",
                "category": "traffic",
                "severity": "warning",
                "title": f"Sadakat düşük: Kullanıcıların yalnızca %{returning_pct*100:.0f}'i geri dönüyor",
                "data": {
                    "returning_pct": returning_pct,
                    "returning_users": returning.get("returning_users"),
                    "total_users": returning.get("total_users"),
                },
            }]
        return []

    def _rule_budget_exhaustion_risk(self, budget: dict) -> list[dict]:
        """Kural 10: Ay bitmeden bütçe bitecekse → critical"""
        projected = budget.get("projected_total_tl", 0)
        monthly = budget.get("monthly_budget_tl", 1)
        days_remaining = budget.get("days_remaining", 0)
        overspend_pct = (projected - monthly) / monthly if monthly > 0 else 0
        if overspend_pct > 0.10 and days_remaining > 3:
            return [{
                "rule": "budget_exhaustion_risk",
                "category": "campaign",
                "severity": "critical",
                "title": f"Mevcut harcama hızıyla bütçe ay bitmeden %{overspend_pct*100:.0f} aşılacak",
                "data": {
                    "monthly_budget_tl": monthly,
                    "spent_tl": budget.get("spent_tl"),
                    "projected_total_tl": round(projected),
                    "days_remaining": days_remaining,
                    "overspend_tl": round(projected - monthly),
                },
            }]
        return []

    # ─── AI Zenginleştirme ──────────────────────────────────────────────────────

    def _rule_fallback(self, raw: dict) -> dict:
        """Anthropic olmadan kural verisiyle Türkçe açıklama üret."""
        rule = raw["rule"]
        data = raw.get("data", {})

        templates = {
            "checkout_drop": {
                "finding": f"Checkout sayfanızda %{data.get('drop_rate', 0)*100:.0f} sepet terk oranı tespit edildi. "
                           f"Her 100 kullanıcıdan {int(data.get('drop_rate', 0)*100)}'i ödeme adımını tamamlamıyor.",
                "cause": "Mobil ödeme formlarındaki karmaşıklık, zorunlu üyelik şartı veya beklenmedik kargo ücretleri "
                         "kullanıcıları son adımda kaybettiriyor.",
                "action": "1) Misafir ödeme seçeneği ekle  2) Kargo ücretini ürün sayfasında göster  "
                          "3) Mobil checkout formunu 3 adımdan fazla tutma  4) Güven rozetleri (SSL, iade garantisi) ekle.",
            },
            "mobile_conversion_low": {
                "finding": f"Mobil dönüşüm oranınız %{data.get('mobile_cr', 0)*100:.1f} iken masaüstünde "
                           f"%{data.get('desktop_cr', 0)*100:.1f}. Mobil kullanıcılar alım yapmadan ayrılıyor.",
                "cause": "Mobil kullanıcı deneyimi masaüstü kadar optimize edilmemiş; küçük butonlar, yavaş yükleme "
                         "veya karmaşık navigasyon mobil dönüşümü düşürüyor.",
                "action": "1) CTA butonlarını en az 44px yüksekliğe çıkar  2) Sayfa yükleme süresini 3 saniyenin altına indir  "
                          "3) Mobil ödeme için Apple Pay / Google Pay ekle  4) Ürün görsellerini optimize et.",
            },
            "high_bounce_landing": {
                "finding": f"'{data.get('page', '')}' sayfanız %{data.get('bounce_rate', 0)*100:.0f} hemen çıkma oranıyla "
                           f"{data.get('sessions', 0):,} ziyaret alıyor. Ziyaretçiler sayfaya gelip hemen ayrılıyor.",
                "cause": "Reklam mesajı ile açılış sayfası içeriği arasında uyumsuzluk, yavaş yükleme veya "
                         "ilgi çekici bir CTA olmaması hemen çıkmayı artırıyor.",
                "action": "1) Reklam metniyle sayfa başlığını hizala  2) Hero bölümüne net bir CTA ekle  "
                          "3) Sayfayı mobilde 2 saniyenin altında yüklenecek şekilde optimize et  "
                          "4) Sosyal kanıt (müşteri yorumları) ekle.",
            },
            "campaign_roas_declining": {
                "finding": f"{len(data.get('campaigns', []))} kampanyanızın ROAS'ı düşüşe geçti: "
                           f"{', '.join(data.get('campaigns', [])[:2])}. Harcama artıyor, gelir düşüyor.",
                "cause": "Rekabet artışı tıklama maliyetlerini yükseltiyor; aynı bütçeyle daha az dönüşüm elde ediliyor. "
                         "Hedef kitle yorgunluğu veya mevsimsel etkenler de rol oynuyor olabilir.",
                "action": "1) Düşük performanslı anahtar kelimeleri duraklat  2) Bütçeyi yüksek ROAS'lı kampanyalara kaydır  "
                          "3) Reklam metinlerini ve görselleri yenile  4) Hedef kitle segmentasyonunu daralt.",
            },
            "organic_opportunity": {
                "finding": f"Trafiğinizin yalnızca %{data.get('organic_share', 0)*100:.0f}'i organik aramadan geliyor. "
                           "Rakipleriniz SEO'ya yatırım yaparak reklam maliyeti olmadan büyüyor.",
                "cause": "Blog içeriği ve kategori sayfası SEO'su yetersiz kalmış. Ücretli trafiğe bağımlılık "
                         "uzun vadede reklam maliyetlerini artırıyor.",
                "action": "1) En çok aranan 5 kategori için SEO optimizasyonu yap  2) Ayda 2 blog yazısı üret  "
                          "3) Ürün açıklamalarına anahtar kelime ekle  4) Site hızını ve mobil uyumluluğu iyileştir.",
            },
            "top_performing_channel": {
                "finding": f"'{data.get('campaign', '')}' kampanyanız {data.get('roas', 0):.1f}x ROAS ile "
                           "diğer tüm kanalları geride bırakıyor. Bu kanal büyüme için hazır.",
                "cause": "Bu kampanya doğru hedef kitleye doğru mesajla ulaşıyor. Bütçe artışı orantılı gelir büyümesi sağlayabilir.",
                "action": "1) Bu kampanyanın bütçesini %20-30 artır  2) Benzer hedef kitle (lookalike) oluştur  "
                          "3) Bu kampanyadaki reklam metni ve görseli diğer kanallara uygula  "
                          "4) Haftalık performansı yakından izle.",
            },
            "product_performance_gap": {
                "finding": f"En çok satan ürününüz ({data.get('top_seller', '')}) en karlı değil. "
                           f"En karlı ürününüz %{data.get('gap_pct', 0)*100:.0f} daha yüksek marjla satılıyor.",
                "cause": "Yüksek ciro düşük marjlı ürünlere odaklanmak toplam karlılığı sınırlandırıyor. "
                         "Reklam bütçesi yanlış ürünlere yönlendiriliyor olabilir.",
                "action": f"1) '{data.get('top_margin_product', '')}' ürününü öne çıkar  "
                          "2) Yüksek marjlı ürünlere reklam bütçesi kaydır  "
                          "3) Çapraz satış (cross-sell) ile karlı ürünleri sepete eklet.",
            },
            "weekly_traffic_anomaly": {
                "finding": f"Geçen haftaya kıyasla trafiğinizde %{abs(data.get('change_pct', 0)):.0f} "
                           f"{'artış' if data.get('change_pct', 0) > 0 else 'düşüş'} tespit edildi. Bu beklenmedik bir değişim.",
                "cause": "Mevsimsel etkenler, rakip kampanyaları, algoritma güncellemeleri veya "
                         "teknik bir sorun (404 sayfaları, yavaş yükleme) trafiği etkiliyor olabilir.",
                "action": "1) Trafik kaynağı dağılımını kontrol et  2) Search Console'da sıralama değişikliklerini incele  "
                          "3) Rakiplerin reklam aktivitesini gözlemle  4) Site'de teknik sorun olmadığını doğrula.",
            },
            "low_returning_users": {
                "finding": f"Kullanıcılarınızın yalnızca %{data.get('returning_pct', 0)*100:.0f}'i tekrar geliyor. "
                           f"{data.get('returning_users', 0):,} sadık müşteriye karşın {data.get('total_users', 0):,} toplam kullanıcı var.",
                "cause": "Müşteri deneyimi satın alma sonrası zayıf kalıyor. E-posta pazarlaması, sadakat programı "
                         "veya yeniden hedefleme kampanyaları yetersiz.",
                "action": "1) Satın alma sonrası e-posta serisi kur (teşekkür, sipariş güncelleme, ürün önerisi)  "
                          "2) Sadakat puanı programı başlat  3) 30 gün içinde dönmeyen müşterilere özel indirim gönder.",
            },
            "budget_exhaustion_risk": {
                "finding": f"Mevcut harcama hızınızla aylık ₺{data.get('monthly_budget_tl', 0):,.0f} bütçeniz "
                           f"ay bitmeden %{((data.get('projected_total_tl', 0) - data.get('monthly_budget_tl', 0)) / max(data.get('monthly_budget_tl', 1), 1) * 100):.0f} aşılacak.",
                "cause": "Tıklama maliyetlerindeki artış veya kampanya optimize edilmemiş teklif stratejisi "
                         "bütçeyi planlanandan hızlı tüketiyor.",
                "action": f"1) Günlük bütçe sınırını {data.get('days_remaining', 0)} günlük kalan bütçeye göre ayarla  "
                          "2) Düşük performanslı kampanyaları duraklat  "
                          "3) Teklif stratejisini hedef ROAS'a çevir  4) En karlı saatlere göre gün bölümü uygula.",
            },
        }

        fallback = templates.get(rule, {
            "finding": raw["title"],
            "cause": "Verileriniz bu alanda iyileştirme fırsatı olduğuna işaret ediyor.",
            "action": "Detaylı analiz için ilgili metriklerinizi incelemenizi öneriyoruz.",
        })

        return {
            "rule": rule,
            "category": raw["category"],
            "severity": raw["severity"],
            "title": raw["title"],
            "finding": fallback["finding"],
            "cause": fallback["cause"],
            "action": fallback["action"],
            "impact_tl": fallback.get("impact_tl"),
        }

    async def _enrich_with_ai(self, raw: dict) -> dict:
        """Anthropic Haiku ile Türkçe KOBİ dostu açıklama üret. Başarısız olursa kural fallback'e düş."""
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "buraya-gir":
            return self._rule_fallback(raw)

        prompt = f"""Sen Aria adlı bir AI pazarlama asistanısın. Türkiye'deki e-ticaret KOBİ sahiplerine yardım ediyorsun.

Aşağıdaki analiz bulgusunu Türkçe, anlaşılır ve aksiyon odaklı şekilde açıkla:

Kural: {raw['rule']}
Başlık: {raw['title']}
Veri: {raw['data']}

Şu JSON formatında yanıt ver (markdown code block olmadan, sadece JSON):
{{
  "finding": "Ne tespit edildi (1-2 cümle, veri destekli)",
  "cause": "Neden oluyor (1-2 cümle)",
  "action": "Ne yapılmalı (somut, uygulanabilir adımlar)",
  "impact_tl": null
}}"""

        try:
            response = self.anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            import json, re
            content = response.content[0].text.strip()
            # Markdown code block varsa temizle
            content = re.sub(r"```(?:json)?\n?", "", content).strip()
            ai_data = json.loads(content)
            return {
                "rule": raw["rule"],
                "category": raw["category"],
                "severity": raw["severity"],
                "title": raw["title"],
                **ai_data,
            }
        except Exception:
            return self._rule_fallback(raw)
