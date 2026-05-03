import time

from .settings import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_SECONDS


RATE_BUCKETS = {}


def get_client_ip(handler):
    forwarded_for = handler.headers.get("X-Forwarded-For")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return handler.client_address[0] if handler.client_address else "unknown"


def is_rate_limited(handler):
    now = time.time()
    client_ip = get_client_ip(handler)
    bucket = RATE_BUCKETS.get(client_ip)

    if not bucket or now > bucket["reset_at"]:
        RATE_BUCKETS[client_ip] = {"count": 1, "reset_at": now + RATE_LIMIT_WINDOW_SECONDS}
        return False

    bucket["count"] += 1
    return bucket["count"] > RATE_LIMIT_MAX
