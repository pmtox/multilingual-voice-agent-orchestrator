import os
import httpx
from .whatsapp import send_media, send_text


def transcript_text(transcript) -> str:
    if isinstance(transcript, str):
        return transcript
    if isinstance(transcript, list):
        return "\n".join(
            f"{item.get('role', item.get('speaker', '?'))}: {item.get('message', item.get('text', ''))}"
            for item in transcript if isinstance(item, dict)
        )
    return ""


def template_followup(lead: dict | None) -> str:
    lead = lead or {}
    applicant = os.getenv("APPLICANT_NAME", "ElevateBox")
    details = [f"{label}: {lead[key]}" for key, label in (
        ("products", "products"), ("budget", "budget"),
        ("timeline", "timeline"), ("features", "must-haves"),
    ) if lead.get(key)]
    context = ", ".join(details) or lead.get("summary") or "the e-commerce build we discussed"
    return (
        f"Hi, this is {applicant} from ElevateBox. Thanks for speaking with us.\n\n"
        f"Quick recap: {context}. I'd love to scope this properly.\n\n"
        f"Call me back: {os.getenv('APPLICANT_PHONE', '')}\n"
        "I’m sharing the resume and architecture overview separately."
    )


async def llm_followup(transcript: str, lead: dict | None):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    prompt = (
        f"Write a warm WhatsApp follow-up under 110 words as {os.getenv('APPLICANT_NAME', 'the applicant')} "
        "after a sales call about an e-commerce website. Use only actual details from the transcript. "
        f"Include callback number {os.getenv('APPLICANT_PHONE', '')} and mention attachments.\n"
        f"Transcript:\n{transcript[:6000]}\nKnown lead details: {lead or {}}"
    )
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                f"{os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "temperature": 0.5,
                      "messages": [{"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None


async def send_followup(call_id: str, phone: str, transcript, lead: dict | None):
    text = await llm_followup(transcript_text(transcript), lead) or template_followup(lead)
    try:
        await send_text(phone, text)
    except Exception:
        pass
    image_url = os.getenv("ARCHITECTURE_IMAGE_URL")
    if image_url:
        try:
            await send_media(phone, image_url, "image", "How the voice agent qualifies, acts and follows up.")
        except Exception:
            pass
    resume_url = os.getenv("RESUME_URL")
    if resume_url:
        try:
            filename = f"{os.getenv('APPLICANT_NAME', 'applicant').replace(' ', '_')}_resume.pdf"
            await send_media(phone, resume_url, "document", "Resume", filename)
        except Exception:
            pass
