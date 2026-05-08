import os

from .common import endpoint_url, env_int, post_json, responses_api_text


def call_gpt_chat(api_key, model, messages, options, ssl_context):
    request_body = {
        "model": model,
        "input": messages,
        "max_output_tokens": env_int("OPENAI_MAX_OUTPUT_TOKENS", 4096),
    }

    if options.get("web_search"):
        request_body["tools"] = [{"type": "web_search"}]

    if options.get("thinking"):
        request_body["reasoning"] = {"effort": os.getenv("OPENAI_REASONING_EFFORT") or "medium"}

    data = post_json(
        endpoint_url(options.get("base_url"), "/responses"),
        request_body,
        {"Authorization": f"Bearer {api_key}"},
        env_int("OPENAI_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return responses_api_text(data)
