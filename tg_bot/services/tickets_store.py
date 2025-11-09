# Память тикетов (как у тебя)
tickets: dict[str, dict] = {}
user_last_ticket: dict[int, str] = {}
pending_reason: dict[int, bool] = {}
thread_to_ticket: dict[int, str] = {}
ticket_to_thread: dict[str, int] = {}

def get_open_ticket_id(uid: int) -> str | None:
    tid = user_last_ticket.get(uid)
    if not tid:
        return None
    if tid in tickets:
        return tid
    user_last_ticket.pop(uid, None)
    return None
