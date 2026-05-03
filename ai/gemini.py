import os
import urllib.parse

from .common import env_int, normalize_usage, post_json, split_system_messages


def call_gemini_chat(api_key, model, messages, options, ssl_context):
    system, chat_messages = split_system_messages(messages)
    contents = []

    for message in chat_messages:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": message["content"]}]})

    request_body = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": env_int("GEMINI_MAX_OUTPUT_TOKENS", 4096),
        },
    }

    if system:
        request_body["system_instruction"] = {"parts": [{"text": system}]}

    if options.get("web_search"):
        request_body["tools"] = [{"google_search": {}}]

    if options.get("thinking"):
        request_body["generationConfig"]["thinkingConfig"] = {
            "thinkingBudget": env_int("GEMINI_THINKING_BUDGET", 1024),
            "includeThoughts": True,
        }

    base_url = (os.getenv("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model_path = urllib.parse.quote(model, safe="")
    url = f"{base_url}/models/{model_path}:generateContent"
    data = post_json(
        url,
        request_body,
        {"x-goog-api-key": api_key},
        env_int("GEMINI_TIMEOUT_SECONDS", 120),
        ssl_context,
    )
    return gemini_text(data)


def gemini_text(data):
    candidates = data.get("candidates") or []
    candidate = candidates[0] if candidates else {}
    content = candidate.get("content") or {}
    content_parts = []
    reasoning_parts = []

    for part in content.get("parts") or []:
        if not isinstance(part, dict) or not part.get("text"):
            continue

        if part.get("thought"):
            reasoning_parts.append(str(part["text"]))
        else:
            content_parts.append(str(part["text"]))

    return {
        "content": "\n".join(content_parts).strip(),
        "reasoning": "\n".join(reasoning_parts).strip(),
        "finishReason": candidate.get("finishReason"),
        "usage": normalize_usage(data.get("usageMetadata")),
    }
