# Portfolio v5 — Design Doc
**Last updated: 2026-05-14**

Two pages. One active persona at deploy time. No routing library — context switch.

**Repos:**
- Frontend → `04_git/portfolio-4` (React + Vite)
- Backend  → `03.1` (Node + Express)
- AI Brain → `05/` (Python + FastAPI)

**Personas:**
| Card | Status |
|------|--------|
| Recruiter | ✅ deployed, only active card |
| Professor | `// commented out` — one line to re-enable |
| Tech Lead | deleted |
| Catalyst  | deleted |

---

## Page 1 — Landing (CURRENT STATE)

**Hero name:** `LALITH VISHNU R`
**Subtitle line:** `College Student · IIT Hyderabad` ← TODO: add this below the name
**Status badge:** `● Available for Internships` (green pulse) ← TODO: add this

**Current section order:**
```
┌─────────────────────────────────────────────────────────┐
│  SECTION 1 — HERO  (full screen, 3D background)         │
│                                                          │
│   System Online • v4.0                                   │
│   LALITH VISHNU R                                        │
│   [ AI Systems Engineer ] [ IIT Hyderabad ]             │
│                                                          │
│   LEFT PANEL          CENTER (3D)      RIGHT PANEL       │
│   ┌────────────┐      (passthrough)   ┌────────────┐    │
│   │ Who Am I   │                      │ Highlights │    │
│   │            │                      │            │    │
│   │ B.Tech     │                      │ Achievements    │
│   │ IIT-H      │                      │            │    │
│   │ Targeting  │                      ├────────────┤    │
│   │ Stack      │                      │ RECRUITER  │    │
│   └────────────┘                      │ CARD →     │    │
│                                       └────────────┘    │
│   ─── bottom bar ─────────────────────────────────      │
│   GitHub | LinkedIn | email                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SECTION 2 — INTERACT                                    │
│                                                          │
│   ┌──────────────────────┐  ┌──────────────────────┐   │
│   │  Who are you?        │  │  Ask about me        │   │
│   │  (visitor form)      │  │  (AI chat panel)     │   │
│   │                      │  │                      │   │
│   │  Name                │  │  Suggested prompts   │   │
│   │  Role                │  │  Message thread      │   │
│   │  Company             │  │  Input + Send        │   │
│   │  Purpose             │  │                      │   │
│   │  Feedback            │  │  → POST /chat        │   │
│   │  [SUBMIT_]           │  │    to AI Brain       │   │
│   └──────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SECTION 3 — GALLERY  ← NEW                             │
│                                                          │
│  Diamond collage layout:  rows [1, 3, 5, 5, 3, 1]      │
│  = 18 images max                                         │
│                                                          │
│        [ img ]                                           │
│     [ img ][ img ][ img ]                               │
│  [ img ][ img ][ img ][ img ][ img ]                    │
│  [ img ][ img ][ img ][ img ][ img ]                    │
│     [ img ][ img ][ img ]                               │
│        [ img ]                                           │
│                                                          │
│  Hover any photo → overlay shows:                       │
│    project name (color-coded by category)               │
│    event/occasion name                                   │
│                                                          │
│  Image size: 220×147 px  Gap: 6 px                      │
│  Overflow-x scroll on mobile                            │
│  [ View all on GitHub ] pill link below                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SECTION 4 — OPERATIONAL EXTRAS                          │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  NSS     │  │  NCC     │  │  Karate  │              │
│  │ 100+ hrs │  │ Cadet    │  │ Shodan   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘

[ FOOTER ]
```

---

## Pending UI TODOs (frontend)

| Item | Where | Notes |
|------|-------|-------|
| "Available for Internships" green badge | Hero, below name | green pulse dot + border |
| "College Student · IITH" subtitle | Hero, below name | small gray mono text |
| Wire `VITE_AI_BRAIN_URL` | `.env` | set to `http://localhost:8000` to enable chat |
| Mobile: disable Three.js Hero3D | `Landing.jsx` | WebGL kills mobile battery |
| Mobile: fix contact line | `Landing.jsx` | currently buried on small screens |

---

## Gallery Config (how to add photos)

**Step 1** — Drop image into:
```
04_git/portfolio-4/src/assets/gallery/
```

**Step 2** — Add entry in `gallery.config.js`:
```js
"your-filename.jpg": {
  event:    "What happened / occasion",
  project:  "Which internship / project / club",
  category: "text-yellow-400",  // color for project label
},
```

**Color guide:**
- `text-yellow-400` — hackathons / awards
- `text-blue-400`   — internships / research
- `text-emerald-400`— projects / labs
- `text-purple-400` — clubs / tech work
- `text-rose-400`   — community / sports
- `text-white`      — karate / personal

**Current photos (6):**
| File | Event | Project |
|------|-------|---------|
| `Build-2024_01.jpg` | BUILD-2024 Incubator Presentation | Tinkerers' Lab |
| `Echem_Mat_Lab_04.jpg` | Micro-Supercapacitor Fabrication | ElectroChem Research |
| `Inter-IIT.jpg` | Inter-IIT Tech Meet | IIT Hyderabad Contingent |
| `Mitsubhishi Hacathon Prize money.jpg` | Cash Prize Ceremony | Mitsubishi Hackathon 2024 |
| `SIH.jpg` | Smart India Hackathon | National Hackathon |
| `TL.jpg` | Team Photo | Tinkerers' Lab |

---

## Links Config (how to update any URL)

All external URLs live in one file:
```
04_git/portfolio-4/src/data/links.config.js
```

| Key | What it controls |
|-----|-----------------|
| `LINKS.social.github` | Hero footer, gallery "View all" button |
| `LINKS.social.linkedin` | Hero footer |
| `LINKS.social.email` | Hero footer |
| `LINKS.resume` | Set a Google Drive URL here to add resume download |
| `LINKS.projects["id"].github` | Per-project GitHub link (used in project cards if re-enabled) |
| `LINKS.projects["id"].demo` | Per-project live demo link |
| `LINKS.services.frontend` | Deployed frontend URL |
| `LINKS.services.backend` | Deployed backend URL |
| `LINKS.services.aiBrain` | Set when AI Brain is deployed to Render |

---

## AI Brain UI Connection

The `ChatPanel` in `Landing.jsx` already has the full wiring:
```js
const aiUrl = import.meta.env.VITE_AI_BRAIN_URL;
// if aiUrl is empty → shows "AI Brain not connected yet — coming soon!"
// if aiUrl is set → POST ${aiUrl}/chat with { message, history, persona }
```

To enable locally:
1. Add to `04_git/portfolio-4/.env`:
   ```
   VITE_AI_BRAIN_URL=http://localhost:8000
   ```
2. Make sure AI Brain is running: `uvicorn server:app --reload --port 8000`
3. Restart Vite dev server

Response shape the frontend expects:
```json
{ "reply": "string" }
```
The current server returns `{ reply, provider, latency_ms, competition }` — the frontend only reads `reply`, the rest is ignored (available for debugging).

---

## AI Brain Architecture

```
POST /chat  { message, history, persona }
        │
        ▼
   RAGPipeline.build_prompt()
        │  embeds query with all-MiniLM-L6-v2
        │  retrieves top-4 chunks from knowledge/
        │  builds messages[] with system + context + history
        ▼
   router.route(messages)
        │
        ├── RACE mode (default):
        │     fire all active providers concurrently
        │     return first successful response
        │
        ├── COMPETE mode:
        │     fire all, collect all
        │     log latency + length per provider
        │     return longest reply
        │     view full results at GET /competition
        │
        └── SINGLE mode:
              local SLM first → then cloud in order
```

**Knowledge base is just Markdown files:**
```
05/knowledge/
├── about.md              ← edit to change bio
├── projects/             ← one file per project
├── experience/           ← one file per role
├── achievements/         ← hackathons, academics, sports
├── skills/skills.md      ← tech stack details
└── faqs/                 ← general + portfolio tech FAQs
```
Add or edit any `.md` file → restart the brain server → RAG index rebuilds.

---

## Tech Decisions

| Decision | Reason |
|----------|--------|
| Python for AI Brain (changed from Node) | torch/transformers/accelerate ecosystem is Python-native |
| Phi-3.5-Mini over larger models | 3.8B fits in 20 GB RAM; strong instruction following |
| AirLLM-style layer shards | Interview talking point; keeps peak RAM ~500 MB |
| sentence-transformers for RAG | 80 MB, no API key, runs offline |
| numpy cosine sim over FAISS | No C++ dependency; 11 chunks is tiny, numpy is fast enough |
| RACE mode as default router | Fastest UX; providers have similar quality for short Q&A |
| COMPETE mode for logging | Shows provider comparison — useful for choosing best provider |
| Markdown knowledge base | Non-technical to edit; no DB; git-versioned |
| links.config.js | Single file to update all URLs — no hunting through components |
| gallery.config.js + import.meta.glob | Drop image + add 4 lines → appears in gallery automatically |

---

## Build Order from here

1. ✅ AI Brain running locally with Groq
2. ⬜ Wire frontend chat → AI Brain (`VITE_AI_BRAIN_URL`)
3. ⬜ Add "Available for Internships" badge to hero
4. ⬜ Run `python scripts/setup.py` to enable local Phi-3.5-Mini
5. ⬜ Home PC Ollama via Cloudflare Tunnel
6. ⬜ Deploy AI Brain to Render (cloud-only mode, no model shards)
7. ⬜ MCP Server (Phase 3)
8. ⬜ Docker Compose (Phase 3)
