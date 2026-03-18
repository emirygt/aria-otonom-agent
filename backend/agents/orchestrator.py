"""
Orchestrator — Aria'nın ana beyin.
Anthropic SDK + tool use ile diğer agent'ları koordine eder.
Sprint 3'te tam olarak devreye girecek.
"""
from typing import Any
import anthropic

from core.config import settings
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.operator_agent import OperatorAgent


TOOLS = [
    {
        "name": "get_overview",
        "description": "Kullanıcının GA4 genel bakış verisini çeker: oturum, gelir, dönüşüm.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Kaç günlük veri (default 30)", "default": 30}
            },
        },
    },
    {
        "name": "get_insights",
        "description": "Kullanıcı için insight analizi çalıştırır ve Türkçe öneriler üretir.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "plan_operator_action",
        "description": "Google Ads'te bir aksiyon planlar (kampanya durdur, bütçe değiştir).",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string"},
                "parameters": {"type": "object"},
            },
            "required": ["action_type", "parameters"],
        },
    },
]

SYSTEM_PROMPT = """Sen Aria'sın — Türkiye'deki e-ticaret KOBİ'leri için yapay zekâ destekli bir pazarlama asistanısın.

Görevin:
1. Kullanıcının reklam ve analitik verilerini anlayıp Türkçe, net öneriler sunmak
2. Sorunların nedenini açıklamak (sadece ne olduğunu değil, neden olduğunu)
3. Somut aksiyon adımları önermek
4. Gerektiğinde kampanya aksiyonları planlamak (ama HİÇBİR ZAMAN onaysız uygulama)

Ton: Profesyonel ama anlaşılır. KOBİ sahibine arkadaşça ama doğrudan konuş.
Format: Kısa paragraflar. Önemli metrikleri TL cinsinden belirt."""


class Orchestrator:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.data_agent = DataAgent()
        self.insight_agent = InsightAgent()
        self.operator_agent = OperatorAgent()
        self._client = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def chat(self, user_message: str) -> str:
        """Kullanıcı mesajına yanıt ver, gerekirse tool kullan."""
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "buraya-gir":
            return "Lütfen backend/.env dosyasına geçerli bir ANTHROPIC_API_KEY ekleyin."

        messages = [{"role": "user", "content": user_message}]

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._handle_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return "Bir hata oluştu, lütfen tekrar deneyin."

    async def _handle_tool(self, name: str, inputs: dict) -> Any:
        match name:
            case "get_overview":
                return await self.data_agent.get_ga4_overview(self.user_id, inputs.get("days", 30))
            case "get_insights":
                return await self.insight_agent.analyze(self.user_id)
            case "plan_operator_action":
                return await self.operator_agent.plan(inputs["action_type"], inputs["parameters"])
            case _:
                return {"error": f"Bilinmeyen tool: {name}"}

    def _extract_text(self, response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""
