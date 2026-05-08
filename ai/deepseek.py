import os

from .common import assistant_text, endpoint_url, env_int, post_json


def call_deepseek_chat(api_key, model, messages, options, ssl_context):
    request_body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": env_int("DEEPSEEK_MAX_TOKENS", 4096),
        "temperature": 0.7,
        "top_p": 0.95,
    }

    if options.get("thinking"):
        request_body["thinking"] = {"type": "enabled"}
        request_body["reasoning_effort"] = os.getenv("DEEPSEEK_REASONING_EFFORT") or "high"

    data = post_json(
        endpoint_url(options.get("base_url"), "/chat/completions"),
        request_body,
        {"Authorization": f"Bearer {api_key}"},
        env_int("DEEPSEEK_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return assistant_text(data)
