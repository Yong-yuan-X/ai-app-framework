import os
import ssl
from pathlib import Path

from ai import (
    PROVIDER_API_KEY_ENV,
    PROVIDER_BASE_URL_ENV,
    PROVIDER_LABELS,
    PROVIDER_MODEL_SUGGESTIONS,
    normalize_provider,
)

try:
    import certifi
except ImportError:
    certifi = None


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ai_app.db"


def load_env_file():
    env_path = BASE_DIR / ".env"

    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))
AI_PROVIDER = os.getenv("AI_PROVIDER", "xiaomi")
AI_MODEL = os.getenv("AI_MODEL", "")

MIMO_TTS_API_URL = os.getenv("MIMO_TTS_API_URL", "")
MIMO_TTS_MODEL = os.getenv("MIMO_TTS_MODEL", "")
MIMO_TTS_VOICE = os.getenv("MIMO_TTS_VOICE", "")
MIMO_TTS_RESPONSE_FORMAT = os.getenv("MIMO_TTS_RESPONSE_FORMAT") or "mp3"
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "xiaomi")

TTS_PROVIDER_LABELS = {
    "xiaomi": "小米",
    "openai": "OpenAI",
    "gemini": "Gemini",
}

TTS_CONFIG = {
    "xiaomi": {
        "api_key_env": "MIMO_TTS_API_KEY",
        "api_key_fallbacks": ["MIMO_API_KEY"],
        "base_url_env": "MIMO_TTS_API_URL",
        "model_env": "MIMO_TTS_MODEL",
        "voice_env": "MIMO_TTS_VOICE",
    },
    "openai": {
        "api_key_env": "OPENAI_TTS_API_KEY",
        "api_key_fallbacks": ["OPENAI_API_KEY"],
        "base_url_env": "OPENAI_TTS_API_URL",
        "model_env": "OPENAI_TTS_MODEL",
        "voice_env": "OPENAI_TTS_VOICE",
    },
    "gemini": {
        "api_key_env": "GEMINI_TTS_API_KEY",
        "api_key_fallbacks": ["GEMINI_API_KEY"],
        "base_url_env": "GEMINI_TTS_API_URL",
        "model_env": "GEMINI_TTS_MODEL",
        "voice_env": "GEMINI_TTS_VOICE",
    },
}

ALLOWED_TTS_FORMATS = {"mp3", "wav", "opus", "flac", "pcm", "aac", "b64_json"}
TTS_CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/ogg",
    "flac": "audio/flac",
    "pcm": "audio/L16",
    "aac": "audio/aac",
}

MAX_REQUEST_SIZE = int(os.getenv("AI_MAX_REQUEST_SIZE_BYTES", str(1024 * 1024 * 1024)))
MAX_TTS_TEXT_LENGTH = 3000
MAX_CONVERSATION_MESSAGES = 100
MAX_CONVERSATIONS = 30
CONVERSATION_RETENTION_SECONDS = 30 * 24 * 60 * 60
RATE_LIMIT_WINDOW_SECONDS = 60 * 60
RATE_LIMIT_MAX = int(os.getenv("AI_RATE_LIMIT_PER_HOUR", "60"))
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()

LOCAL_USER = {
    "id": 1,
    "username": "local",
    "displayName": "本地用户",
    "role": "admin",
    "status": "approved",
}


def current_provider():
    return normalize_provider(os.getenv("AI_PROVIDER", AI_PROVIDER))


def current_model():
    provider = current_provider()
    model = os.getenv("AI_MODEL", AI_MODEL).strip()

    if not model and provider == "xiaomi":
        model = os.getenv("MIMO_MODEL", "").strip()

    return model


def provider_api_key(provider=None):
    provider = normalize_provider(provider or current_provider())
    provider_key = PROVIDER_API_KEY_ENV.get(provider, "AI_API_KEY")

    if provider == "xiaomi":
        return os.getenv(provider_key) or os.getenv("AI_API_KEY") or os.getenv("MIMO_API_KEY") or ""

    if provider == "qwen":
        return os.getenv(provider_key) or os.getenv("QIANWEN_API_KEY") or os.getenv("AI_API_KEY") or ""

    return os.getenv(provider_key) or os.getenv("AI_API_KEY") or ""


def provider_base_url(provider=None):
    provider = normalize_provider(provider or current_provider())
    base_url_env = PROVIDER_BASE_URL_ENV.get(provider, "AI_BASE_URL")
    return os.getenv(base_url_env) or os.getenv("AI_BASE_URL") or ""


def update_env_file(updates):
    env_path = BASE_DIR / ".env"
    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
    pending = dict(updates)
    next_lines = []

    for line in existing_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or "=" not in line:
            next_lines.append(line)
            continue

        key = line.split("=", 1)[0].strip()

        if key in pending:
            next_lines.append(f"{key}={pending.pop(key)}")
        else:
            next_lines.append(line)

    for key, value in pending.items():
        next_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")


def config_payload(include_secret=False):
    provider = current_provider()
    api_key = provider_api_key(provider)
    base_url = provider_base_url(provider)

    return {
        "provider": provider,
        "model": current_model(),
        "baseUrl": base_url,
        "apiKey": api_key if include_secret else "",
        "apiKeySet": bool(api_key),
        "providers": [
            {
                "value": value,
                "label": label,
                "models": PROVIDER_MODEL_SUGGESTIONS.get(value, []),
            }
            for value, label in PROVIDER_LABELS.items()
        ],
    }


def tts_api_key():
    provider = current_tts_provider()
    config = TTS_CONFIG[provider]
    api_key = os.getenv(config["api_key_env"]) or ""

    if api_key:
        return api_key

    for fallback_env in config.get("api_key_fallbacks", []):
        api_key = os.getenv(fallback_env) or ""
        if api_key:
            return api_key

    return ""


def normalize_tts_provider(provider):
    value = str(provider or "xiaomi").strip().lower()
    return value if value in TTS_PROVIDER_LABELS else "xiaomi"


def current_tts_provider():
    return normalize_tts_provider(os.getenv("TTS_PROVIDER", TTS_PROVIDER))


def tts_provider_config(provider=None):
    return TTS_CONFIG[normalize_tts_provider(provider or current_tts_provider())]


def current_tts_model():
    config = tts_provider_config()
    return os.getenv(config["model_env"], "").strip()


def current_tts_base_url():
    config = tts_provider_config()
    return os.getenv(config["base_url_env"], "").strip()


def current_tts_voice():
    config = tts_provider_config()
    return os.getenv(config["voice_env"], "").strip()


def current_tts_response_format():
    response_format = os.getenv("MIMO_TTS_RESPONSE_FORMAT", MIMO_TTS_RESPONSE_FORMAT).strip()
    return response_format if response_format in ALLOWED_TTS_FORMATS else "mp3"


def tts_config_payload(include_secret=False):
    provider = current_tts_provider()
    config = tts_provider_config(provider)
    api_key = os.getenv(config["api_key_env"]) or ""
    fallback_key_set = any(bool(os.getenv(env)) for env in config.get("api_key_fallbacks", []))

    return {
        "provider": provider,
        "model": current_tts_model(),
        "baseUrl": current_tts_base_url(),
        "voice": current_tts_voice(),
        "apiKey": api_key if include_secret else "",
        "apiKeySet": bool(api_key),
        "apiKeyEnv": config["api_key_env"],
        "fallbackApiKeySet": fallback_key_set,
        "providers": [{"value": value, "label": label} for value, label in TTS_PROVIDER_LABELS.items()],
    }
