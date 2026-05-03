def normalize_messages(messages):
    if not isinstance(messages, list):
        return []

    normalized = []

    for message in messages:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role in {"system", "user", "assistant"} and isinstance(content, str):
            normalized.append({"role": role, "content": content})

    return normalized[-20:]
