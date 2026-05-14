# AI Systems Intern — Stremly (AI Startup)

**Duration:** Apr 2026 – Jun 2026  
**Location:** Dublin, Ireland (remote)  
**Type:** Industry internship

## About Stremly
Stremly is a Dublin-based AI startup building tools that connect LLMs to enterprise software. Lalith joined as their AI Systems Intern during a critical build phase.

## What Lalith built
- **MCP server infrastructure** — lets LLMs interact with external tools (Slack, Jira, GitHub) using the Model Context Protocol standard. This is the same pattern used by Claude Desktop and Cursor.
- **Redis-based health monitoring** — tracks service uptime and request latency across the MCP layer
- **HMAC authentication** — secures communication between the LLM orchestrator and tool servers, preventing spoofing
- **Async request handling** — designed to manage concurrent tool calls without race conditions using Python asyncio

## Why it matters for the portfolio
This portfolio's own chat panel uses the MCP pattern — built by someone who has shipped it in production at a startup. The architecture here is not academic; it's the same approach at a smaller scale.
