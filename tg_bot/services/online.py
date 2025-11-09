from datetime import datetime, timedelta
from ..db import query_one

def detect_online_table() -> str | None:
    # TODO: real detection if needed
    return "tg_online"

def get_online_status_by_uuid(player_uuid: str) -> tuple[str, str]:
    tbl = detect_online_table()
    if not tbl:
        return "unknown", "table not found"

    row = query_one(f"SELECT * FROM {tbl} WHERE uuid=%s", (player_uuid,))
    if not row:
        return "unknown", "player not found"

    if "online" in row:
        state = "online" if int(row["online"]) == 1 else "offline"
        return state, f"src: {tbl}.online"

    if "last_seen" in row and row["last_seen"]:
        try:
            last_seen = row["last_seen"]
            if isinstance(last_seen, str):
                last_seen = datetime.fromisoformat(last_seen)
            is_online = (datetime.utcnow() - last_seen.replace(tzinfo=None)) < timedelta(seconds=120)
            return ("online" if is_online else "offline"), f"src: {tbl}.last_seen"
        except Exception:
            return "unknown", f"cannot parse {tbl

}.last_seen"

    return "unknown", f"{tbl}: no fields"
