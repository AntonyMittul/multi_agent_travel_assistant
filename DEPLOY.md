# Deploying Navora to Render (free tier)

The repo ships a `render.yaml` Blueprint that creates **both** services:
- `navora-api` — the FastAPI + LangGraph backend (Python web service)
- `navora-web` — the React frontend (static site)

The frontend's API URL is wired automatically (Render injects the backend host).

## Steps

1. **Push** the latest code to GitHub (already done if you've been pulling).
2. Go to <https://dashboard.render.com> → sign up / log in (free).
3. **New → Blueprint** → connect your GitHub and pick
   `AntonyMittul/multi_agent_travel_assistant`.
4. Render reads `render.yaml` and shows both services. Click **Apply**.
5. On the **navora-api** service, open **Environment** and set the secrets
   (these are marked `sync: false`, so Render asks for them):
   - `GOOGLE_API_KEY` — your Gemini key
   - `OPENCAGE_API_KEY` — your OpenCage key
   - `AVIATIONSTACK_API_KEY` — optional
6. Deploy. First build takes a few minutes (installs Python deps).
7. Open the **navora-web** URL (e.g. `https://navora-web.onrender.com`) — that's
   your live app.

## Notes

- **Free tier cold start:** `navora-api` sleeps after ~15 min idle; the first
  request then takes ~30–60s while it wakes. The static frontend is always on.
  (Tip: the very first plan after idle will be slow — that's the wake-up.)
- **CORS** is open (`*`) so the static site can call the API across origins.
- **Keys live only on the backend.** The frontend never sees them.
- To change the Gemini model, edit `GEMINI_MODEL` on `navora-api`.
- **Local dev is unchanged:** `VITE_API_BASE` is empty locally, so Vite proxies
  `/api` → `http://localhost:8000`.

## If a service URL name is taken

Render service names are global. If `navora-api`/`navora-web` are unavailable,
Render will suffix them — the `fromService` wiring still resolves automatically,
so no manual change is needed.
