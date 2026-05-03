import os

from .common import assistant_text, env_int, post_json


def call_xiaomi_chat(api_key, model, messages, options, ssl_context):
    request_body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_completion_tokens": env_int("MIMO_MAX_COMPLETION_TOKENS", 20480),
        "temperature": 0.7,
        "top_p": 0.95,
    }

    if options.get("thinking"):
        request_body["thinking"] = {"type": "enabled"}

    if options.get("web_search"):
        request_body["tools"] = [{"type": "web_search"}]
        request_body["tool_choice"] = "auto"

    data = post_json(
        os.getenv("MIMO_API_URL") or "https://api.xiaomimimo.com/v1/chat/completions",
        request_body,
        {"api-key": api_key, "Authorization": f"Bearer {api_key}"},
        env_int("MIMO_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return assistant_text(data)
