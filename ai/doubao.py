import os

from .common import env_int, post_json, responses_api_text


def call_doubao_chat(api_key, model, messages, options, ssl_context):
    base_url = (os.getenv("DOUBAO_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
    api_url = os.getenv("DOUBAO_RESPONSES_API_URL") or f"{base_url}/responses"
    request_body = {
        "model": model,
        "input": messages,
        "max_output_tokens": env_int("DOUBAO_MAX_OUTPUT_TOKENS", 2048),
    }

    if options.get("web_search"):
        request_body["tools"] = [{"type": "web_search"}]

    data = post_json(
        api_url,
        request_body,
        {"Authorization": f"Bearer {api_key}"},
        env_int("DOUBAO_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return responses_api_text(data)
