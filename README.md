# Multilingual Voice Agent Orchestrator

FastAPI + React dashboard for an outbound multilingual voice-agent workflow: Vapi call placement and webhooks, lead qualification, callback scheduling, WhatsApp actions, and post-call follow-up.

## Requirements

- Python 3.10+
- Node.js 18+
- Vapi credentials for real outbound calls
- Meta WhatsApp Cloud API credentials (optional; required to deliver WhatsApp messages)

## Run the API

```bash
cd backend
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
# Edit .env, then:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Run the dashboard

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Set `VITE_API_URL` in `frontend/.env.local` if the API is not at `http://localhost:8000`.

## Vapi webhook setup

Expose port 8000 using a secure HTTPS tunnel for local testing, then configure the Vapi assistant server URL as `https://YOUR_PUBLIC_HOST/api/vapi/webhook`. Set the same `VAPI_SERVER_SECRET` on this service and in the assistant webhook configuration. The assistant must have `sendWhatsApp`, `bookCallback`, and `recordLead` function tools configured to use this webhook.

The outbound call button requires `VAPI_API_KEY`, `VAPI_ASSISTANT_ID`, and `VAPI_PHONE_NUMBER_ID`. WhatsApp business-initiated messages normally require an approved Meta template. Configure the template name and one body variable for the mid-call context. Never commit your `.env` file or API keys.

## Data

SQLite database is created at `backend/data/voice_agent.db` on first run. It stores qualified leads, callback bookings, and WhatsApp events.
