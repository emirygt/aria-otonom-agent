# Aria — AI Marketing OS

## Proje Özeti
Aria, Türkiye'deki e-ticaret KOBİ'leri için AI Marketing OS.
Tagline: "Reklam bütçeni boşa harcama."
Hedef kitle: Aylık ₺500K–₺10M ciro yapan Shopify/Ticimax mağazası sahipleri.

## Tech Stack
- **Backend:** Python 3.11 + FastAPI (async) + SQLAlchemy + Alembic
- **AI:** Anthropic SDK (claude-haiku-4-5 başlangıç, claude-sonnet-4-6 sonra)
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS
- **Auth:** JWT (python-jose + passlib)
- **Container:** Docker + Docker Compose

## Klasör Yapısı
```
aria/
├── docker-compose.yml
├── backend/
│   ├── main.py
│   ├── core/config.py, auth.py
│   ├── db/database.py, models.py
│   ├── api/routes/auth.py, dashboard.py, insights.py, integrations.py, operator.py
│   └── agents/orchestrator.py, data_agent.py, insight_agent.py, operator_agent.py
└── frontend/
    └── src/app/, components/, lib/
```

## Tamamlanan Özellikler
- Auth: JWT register/login/me — TAM
- DB Models: User, Integration, HealthScore, Insight, DataSnapshot, OperatorAction — TAM
- Dashboard routes: /overview, /campaigns — DEMO DATA (gerçek GA4 yok)
- Operator agent: plan/confirm/history + güvenlik kuralları — TAM
- Orchestrator: Anthropic tool-use, Türkçe yanıt — TAM
- Insight agent: 6 kural motoru (10'dan 4 eksik) — KISMİ
- Data agent: tüm metodlar mock data döndürüyor — MOCK
- Frontend: dashboard, login, tüm komponentler — TAM

## Eksik / Sprint 3-4 Scope
1. **insight_agent.py** — 4 kural eksik: `product_performance_gap`, `low_returning_users`, `budget_exhaustion_risk`, `high_bounce_landing`
2. **data_agent.py** — gerçek GA4 API çağrısı yok, mock data
3. **operator_agent.py** — execute() placeholder, Google Ads API bağlantısı yok
4. **insights.py /generate** — placeholder, orchestrator bağlantısı eksik
5. **backend/.env** — `ANTHROPIC_API_KEY=buraya-gir` → gerçek key girilmemiş
6. **Google OAuth** — redirect scaffolded, callback handler bitmemiş

## Tasarım Sistemi
- Background: #000000
- Surface: #18181b (zinc-900)
- Border: #27272a (zinc-800)
- Text: #ffffff / #a1a1aa (zinc-400)
- Accent: #7c3aed (violet-600)
- Success: #10b981, Warning: #f59e0b, Danger: #ef4444

## Önemli Kurallar
- Tüm UI ve AI yanıtları Türkçe
- Metrikler TL cinsinden
- Agent'lar: günlük bütçeyi %50'den fazla artırma, onaysız kampanya kapatma
- DB session dependency injection ile yönet
- Async/await her yerde tutarlı
- Credentials JSON içinde sakla (prod'da encrypt edilecek)

## Çalıştırma
```bash
cd /Users/emirygt/Desktop/aria
docker-compose up --build
```
- Frontend: http://localhost:3000
- API Docs: http://localhost:8080/docs
- Health: http://localhost:8080/health

## Seed / Test
- Kayıt: POST /api/v1/auth/register
- Giriş: POST /api/v1/auth/login
- Dashboard: GET /api/v1/dashboard/overview (JWT gerekli)
