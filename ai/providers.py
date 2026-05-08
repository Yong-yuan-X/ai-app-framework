from .claude import call_claude_chat
from .deepseek import call_deepseek_chat
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
    "deepseek": "DeepSeek",
}

PROVIDER_ALIASES = {
    "qianwen": "qwen",
    "openai": "gpt",
    "anthropic": "claude",
    "google": "gemini",
}

PROVIDER_MODEL_SUGGESTIONS = {
    "xiaomi": [],
    "doubao": [],
    "qwen": [],
    "gpt": [],
    "claude": [],
    "gemini": [],
    "deepseek": [],
}

PROVIDER_API_KEY_ENV = {
    "xiaomi": "MIMO_API_KEY",
    "doubao": "DOUBAO_API_KEY",
    "qwen": "QWEN_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

PROVIDER_BASE_URL_ENV = {
    "xiaomi": "MIMO_API_URL",
    "doubao": "DOUBAO_BASE_URL",
    "qwen": "QWEN_API_URL",
    "gpt": "OPENAI_RESPONSES_API_URL",
    "claude": "ANTHROPIC_API_URL",
    "gemini": "GEMINI_API_URL",
    "deepseek": "DEEPSEEK_API_URL",
}

PROVIDER_HANDLERS = {
    "xiaomi": call_xiaomi_chat,
    "doubao": call_doubao_chat,
    "qwen": call_qwen_chat,
    "gpt": call_gpt_chat,
    "claude": call_claude_chat,
    "gemini": call_gemini_chat,
    "deepseek": call_deepseek_chat,
}


def normalize_provider(provider):
    value = str(provider or "xiaomi").strip().lower()
    value = PROVIDER_ALIASES.get(value, value)
    return value if value in PROVIDER_LABELS else "xiaomi"


def normalize_model(provider, model):
    value = str(model or "").strip()
    provider = normalize_provider(provider)

    if provider == "xiaomi":
        return value.lower()

    return value


def call_provider_chat(provider, api_key, model, messages, options, ssl_context):
    provider = normalize_provider(provider)
    result = PROVIDER_HANDLERS[provider](api_key, model, messages, options or {}, ssl_context)

    if not result.get("content"):
        raise ValueError(f"{PROVIDER_LABELS[provider]} 返回成功，但未解析到文本内容")

    return result
