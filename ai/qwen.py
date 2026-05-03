import os

from .common import assistant_text, env_int, post_json


def call_qwen_chat(api_key, model, messages, options, ssl_context):
    request_body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": env_int("QWEN_MAX_TOKENS", 4096),
        "temperature": 0.7,
        "top_p": 0.95,
    }

    if options.get("web_search"):
        request_body["enable_search"] = True

    if options.get("thinking"):
        request_body["enable_thinking"] = True

    data = post_json(
        os.getenv("QWEN_API_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        request_body,
        {"Authorization": f"Bearer {api_key}"},
        env_int("QWEN_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return assistant_text(data)
