# Home PC Setup — Ollama via Cloudflare Tunnel

Run this on your **home desktop / gaming PC** to expose a local Ollama server
to the internet so the AI brain on your laptop (or on Render) can call it.

---

## Step 1 — Install Ollama
```
https://ollama.com/download
```
Pull the model you want:
```bash
ollama pull llama3.2
# or
ollama pull phi3.5
ollama pull mistral
```

## Step 2 — Start Ollama (bind to all interfaces)
```bash
# Windows PowerShell
$env:OLLAMA_HOST = "0.0.0.0:11434"
ollama serve
```

## Step 3 — Expose via Cloudflare Tunnel (no account needed, temporary URL)
```bash
# Download cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared tunnel --url http://localhost:11434
```
It will print something like:
```
https://random-words-123.trycloudflare.com
```
Copy that URL.

## Step 4 — Set in .env on your laptop
```env
HOME_PC_URL=https://random-words-123.trycloudflare.com
HOME_PC_MODEL=llama3.2
```
Then add `home_pc` to `ACTIVE_PROVIDERS`.

## Notes
- The free Cloudflare Tunnel URL changes every time you restart cloudflared.
  For a persistent URL, sign up for a free Cloudflare account and use a named tunnel.
- If home PC is off, the `home_pc` provider simply fails and the router falls
  back to cloud providers automatically.
- For a permanent setup, run cloudflared as a Windows service:
  ```
  cloudflared service install
  ```
