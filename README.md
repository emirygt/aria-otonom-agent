<p align="center">
  <img src="https://img.shields.io/badge/Status-Sprint%202-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/AI-Gemini%203.1%20Pro%20%7C%20Claude%203.5-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-Private-red?style=for-the-badge" />
</p>

# Aria — AI Marketing OS

> **"Reklam butceni bosa harcama."**

Aria, Turkiye'deki e-ticaret KOBi'leri icin gelistirilen otonom AI pazarlama ajanıdır. Google Analytics 4 ve Google Ads verilerinizi baglar, analiz eder ve aksiyona doner — siz uyurken bile.

---

## Project Overview

Aria, **Gemini 3.1 Pro Preview** ve **Anthropic Claude 3.5 Sonnet** modellerini kullanan, KOBi'lerin dijital pazarlama operasyonlarini otonom olarak yoneten bir SaaS platformudur.

**Hedef Kitle:** Aylik ₺500K–₺10M ciro yapan Shopify / Ticimax magaza sahipleri.

### Ne Yapar?

- Google Analytics 4 ve Google Ads hesaplarınıza **OAuth 2.0** ile baglanır
- Kampanya performansını **gercek zamanli** izler
- AI ajanları ile **otonom analiz** ve **aksiyon onerisi** uretir
- Refresh Token altyapısı sayesinde **7/24 kesintisiz** calısır
- Operator Agent ile guvenli, onay tabanli kampanya yonetimi saglar

---

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | Python 3.11, FastAPI (async), SQLAlchemy 2.0, Alembic |
| **Database** | PostgreSQL 15 (AsyncPG driver) |
| **Cache / Queue** | Redis 7 (Celery worker icin hazir) |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| **AI Models** | Gemini 3.1 Pro Preview, Anthropic Claude 3.5 Sonnet |
| **Auth** | JWT (python-jose + passlib), Google OAuth 2.0 |
| **Infra** | Docker, Docker Compose |

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Docker Network                │
                    │                                         │
   :4000            │  ┌───────────┐      ┌───────────┐      │
 ──────────────────►│  │ Frontend  │─────►│ Backend   │      │
   Browser          │  │ Next.js   │ API  │ FastAPI   │      │
                    │  │ :3000     │      │ :8080     │      │
                    │  └───────────┘      └─────┬─────┘      │
                    │                           │             │
                    │                     ┌─────┴─────┐       │
                    │                     │           │       │
                    │               ┌─────▼──┐  ┌────▼───┐   │
                    │               │ Postgres│  │ Redis  │   │
                    │               │  :5432  │  │ :6379  │   │
                    │               └────────┘  └────────┘   │
                    └─────────────────────────────────────────┘
                                      │
                              ┌───────┴────────┐
                              │  Google Cloud   │
                              │  OAuth 2.0      │
                              │  GA4 API        │
                              │  Ads API        │
                              └────────────────┘
```

### Port Mapping

| Service | Container Port | Host Port |
|---------|---------------|-----------|
| Backend (FastAPI) | 8080 | **3000** |
| Frontend (Next.js) | 3000 | **4000** |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |

### OAuth 2.0 Flow

```
User ──► Login Page ──► Backend /auth/google/connect
                              │
                              ▼
                        Google Consent
                              │
                              ▼
                   Backend /auth/google/callback
                              │
                        ┌─────┴─────┐
                        │ Create/   │
                        │ Find User │
                        │ Issue JWT │
                        └─────┬─────┘
                              │
                              ▼
                   Frontend /?token=JWT
                        (localStorage)
```

**GA4 & Ads Integration Flow:**

```
Dashboard ──► /integrations ──► Backend /integrations/google/connect
                                        │
                                        ▼
                                  Google Consent
                                  (analytics.readonly + adwords scope)
                                        │
                                        ▼
                              Backend /integrations/ga4/callback
                                        │
                                  ┌─────┴─────┐
                                  │ Save       │
                                  │ Tokens to  │
                                  │ Database   │
                                  └───────────┘
```

---

## Key Features

### 1. Otonom Veri Cekme (GA4 / Ads)
OAuth 2.0 ile baglanan hesaplardan **refresh token** kullanarak surekli veri ceker. Token suresi dolsa bile otomatik yeniler — kullanici mudahalesi gerekmez.

### 2. AI Destekli Kampanya Yorumlama
- **Orchestrator Agent:** Kullanici sorgularini anlayip dogru ajana yonlendirir
- **Data Agent:** GA4 ve Ads API'lerinden veri toplar
- **Insight Agent:** 6 kural motoru ile anomali ve firsatlari tespit eder
- **Operator Agent:** Kampanya degisikliklerini **onay tabanli** olarak yurutur

### 3. Guvenlik Kurallari
- Gunluk butceyi **%50'den fazla artirmaz**
- Onaysiz kampanya **kapatamaz**
- Tum aksiyonlar **log**lanir ve geri alinabilir

### 4. Turkce & TL
- Tum UI ve AI yanıtları **Turkce**
- Metrikler **TL** cinsinden

---

## Installation & Setup

### Gereksinimler

- Docker & Docker Compose
- Google Cloud Console projesi (OAuth 2.0 credentials)

### 1. Repo'yu Klonla

```bash
git clone https://github.com/emirygt/aria-otonom-agent.git
cd aria-otonom-agent
```

### 2. Environment Dosyalarini Olustur

**`backend/.env`**
```env
DATABASE_URL=postgresql+asyncpg://aria:aria@db:5432/aria
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/api/v1/integrations/ga4/callback
GOOGLE_AUTH_REDIRECT_URI=http://localhost:3000/api/v1/auth/google/callback
```

**`frontend/.env`**
```env
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXTAUTH_URL=http://localhost:4000
NEXTAUTH_SECRET=your-nextauth-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
DATABASE_URL=postgresql://aria:aria@db:5432/aria
```

### 3. Google Cloud Console

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. OAuth 2.0 Client ID olustur (Web Application)
3. Authorized redirect URIs ekle:
   - `http://localhost:3000/api/v1/auth/google/callback`
   - `http://localhost:3000/api/v1/integrations/ga4/callback`
4. Analytics API ve Google Ads API'yi etkinlestir

### 4. Calistir

```bash
docker-compose up --build
```

| Servis | URL |
|--------|-----|
| Frontend | http://localhost:4000 |
| API Docs | http://localhost:3000/docs |
| Health Check | http://localhost:3000/health |

---

## Current Status

### Sprint 1 — OAuth & DB Entegrasyonu ✅

- [x] JWT Authentication (Register / Login / Me)
- [x] Google OAuth 2.0 Login (backend-driven)
- [x] GA4 & Google Ads OAuth Integration
- [x] Token Storage & Auto-Refresh
- [x] Database Models (User, Integration, HealthScore, Insight, DataSnapshot, OperatorAction)
- [x] Dashboard UI (demo data)
- [x] Integrations Page (GA4 connect/disconnect)
- [x] Docker Compose full stack

### Sprint 2 — Data Extraction & AI Analysis 🔜

- [ ] GA4 Data API gercek veri cekme (Property ID ile)
- [ ] Google Ads API gercek veri cekme (Customer ID ile)
- [ ] Insight Agent: kalan 4 kural (`product_performance_gap`, `low_returning_users`, `budget_exhaustion_risk`, `high_bounce_landing`)
- [ ] Orchestrator → Insight pipeline baglantisi
- [ ] Data Agent: mock → gercek API gecisi
- [ ] Celery worker ile zamanlanmis veri cekme

### Sprint 3 — Operator & Automation 📋

- [ ] Operator Agent: execute() gercek Google Ads API baglantisi
- [ ] Kampanya butce degisikligi (onay tabanli)
- [ ] Otomatik raporlama
- [ ] Alarm / Notification sistemi

---

## API Endpoints

### Auth
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| POST | `/api/v1/auth/register` | Yeni kullanici kaydi |
| POST | `/api/v1/auth/login` | Email/sifre ile giris |
| GET | `/api/v1/auth/me` | Mevcut kullanici bilgisi |
| GET | `/api/v1/auth/google/connect` | Google OAuth baslat |
| GET | `/api/v1/auth/google/callback` | Google OAuth callback |

### Dashboard
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/dashboard/overview` | Genel bakis metrikleri |
| GET | `/api/v1/dashboard/campaigns` | Kampanya listesi |

### Integrations
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/integrations/status` | Bagli hesaplar |
| GET | `/api/v1/integrations/google/connect` | GA4/Ads OAuth baslat |
| GET | `/api/v1/integrations/ga4/callback` | GA4 OAuth callback |
| DELETE | `/api/v1/integrations/google/disconnect` | Baglanti kopar |

---

## Project Structure

```
aria/
├── docker-compose.yml
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── auth.py                # JWT utilities
│   │   └── google_oauth.py        # OAuth flow & HMAC state
│   ├── db/
│   │   ├── database.py            # AsyncPG session
│   │   └── models.py              # SQLAlchemy models
│   ├── api/routes/
│   │   ├── auth.py                # Auth endpoints
│   │   ├── dashboard.py           # Dashboard endpoints
│   │   ├── insights.py            # AI insights
│   │   ├── integrations.py        # Google OAuth integration
│   │   └── operator.py            # Operator agent actions
│   └── agents/
│       ├── orchestrator.py        # Multi-agent coordinator
│       ├── data_agent.py          # Data collection
│       ├── insight_agent.py       # Rule engine analysis
│       └── operator_agent.py      # Campaign operations
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── app/                   # Next.js App Router pages
        ├── components/            # React components
        └── lib/                   # API client & utilities
```

---

<p align="center">
  <b>Aria AI Marketing OS</b> — Otonom. Akilli. Turkce.
  <br/>
  <sub>Built with FastAPI, Next.js, Gemini 3.1 Pro & Claude 3.5 Sonnet</sub>
</p>
