# Smart Migrant Labor Welfare & Skill Mapping Platform
## Version 1

An AI-powered platform helping interstate migrant workers in Gujarat access welfare schemes,
fair wage information, safe working conditions, and grievance reporting.

---

## Architecture

```
Frontend (HTML/JS/CSS — trilingual: English, Hindi, Gujarati)
    ↓
Python Backend/API (FastAPI)
    ↓
Main Coordinator Agent (watsonx Orchestrate)
    ↓
Specialized Agents (watsonx Orchestrate)
    ↓
Central Knowledge Base (watsonx Orchestrate)
    ↓
Shared Cloud Database (PostgreSQL) / Cloud Object Storage
```

---

## Version 1 Scope

1. Worker Profile
2. Skill & Location Mapping
3. Welfare Scheme Eligibility
4. Welfare Application Guidance
5. Wage Fairness Monitoring
6. Safety & Grievance Reporting
7. Worker Dashboard
8. Admin Dashboard
9. Government/Labor Officer Dashboard
10. Main Coordinator Agent
11. Five Specialized Agents
12. Shared Cloud Database
13. Central Knowledge Base
14. Document/evidence storage
15. Authentication (Mobile OTP)
16. Notifications (in-app + SMS)
17. Audit/activity logging
18. Backup and recovery
19. English, Hindi, Gujarati support

**Not in Version 1:** Job Matching (future feature)

---

## Project Structure

```
/agents          — watsonx Orchestrate agent definitions (YAML)
/backend         — Python FastAPI backend
/frontend        — Web application (HTML/CSS/JS)
/knowledge       — Knowledge base content and update scripts
/database        — Schema, migrations, seeds
/storage         — Document/evidence storage config
/config          — Environment and service configuration
/tests           — Agent, API, integration, knowledge tests
/tools           — watsonx Orchestrate tool definitions
/docs            — Technical documentation
```

---

## Agents

| Agent | Role |
|---|---|
| `main-coordinator` | Routes all worker requests to the right specialized agent |
| `skill-location-agent` | Manages worker profiles, skills, location |
| `welfare-scheme-agent` | Eligibility checking, application guidance |
| `wage-fairness-agent` | Wage comparison against verified references |
| `safety-grievance-agent` | Complaint intake, evidence, status tracking |
| `labor-welfare-dashboard-agent` | Worker / Admin / Officer dashboards |

---

## Technology

- **AI Platform**: IBM watsonx Orchestrate (jp-tok)
- **AI Models**: IBM Granite / watsonx-orchestrate/frontier
- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL (IBM Cloud Databases)
- **Storage**: IBM Cloud Object Storage
- **Auth**: Mobile OTP (role-based: Worker / Admin / Officer)
- **Languages**: English, Hindi, Gujarati

---

## Setup

See `docs/setup.md` for full setup instructions.

---

## Development Phase

Current: **Version 1 — Build**
Environment: **Draft (jp-tok)**
