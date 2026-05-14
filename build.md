# Portfolio Build Plan — Ramuni Lalith Vishnu
**Last updated: 2026-05-14**

---

## Scenario & Context

**Who:** Ramuni Lalith Vishnu (goes by Lalith), 3rd year B.Tech Industrial Chemistry
(Minor: Civil Eng), IIT Hyderabad (2023–2027). CGPA 7.99.
Targeting AI Engineering / Data Science placements.

**What this is:** A personal portfolio website with microservices architecture.
Not a simple static site — built to demonstrate systems thinking in interviews.
Each service is independently deployable. The architecture diagram *is* the interview answer.

**Current internship:** AI Systems Intern at Stremly (Dublin-based AI startup), Apr–Jun 2026.
Built MCP server infrastructure letting LLMs interact with Slack, Jira, and other tools.
This portfolio uses the same MCP pattern — built by someone who has shipped it in production.

---

## Deployed Links

| Service | URL | Repo (local) | Status |
|---------|-----|--------------|--------|
| Frontend | `https://portfolio-server-4-kg3z.onrender.com` | `Portfolio/04_git/portfolio-4` | ✅ Live |
| Backend  | `https://portfolio-server-3-ohjk.onrender.com` | `Portfolio/03` | ✅ Live |
| AI Brain | local only (port 8000) | `Portfolio/05` | 🔧 Running locally |

> Note: `03.1` is the local dev copy of the backend (has `.env` with secrets).
> `03` is the production copy connected to Render.
> Always edit in `03.1`, copy changed files to `03`, push from `03`.

---

## Tech Stack (CURRENT)

| Layer | Stack |
|-------|-------|
| Frontend | React 19 + Vite + Tailwind CSS + Framer Motion + Three.js (R3F) |
| Backend | Node.js + Express (deployed on Render) |
| AI Brain | **Python + FastAPI** — `05/` folder (changed from Node.js) |
| LLM local | Phi-3.5-Mini (AirLLM layer-wise inference, laptop only) |
| LLM cloud | Groq / Gemini / Mistral / OpenRouter / Cerebras / xAI / Anthropic (router) |
| LLM home PC | Ollama via Cloudflare Tunnel (not yet set up) |
| RAG | sentence-transformers (all-MiniLM-L6-v2) + numpy cosine similarity |
| Analytics store | Google Sheets (via service account) |
| Secrets | Azure Key Vault |
| Gallery images | `src/assets/gallery/` (auto-loaded via import.meta.glob) |

---

## Architecture (CURRENT)

```
         Browser
            │
            ▼
    ┌───────────────────┐
    │     Frontend      │  React 19 + Vite + Three.js
    │  (Render)         │  Hero: LALITH VISHNU R
    │                   │  Sections: Interact │ Gallery │ Extras
    └──────┬────────────┘
           │  POST /log   { role, token }
           │  POST /track { token, session_id, ... }
           │  POST /chat  { message, history, persona }  ← wired, AI Brain local only
           ▼
    ┌───────────────────┐        ┌──────────────────────┐
    │     Backend       │◄───────│   Azure Key Vault    │
    │     (Render)      │        │   (secrets)          │
    │   POST /log       │        └──────────────────────┘
    │   POST /track     │
    └──────┬────────────┘
           ├──► Google Sheets (Visits + Behavior tabs)
           └──► Discord Webhook

    ── AI Brain (LOCAL — port 8000) ─────────────────────
                                │
                     ┌──────────┴──────────────┐
                  RAG Pipeline            LLM Router
                  (knowledge/*.md)             │
                  sentence-transformers    ┌───┴────────────────────┐
                                          │                        │
                                      RACE / COMPETE           SINGLE
                                          │
                    ┌──────────┬──────────┼──────────┬──────────┐
                  Groq      Gemini    Mistral     xAI       Home PC
                 (fast)    (large    (free)    (Grok)    (Ollama via
                           context)                      Cloudflare)
                                          │
                                     Anthropic (fallback)
```

---

## File Map (CURRENT)

```
Portfolio/
├── 03/                          ← Backend repo (Render-connected)
│   ├── server.js
│   └── Index/index.html         ← redirect to new frontend
│
├── 03.1/                        ← Backend local dev (has .env)
│   ├── server.js                ← keep in sync with 03/
│   └── .env                     ← secrets (not committed)
│
├── 04_git/portfolio-4/          ← Frontend repo
│   ├── src/
│   │   ├── App.jsx
│   │   ├── analytics.js         ← SESSION_TOKEN, event queue
│   │   ├── hooks/useAnalytics.js
│   │   ├── context/RoleContext.jsx
│   │   ├── data/
│   │   │   ├── projectData.jsx  ← resume, experience, headers
│   │   │   ├── links.config.js  ← ✅ NEW: all external URLs in one file
│   │   │   └── gallery.config.js← ✅ NEW: photo metadata (event + project per image)
│   │   ├── assets/gallery/      ← ✅ NEW: drop photos here → auto-appear in gallery
│   │   │   ├── Build-2024_01.jpg
│   │   │   ├── Echem_Mat_Lab_04.jpg
│   │   │   ├── Inter-IIT.jpg
│   │   │   ├── Mitsubhishi Hacathon Prize money.jpg
│   │   │   ├── SIH.jpg
│   │   │   └── TL.jpg
│   │   ├── pages/
│   │   │   ├── Landing.jsx      ← hero + interact + gallery + extras
│   │   │   └── Recruiter.jsx    ← full recruiter dashboard
│   │   └── components/
│   │       ├── Hero3D.jsx
│   │       └── Footer.jsx
│   └── public/images/Profile.JPG
│
└── 05/                          ← AI Brain (Python + FastAPI)
    ├── server.py                ← FastAPI: /health /chat /competition
    ├── requirements.txt         ← torch==2.6.0, transformers, accelerate, etc.
    ├── .env                     ← local secrets (gitignored)
    ├── .env.example             ← template with all provider slots
    ├── .gitignore               ← excludes model_shards/, .env
    ├── brain/
    │   ├── engine.py            ← LayerWiseEngine (AirLLM-style Phi-3.5-Mini)
    │   ├── rag.py               ← RAG pipeline (retrieve + build_prompt)
    │   ├── knowledge_base.py    ← loads all knowledge/*.md files
    │   ├── providers.py         ← 8 async provider calls
    │   └── router.py            ← RACE / COMPETE / SINGLE routing logic
    ├── knowledge/               ← edit these → AI brain updates automatically
    │   ├── about.md
    │   ├── projects/            ← finshield, mitsubishi, ibm_rag, axidraw
    │   ├── experience/          ← stremly, iisc, iith_safety
    │   ├── achievements/        ← hackathons, academics, sports_clubs
    │   ├── skills/skills.md
    │   └── faqs/                ← general, portfolio_tech
    ├── model_shards/            ← gitignored; created by scripts/setup.py
    └── scripts/
        ├── setup.py             ← download + split Phi-3.5-Mini into layer shards
        └── home_pc_setup.md     ← Ollama + Cloudflare Tunnel guide
```

---

## Phase 1 — Frontend + Backend — ✅ COMPLETE

| Task | Status |
|------|--------|
| Frontend personas — TechLead, Catalyst, Dashboard deleted | ✅ |
| AI Systems Engineer positioning (pills, tagline, skills) | ✅ |
| Stremly internship in experience | ✅ |
| `.env` / `.env.production` with `VITE_BACKEND_URL` | ✅ |
| SEO meta tags, sitemap.xml | ✅ |
| Backend CORS + `POST /log` with geolocation + Sheets | ✅ |
| Backend `POST /track` — full behavioral analytics | ✅ |
| Discord webhook — blue visit + green behavior embeds | ✅ |
| Azure Key Vault with `.env` fallback | ✅ |
| `useAnalytics.js` — sections, scroll, cursor, idle, copy, return visitor | ✅ |
| Google Sheets Visits tab (11 cols) + Behavior tab (14 cols) | ✅ |

---

## Phase 2 — AI Brain — 🔧 IN PROGRESS (local, not deployed)

### What is done in 05/

| Task | Status |
|------|--------|
| Python FastAPI server (`server.py`) | ✅ |
| AirLLM-style `LayerWiseEngine` (Phi-3.5-Mini layer shards) | ✅ |
| `scripts/setup.py` — download + split model into layer files | ✅ |
| RAG pipeline with sentence-transformers + numpy | ✅ |
| Knowledge base as Markdown files (`knowledge/` tree) | ✅ |
| 8 async cloud providers: Groq, Gemini, Mistral, OpenRouter, Cerebras, xAI, Anthropic, Home PC | ✅ |
| LLM Router — RACE / COMPETE / SINGLE modes | ✅ |
| `/health`, `/chat`, `/competition` endpoints | ✅ |
| `links.config.js` — all external URLs in one file (frontend) | ✅ |
| `gallery.config.js` — photo metadata config (frontend) | ✅ |
| Photo gallery section — diamond collage, hover overlays (frontend) | ✅ |
| Enter key scroll bug fixed (preventDefault) | ✅ |
| Groq API key working (gsk_ prefix) | ✅ |
| xAI provider added (xai- prefix, separate from Groq) | ✅ |

### What is NOT done yet in 05/

| Task | Notes |
|------|-------|
| Local SLM model shards | Run `python scripts/setup.py` (downloads ~7.5 GB Phi-3.5-Mini) |
| Frontend chat wired to local AI Brain | Set `VITE_AI_BRAIN_URL=http://localhost:8000` in frontend `.env` |
| Home PC Ollama setup | See `scripts/home_pc_setup.md` |
| Deploy AI Brain to Render | Python service; needs `Procfile` or `render.yaml` |
| MCP Server | Still Phase 3 — not started |
| Docker Compose | Still Phase 3 |
| Streaming (SSE) | Currently returns full response; streaming not yet implemented |

---

## Next Steps (priority order)

### 1 — Wire frontend chat to local AI Brain
In `04_git/portfolio-4/.env`:
```
VITE_AI_BRAIN_URL=http://localhost:8000
```
The `ChatPanel` in `Landing.jsx` already reads `import.meta.env.VITE_AI_BRAIN_URL`
and calls `${aiUrl}/chat`. Just set the var and restart Vite.

### 2 — Run model setup (optional — cloud providers work without it)
```bash
cd Portfolio/05
python scripts/setup.py   # ~8 min, downloads Phi-3.5-Mini, splits into shards
```
Restart the server — it auto-detects shards and warms the local SLM.

### 3 — Home PC Ollama (optional, see scripts/home_pc_setup.md)
```bash
# On home PC:
ollama pull llama3.2
$env:OLLAMA_HOST="0.0.0.0:11434"; ollama serve
cloudflared tunnel --url http://localhost:11434
# Copy the trycloudflare.com URL → paste in 05/.env as HOME_PC_URL
```

### 4 — Deploy AI Brain to Render
Add `Procfile` to `05/`:
```
web: uvicorn server:app --host 0.0.0.0 --port $PORT
```
Push `05/` as a new Render service. Set all provider keys as env vars.
Model shards (7.5 GB) won't fit on Render free tier — use cloud providers only on Render.

### 5 — MCP Server (Phase 3)
- New repo: `portfolio-mcp`
- Tools: `search_projects`, `read_resume`, `get_visitor_stats`, `get_github_activity`
- Connect from `brain/router.py` before LLM call (tool context injection)

### 6 — Docker Compose (Phase 3)
```yaml
services:
  frontend:  { build: ./04_git/portfolio-4, ports: ["5173:5173"] }
  backend:   { build: ./03.1,               ports: ["3000:3000"] }
  ai-brain:  { build: ./05,                 ports: ["8000:8000"] }
```

---

## Running the stack locally

```bash
# Terminal 1 — Frontend
cd Portfolio/04_git/portfolio-4
npm run dev

# Terminal 2 — Backend
cd Portfolio/03.1
node server.js

# Terminal 3 — AI Brain
cd Portfolio/05
.venv\Scripts\activate
uvicorn server:app --reload --port 8000
```

Frontend env var needed to connect chat to brain:
```
VITE_AI_BRAIN_URL=http://localhost:8000
```

---

## Provider Key Status

| Provider | Key format | Where to get | Status |
|----------|-----------|--------------|--------|
| Groq | `gsk_...` | console.groq.com | ✅ working |
| xAI  | `xai-...` | console.x.ai | ✅ key exists, add to .env |
| Gemini | `AIza...` | aistudio.google.com/apikey | ⬜ not added |
| Mistral | `...` | console.mistral.ai | ⬜ not added |
| OpenRouter | `sk-or-...` | openrouter.ai | ⬜ not added |
| Cerebras | `...` | cloud.cerebras.ai | ⬜ not added |
| Anthropic | `sk-ant-...` | console.anthropic.com | ⬜ not added |
| Home PC | tunnel URL | Cloudflare | ⬜ not set up |

---

## Azure Key Vault — All Secrets

| Secret name | Used by |
|------------|---------|
| `GOOGLE-PRIVATE-KEY` | Backend, MCP |
| `GOOGLE-CLIENT-EMAIL` | Backend, MCP |
| `SHEET-ID` | Backend, MCP |
| `WEBHOOK-URL` | Backend (Discord) |
| `CLAUDE-API-KEY` | AI Brain fallback |
| `HOME-PC-TUNNEL-URL` | AI Brain home PC route |
| `GITHUB-TOKEN` | MCP (future) |

---

## Interview Talking Points

**"Why did you build this as microservices?"**
> Each service is independent — frontend can redeploy without touching analytics,
> AI brain can go down without breaking the portfolio.
> Same separation-of-concerns thinking I'd apply in a production system.
> Also lets me demo MCP server design, which is exactly what I built at Stremly.

**"What is the AI brain doing?"**
> It's a local Phi-3.5-Mini (3.8B parameters) running with AirLLM-style inference —
> each of the 32 transformer layers is loaded from disk one at a time, so the model
> fits in 500 MB of RAM despite being 7.5 GB. On top of that I added a RAG layer
> that retrieves the relevant chunks from my knowledge base before generating —
> so it doesn't hallucinate my experience.

**"What is the LLM router?"**
> It fires all available providers (Groq, Gemini, Mistral, local SLM, home PC Ollama)
> concurrently in RACE mode and returns whichever responds first.
> In COMPETE mode it collects all responses, logs latency and length per provider,
> and returns the best one. The `/competition` endpoint shows the full comparison.
> It degrades gracefully — if home PC is offline, cloud kicks in automatically.

**"What does AirLLM-style mean?"**
> Instead of loading all 32 transformer layers into RAM simultaneously (7.5 GB),
> I split the model into 34 separate files on disk. During inference, one layer
> is loaded, the forward pass runs, then it's freed. KV-cache (attention state)
> stays in RAM across layers. Peak RAM during inference is around 500 MB.
> This lets the model run on any laptop, not just ones with 16 GB+ free RAM.
