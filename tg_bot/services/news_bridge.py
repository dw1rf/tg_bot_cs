import logging
import requests
from ..config import DISCORD_WEBHOOK_URL

def forward_to_discord(text: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        logging.warning("[NEWS] DISCORD_WEBHOOK_URL not set")
        return
    try:
        payload = {"content": (text or "")[:2000]}
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if r.status_code // 100 != 2:
            logging.warning(f"[NEWS] Discord responded {r.status_code}: {r.text}")
    except Exception as e:
        logging.exception(f"[NEWS] send error: {e}")
