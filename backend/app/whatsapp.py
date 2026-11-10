import os
import httpx


def _digits(phone: str) -> str:
    return "".join(character for character in (phone or "") if character.isdigit())


async def _meta_send(payload: dict):
    phone_id = os.getenv("META_PHONE_NUMBER_ID")
    token = os.getenv("META_WABA_TOKEN")
    if not phone_id or not token:
        raise RuntimeError("Meta WhatsApp credentials are not configured")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"https://graph.facebook.com/v21.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"messaging_product": "whatsapp", "recipient_type": "individual", **payload},
        )
        response.raise_for_status()
        return response.json()


async def send_text(to: str, text: str):
    return await _meta_send({"to": _digits(to), "type": "text", "text": {"body": text, "preview_url": False}})


async def send_template(to: str, context: str):
    name = os.getenv("META_TEMPLATE_NAME")
    if not name:
        raise RuntimeError("META_TEMPLATE_NAME is not configured")
    return await _meta_send({
        "to": _digits(to),
        "type": "template",
        "template": {
            "name": name,
            "language": {"code": os.getenv("META_TEMPLATE_LANG", "en")},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": context}]}],
        },
    })


async def send_media(to: str, link: str, kind: str, caption: str = "", filename: str | None = None):
    if not link:
        return None
    media = {"link": link, "caption": caption}
    if kind == "document" and filename:
        media["filename"] = filename
    return await _meta_send({"to": _digits(to), "type": kind, kind: media})
