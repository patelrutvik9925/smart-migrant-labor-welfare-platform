# Setup Guide — Smart Migrant Labor Welfare & Skill Mapping Platform

## Version 1

---

## 1. Prerequisites

- Python 3.12+
- PostgreSQL (IBM Cloud Databases for PostgreSQL recommended)
- IBM Cloud account with:
  - watsonx Orchestrate instance (jp-tok region, ID: 4a57643b-32dd-41ac-845f-73f4381e580e)
  - IBM Cloud Object Storage instance
- IBM Cloud API key with Manager role on the WXO instance

---

## 2. Agents Already Deployed (IBM Cloud — jp-tok)

The following agents are live in watsonx Orchestrate:

| Agent | Name in Orchestrate | Role |
|---|---|---|
| Main Coordinator | `migrant_welfare_coordinator` | Routes all worker requests |
| Skill & Location | `skill_location_agent` | Worker profile, skills, location |
| Welfare Schemes | `welfare_scheme_agent` | Eligibility checks, guidance |
| Wage Fairness | `wage_fairness_agent` | Wage comparison |
| Safety & Grievance | `safety_grievance_agent` | Complaints, evidence |
| Dashboard | `labor_welfare_dashboard_agent` | Worker/Admin/Officer dashboards |

---

## 3. Environment Setup

### 3.1 Copy environment config
```powershell
Copy-Item config\environments\draft.env.example .env
```

Edit `.env` and fill in:
- `WXO_API_KEY` — your IBM Cloud API key
- `DB_HOST`, `DB_USER`, `DB_PASSWORD` — PostgreSQL connection
- `COS_ENDPOINT`, `COS_API_KEY`, `COS_INSTANCE_CRN` — IBM COS
- `JWT_SECRET` — a random 64-character string

### 3.2 Install backend dependencies
```powershell
venv\Scripts\pip.exe install -r backend\requirements.txt
```

---

## 4. Database Setup

### 4.1 Create database
```sql
CREATE DATABASE migrant_welfare_db;
```

### 4.2 Run schema
```powershell
psql -h YOUR_HOST -U YOUR_USER -d migrant_welfare_db -f database/schema/v1_schema.sql
```

---

## 5. Run Backend (Development)

```powershell
$env:PYTHONPATH="."
venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: http://localhost:8000/api/docs

---

## 6. Run Frontend (Development)

Open `frontend/public/index.html` directly in a browser, or serve with:

```powershell
python -m http.server 8080 --directory frontend/public
```

Access at: http://localhost:8080

---

## 7. Test Agents

Run knowledge validation:
```powershell
venv\Scripts\python.exe tests/knowledge/test_knowledge_seeds.py
```

Run integration test plan:
```powershell
venv\Scripts\python.exe tests/integration/test_coordinator_workflows.py
```

Test coordinator live via MCP:
- Use Bob chat: "Chat with `migrant_welfare_coordinator`"
- Or via the watsonx Orchestrate UI

---

## 8. IBM Cloud Resources Required

| Resource | Purpose | Notes |
|---|---|---|
| watsonx Orchestrate | AI agents | Already active (jp-tok) |
| IBM Cloud Databases for PostgreSQL | Worker/complaint data | Provision separately |
| IBM Cloud Object Storage | Documents/evidence | Provision separately |
| SMS provider (e.g. MSG91) | OTP/alerts | Optional for draft |

---

## 9. Project Structure

```
agents/          — watsonx Orchestrate agent YAML definitions
backend/         — Python FastAPI backend
  main.py        — App entry point
  api/routes/    — API endpoints (auth, worker, welfare, wage, grievance, dashboard)
  auth/          — JWT authentication
  database/      — Models, connection, migrations
  services/      — Orchestrate client, document extraction
  storage/       — IBM COS client
  notifications/ — SMS + in-app
  audit/         — Structured logging
  utils/         — Config (settings from .env)
frontend/public/ — Web application (HTML/CSS/JS)
  index.html     — Single-page app
  css/style.css  — Styles
  js/i18n.js     — Translations (English/Hindi/Gujarati)
  js/api.js      — Backend API client
  js/app.js      — Navigation and logic
knowledge/       — Knowledge base content and seeds
  seeds/         — Verified official government knowledge
database/schema/ — PostgreSQL schema SQL
config/          — Environment config examples
tests/           — Agent, integration, knowledge tests
docs/            — Documentation
```

---

## 10. Version 1 Status

| Component | Status |
|---|---|
| Environment (jp-tok cloud) | ✅ Active |
| Main Coordinator Agent | ✅ Deployed & Tested |
| Skill & Location Agent | ✅ Deployed |
| Welfare Scheme Agent | ✅ Deployed |
| Wage Fairness Agent | ✅ Deployed |
| Safety & Grievance Agent | ✅ Deployed |
| Labor Welfare Dashboard Agent | ✅ Deployed |
| Project structure | ✅ Complete |
| Database schema | ✅ Complete |
| Backend (FastAPI) | ✅ Code complete — needs DB connection |
| Frontend (Trilingual) | ✅ Complete |
| Knowledge seeds (9 records) | ✅ Validated |
| Auth (Mobile OTP + JWT) | ✅ Implemented |
| Audit logging | ✅ Implemented |
| IBM COS integration | ✅ Implemented (needs credentials) |
| SMS notifications | ✅ Implemented (draft mode logs only) |
| Tests | ✅ Knowledge validated; agents tested live |
| **Pending — user action** | PostgreSQL + COS credentials in .env |
