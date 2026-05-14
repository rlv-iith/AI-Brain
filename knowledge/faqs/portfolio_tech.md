# Portfolio Technical FAQs

## What is this portfolio built with?
Microservices architecture:
- **Frontend** (04/): React 19 + Vite + Tailwind CSS + Framer Motion + Three.js (3D hero), deployed on Render
- **Backend** (03/): Node.js + Express, deployed on Render — handles visitor logging, analytics to Google Sheets, Discord webhooks
- **AI Brain** (05/): Python FastAPI + local Phi-3.5-Mini SLM + multi-provider LLM router — this service
- **Secrets**: Azure Key Vault
- **Analytics**: Google Sheets via service account

## What is the AI brain?
A local Small Language Model (Phi-3.5-Mini 3.8B) running on Lalith's laptop with an AirLLM-style layer-wise inference engine. Each transformer layer is loaded from disk one at a time — peak RAM stays under 1 GB despite the model being 7.5 GB total. A RAG layer retrieves relevant portfolio chunks before each generation.

## What is AirLLM-style inference?
Instead of loading all 32 transformer layers into RAM at once, only one layer is loaded at a time. After each layer's forward pass, it's freed from RAM. KV-cache (attention key/value states) is kept in RAM across layers for fast token generation. This lets the model run on devices with as little as 500 MB free RAM.

## What is MCP?
Model Context Protocol — a standard for connecting LLMs to external tools (Slack, Jira, GitHub, databases). Instead of each app building custom integrations, tools expose a standard interface and LLMs call them via MCP. Lalith built this infrastructure at Stremly.

## Why not just use GPT-4 or Claude?
The portfolio demonstrates that Lalith understands what's inside the black box. Running a local SLM with hand-rolled inference shows depth that calling an API does not.

## What is the multi-provider router?
The AI brain can route queries to multiple LLM providers (Groq, Gemini, Mistral, local SLM, home PC Ollama) and either race them (return fastest) or compete them (return best quality). Response times and quality scores are tracked per provider.
