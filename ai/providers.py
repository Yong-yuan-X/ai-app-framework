from .claude import call_claude_chat
from .doubao import call_doubao_chat
from .gemini import call_gemini_chat
from .gpt import call_gpt_chat
from .qwen import call_qwen_chat
from .xiaomi import call_xiaomi_chat


PROVIDER_LABELS = {
    "xiaomi": "小米",
    "doubao": "豆包",
    "qwen": "千问",
    "gpt": "GPT",
    "claude": "Claude",
    "gemini": "Gemini",
}

PROVIDER_ALIASES = {
    "qianwen": "qwen",
    "openai": "gpt",
    "anthropic": "claude",
    "google": "gemini",
}

PROVIDER_MODEL_SUGGESTIONS = {
    "xiaomi": ["mimo-v2.5", "mimo-v2-pro"],
    "doubao": ["doubao-seed-1.6"],
    "qwen": ["qwen-plus", "qwen-max", "qwen3-max"],
    "gpt": ["gpt-5.5", "gpt-5.4", "gpt-4.1-mini"],
    "claude": ["claude-opus-4-7", "claude-sonnet-4-6", "claude-opus-4-6"],
    "gemini": ["gemini-2.5-pro", "gemini-2.5-flash"],
}

PROVIDER_API_KEY_ENV = {
    "xiaomi": "MIMO_API_KEY",
    "doubao": "DOUBAO_API_KEY",
    "qwen": "QWEN_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

PROVIDER_HANDLERS = {
    "xiaomi": call_xiaomi_chat,
    "doubao": call_doubao_chat,
    "qwen": call_qwen_chat,
    "gpt": call_gpt_chat,
    "claude": call_claude_chat,
    "gemini": call_gemini_chat,
}


def normalize_provider(provider):
    value = str(provider or "xiaomi").strip().lower()
    value = PROVIDER_ALIASES.get(value, value)
    return value if value in PROVIDER_LABELS else "xiaomi"


def call_provider_chat(provider, api_key, model, messages, options, ssl_context):
    provider = normalize_provider(provider)
    result = PROVIDER_HANDLERS[provider](api_key, model, messages, options or {}, ssl_context)

    if not result.get("content"):
        raise ValueError(f"{PROVIDER_LABELS[provider]} 返回成功，但未解析到文本内容")

    return result
