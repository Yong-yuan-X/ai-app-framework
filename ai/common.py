import json
import os
import urllib.request


def env_int(name, default):
    try:
        return int(os.getenv(name) or default)
    except ValueError:
        return default


def post_json(url, body, headers, timeout, ssl_context):
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )

    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
        return json.loads(response.read().decode("utf-8"))


def split_system_messages(messages):
    system_parts = []
    chat_messages = []

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            system_parts.append(content)
        else:
            chat_messages.append({"role": role, "content": content})

    return "\n\n".join(system_parts).strip(), chat_messages


def assistant_text(data):
    choice = (data.get("choices") or [{}])[0] if isinstance(data, dict) else {}
    message = choice.get("message") or {}
    content = message.get("content") or ""

    if isinstance(content, list):
        content = "".join(item.get("text") or item.get("content") or "" for item in content if isinstance(item, dict))

    reasoning_details = message.get("reasoning_details")
    reasoning = message.get("reasoning_content") or message.get("reasoning") or ""

    if not reasoning and isinstance(reasoning_details, list):
        reasoning = "\n".join(
            item.get("text") or item.get("content") or "" for item in reasoning_details if isinstance(item, dict)
        )

    return {
        "content": str(content or "").strip(),
        "reasoning": str(reasoning or "").strip(),
        "finishReason": choice.get("finish_reason"),
        "usage": data.get("usage") if isinstance(data, dict) else None,
    }


def normalize_usage(usage):
    if not isinstance(usage, dict):
        return usage

    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", usage.get("promptTokenCount")))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens", usage.get("candidatesTokenCount")))
    total_tokens = usage.get("total_tokens", usage.get("totalTokenCount"))

    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def responses_api_text(data):
    incomplete_details = data.get("incomplete_details") if isinstance(data, dict) else None
    finish_reason = incomplete_details.get("reason") if isinstance(incomplete_details, dict) else None

    return {
        "content": extract_responses_text(data),
        "reasoning": extract_responses_reasoning(data),
        "finishReason": finish_reason or data.get("status") if isinstance(data, dict) else None,
        "usage": normalize_usage(data.get("usage")) if isinstance(data, dict) else None,
    }


def extract_responses_text(data):
    if not isinstance(data, dict):
        return ""

    output_text = data.get("output_text")

    if output_text:
        return str(output_text).strip()

    text_parts = []

    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue

        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue

            content_type = content.get("type") or ""

            if content_type in {"output_text", "text", "summary_text"}:
                text_value = content.get("text") or content.get("value") or content.get("output_text")
                if text_value:
                    text_parts.append(str(text_value))

                for annotation in content.get("annotations") or []:
                    if isinstance(annotation, dict) and annotation.get("text"):
                        text_parts.append(str(annotation["text"]))
            else:
                for key in ("text", "value", "output_text"):
                    if content.get(key):
                        text_parts.append(str(content[key]))
                        break

    if text_parts:
        return "\n".join(text_parts).strip()

    return assistant_text(data).get("content", "").strip()


def extract_responses_reasoning(data):
    if not isinstance(data, dict):
        return ""

    reasoning_parts = []

    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue

        if item.get("type") == "reasoning":
            summary = item.get("summary") or []

            if isinstance(summary, str):
                reasoning_parts.append(summary)
            elif isinstance(summary, list):
                for summary_item in summary:
                    if isinstance(summary_item, dict):
                        text = summary_item.get("text") or summary_item.get("value")
                        if text:
                            reasoning_parts.append(str(text))

        for content in item.get("content") or []:
            if isinstance(content, dict) and content.get("type") in {"reasoning", "summary_text"}:
                text = content.get("text") or content.get("value")
                if text:
                    reasoning_parts.append(str(text))

    return "\n".join(reasoning_parts).strip()
