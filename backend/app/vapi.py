import os
import httpx


async def place_call(to: str):
    api_key = os.getenv("VAPI_API_KEY")
    assistant_id = os.getenv("VAPI_ASSISTANT_ID")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    if not all((api_key, assistant_id, phone_number_id)):
        raise RuntimeError("Set VAPI_API_KEY, VAPI_ASSISTANT_ID and VAPI_PHONE_NUMBER_ID")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.vapi.ai/call",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "assistantId": assistant_id,
                "phoneNumberId": phone_number_id,
                "customer": {"number": to, "name": os.getenv("LEAD_NAME") or None},
            },
        )
        response.raise_for_status()
        return response.json()
