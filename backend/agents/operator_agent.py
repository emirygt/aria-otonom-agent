"""
Operator Agent — Google Ads kampanyalarında aksiyon alır.
Onaysız hiçbir aksiyon uygulamaz.
Sprint 4'te gerçek Google Ads API bağlantısı eklenecek.
"""
from typing import Any


SUPPORTED_ACTIONS = ["pause_campaign", "increase_budget", "decrease_budget", "create_campaign"]

SAFETY_RULES = {
    "max_budget_increase_pct": 0.50,  # %50'den fazla artırma
    "require_confirmation": True,      # Her zaman onay zorunlu
}


class OperatorAgent:
    """Google Ads üzerinde güvenli aksiyon alan agent."""

    async def plan(self, action_type: str, parameters: dict) -> dict[str, Any]:
        """Aksiyon planı üret, güvenlik kontrolü yap."""
        if action_type not in SUPPORTED_ACTIONS:
            return {
                "ok": False,
                "error": f"Desteklenmeyen aksiyon: {action_type}. Desteklenenler: {SUPPORTED_ACTIONS}",
            }

        violations = self._check_safety(action_type, parameters)
        if violations:
            return {"ok": False, "error": "; ".join(violations)}

        description = self._describe(action_type, parameters)
        return {
            "ok": True,
            "action_type": action_type,
            "parameters": parameters,
            "description": description,
            "requires_confirmation": True,
        }

    async def execute(self, action_type: str, parameters: dict) -> dict[str, Any]:
        """
        Onaylanmış aksiyonu uygula.
        Sprint 4'te Google Ads API çağrısı buraya eklenecek.
        """
        # TODO Sprint 4: Google Ads API client ile gerçek işlem
        return {
            "ok": True,
            "action_type": action_type,
            "parameters": parameters,
            "result": "Aksiyon kuyruğa alındı (Sprint 4'te uygulanacak)",
            "executed": False,
        }

    def _check_safety(self, action_type: str, parameters: dict) -> list[str]:
        """Güvenlik kurallarını kontrol et, ihlalleri döndür."""
        violations = []

        if action_type == "increase_budget":
            current = parameters.get("current_budget_tl", 0)
            new = parameters.get("new_budget_tl", 0)
            if current > 0 and (new - current) / current > SAFETY_RULES["max_budget_increase_pct"]:
                violations.append(
                    f"Bütçe tek seferde %{SAFETY_RULES['max_budget_increase_pct']*100:.0f}'den fazla artırılamaz"
                )

        return violations

    def _describe(self, action_type: str, parameters: dict) -> str:
        """İnsan okunabilir aksiyon açıklaması."""
        match action_type:
            case "pause_campaign":
                return f"'{parameters.get('campaign_name', '?')}' kampanyası duraklatılacak"
            case "increase_budget":
                return (
                    f"'{parameters.get('campaign_name', '?')}' kampanyasının bütçesi "
                    f"₺{parameters.get('current_budget_tl', 0):,.0f} → ₺{parameters.get('new_budget_tl', 0):,.0f} artırılacak"
                )
            case "decrease_budget":
                return (
                    f"'{parameters.get('campaign_name', '?')}' kampanyasının bütçesi "
                    f"₺{parameters.get('current_budget_tl', 0):,.0f} → ₺{parameters.get('new_budget_tl', 0):,.0f} azaltılacak"
                )
            case "create_campaign":
                return f"Yeni kampanya oluşturulacak: '{parameters.get('campaign_name', '?')}'"
            case _:
                return action_type
