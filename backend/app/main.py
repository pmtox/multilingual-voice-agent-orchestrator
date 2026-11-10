import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import connect, fetch_all, fetch_one, init_db
from .followup import send_followup
from .scheduler import display_when, parse_when
from .vapi import place_call
from .whatsapp import send_template, send_text

TZ = ZoneInfo("Asia/Kolkata")
app = FastAPI(title="Multilingual Voice Agent Orchestrator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Vapi-Secret"],
)


@app.on_event("startup")
def startup():
    init_db()


class CallRequest(BaseModel):
    to: str = Field(min_length=5, max_length=30)


def now_iso():
    return datetime.now(TZ).isoformat()


def verify_secret(request: Request, payload: dict):
    expected = os.getenv("VAPI_SERVER_SECRET")
    if expected:
        message = payload.get("message") or {}
        supplied = request.headers.get("x-vapi-secret") or message.get("secret")
        if supplied != expected:
            raise HTTPException(status_code=401, detail="Invalid Vapi webhook secret")


def normalize_tool_calls(message: dict):
    calls = message.get("toolCallList") or message.get("toolCalls") or []
    for item in calls:
        function = item.get("function") or {}
        args = item.get("arguments", function.get("arguments", {}))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        yield {
            "id": item.get("id") or item.get("toolCallId"),
            "name": item.get("name") or function.get("name"),
            "args": args if isinstance(args, dict) else {},
        }


async def handle_tool(name: str, args: dict, call_id: str, phone: str):
    if name == "sendWhatsApp":
        context = args.get("context") or "Following up about your e-commerce store."
        try:
            await send_template(phone, context)
        except Exception:
            await send_text(phone, f"ElevateBox: {context}. I'll follow up with the details shortly.")
        with connect() as db:
            db.execute(
                "INSERT INTO whatsapp_events (call_id,kind,context,created_at) VALUES (?,?,?,?)",
                (call_id, "midcall_hot", context, now_iso()),
            )
        return "WhatsApp sent to the prospect."

    if name == "bookCallback":
        when_text = args.get("when_text", "")
        scheduled = parse_when(when_text)
        if not scheduled:
            return f'Could not parse a time from "{when_text}". Ask them for a day and time.'
        display = display_when(scheduled)
        with connect() as db:
            db.execute(
                """INSERT INTO callbacks
                (call_id,phone,when_text,at,display,tier,note,booked_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (call_id, phone, when_text, scheduled.isoformat(), display,
                 args.get("tier"), args.get("note"), now_iso()),
            )
        return f"Callback booked for {display}."

    if name == "recordLead":
        tier = str(args.get("tier") or "cold").lower()
        if tier not in {"hot", "warm", "cold"}:
            tier = "cold"
        field_values = [args.get(field) for field in
                  ("budget", "products", "timeline", "features", "barrier", "summary")]
        with connect() as db:
            db.execute(
                """INSERT INTO leads
                (call_id,phone,tier,budget,products,timeline,features,barrier,summary,recorded_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(call_id) DO UPDATE SET phone=excluded.phone,tier=excluded.tier,
                budget=excluded.budget,products=excluded.products,timeline=excluded.timeline,
                features=excluded.features,barrier=excluded.barrier,summary=excluded.summary,
                recorded_at=excluded.recorded_at""",
                (call_id, phone, tier, *field_values, now_iso()),
            )
        return f"Lead recorded as {tier}."

    return f"Unknown tool: {name}"


@app.get("/health")
def health():
    return {"ok": True, "timestamp": now_iso()}


@app.post("/api/call")
async def trigger_call(body: CallRequest):
    try:
        call = await place_call(body.to)
        return {"ok": True, "callId": call.get("id"), "to": body.to}
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/vapi/webhook")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    verify_secret(request, payload)
    message = payload.get("message") or {}
    call = message.get("call") or payload.get("call") or {}
    customer = call.get("customer") or message.get("customer") or {}
    call_id = call.get("id") or "unknown"
    phone = customer.get("number") or os.getenv("LEAD_PHONE", "")

    if message.get("type") == "tool-calls":
        results = []
        for tool in normalize_tool_calls(message):
            try:
                result = await handle_tool(tool["name"], tool["args"], call_id, phone)
            except Exception as error:
                result = f"The {tool['name']} step failed. Continue the call naturally."
                print(f"Tool {tool['name']} failed: {error}")
            results.append({"toolCallId": tool["id"], "result": result})
        return {"results": results}

    if message.get("type") == "end-of-call-report":
        transcript = (message.get("artifact") or {}).get("messages") or message.get("messages") or message.get("transcript") or []
        lead = fetch_one("SELECT * FROM leads WHERE call_id = ?", (call_id,))
        if phone:
            background_tasks.add_task(send_followup, call_id, phone, transcript, lead)
    return {"ok": True}


@app.get("/api/leads")
def get_leads():
    return fetch_all("SELECT * FROM leads ORDER BY recorded_at DESC")


@app.get("/api/callbacks")
def get_callbacks():
    return fetch_all("SELECT * FROM callbacks ORDER BY at ASC")


@app.get("/api/whatsapp-events")
def get_whatsapp_events():
    return fetch_all("SELECT * FROM whatsapp_events ORDER BY created_at DESC")
