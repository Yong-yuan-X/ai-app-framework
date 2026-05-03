import os

from .common import env_int, normalize_usage, post_json, split_system_messages


def call_claude_chat(api_key, model, messages, options, ssl_context):
    system, chat_messages = split_system_messages(messages)
    max_tokens = env_int("ANTHROPIC_MAX_TOKENS", 4096)
    request_body = {
        "model": model,
        "messages": chat_messages,
        "max_tokens": max_tokens,
    }

    if system:
        request_body["system"] = system

    if options.get("thinking"):
        if max_tokens <= 1024:
            max_tokens = 2048
            request_body["max_tokens"] = max_tokens
        budget_tokens = min(env_int("ANTHROPIC_THINKING_BUDGET_TOKENS", 1024), max_tokens - 1)
        request_body["thinking"] = {"type": "enabled", "budget_tokens": max(1024, budget_tokens)}

    if options.get("web_search"):
        request_body["tools"] = [{"type": "web_search_20260209", "name": "web_search"}]

    data = post_json(
        os.getenv("ANTHROPIC_API_URL") or "https://api.anthropic.com/v1/messages",
        request_body,
        {
            "x-api-key": api_key,
            "anthropic-version": os.getenv("ANTHROPIC_VERSION") or "2023-06-01",
        },
        env_int("ANTHROPIC_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return claude_text(data)


def claude_text(data):
    content_parts = []
    reasoning_parts = []

    for item in data.get("content") or []:
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        text = item.get("text") or item.get("thinking")

        if item_type == "text" and text:
            content_parts.append(str(text))
        elif item_type in {"thinking", "redacted_thinking"} and text:
            reasoning_parts.append(str(text))

    return {
        "content": "\n".join(content_parts).strip(),
        "reasoning": "\n".join(reasoning_parts).strip(),
        "finishReason": data.get("stop_reason"),
        "usage": normalize_usage(data.get("usage")),
    }
