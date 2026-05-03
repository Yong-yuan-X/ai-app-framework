import os
import ssl
from pathlib import Path

from ai import PROVIDER_API_KEY_ENV, PROVIDER_LABELS, PROVIDER_MODEL_SUGGESTIONS, normalize_provider

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

MIMO_TTS_API_URL = os.getenv("MIMO_TTS_API_URL") or "https://api.xiaomimimo.com/v1/chat/completions"
MIMO_TTS_MODEL = os.getenv("MIMO_TTS_MODEL") or "mimo-v2.5-tts"
MIMO_TTS_VOICE = os.getenv("MIMO_TTS_VOICE") or "mimo_default"
MIMO_TTS_RESPONSE_FORMAT = os.getenv("MIMO_TTS_RESPONSE_FORMAT") or "mp3"

ALLOWED_TTS_FORMATS = {"mp3", "wav", "opus", "flac", "pcm", "b64_json"}
TTS_CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/ogg",
    "flac": "audio/flac",
    "pcm": "audio/L16",
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

    return model or PROVIDER_MODEL_SUGGESTIONS[provider][0]


def provider_api_key(provider=None):
    provider = normalize_provider(provider or current_provider())
    provider_key = PROVIDER_API_KEY_ENV.get(provider, "AI_API_KEY")

    if provider == "xiaomi":
        return os.getenv(provider_key) or os.getenv("AI_API_KEY") or os.getenv("MIMO_API_KEY") or ""

    if provider == "qwen":
        return os.getenv(provider_key) or os.getenv("QIANWEN_API_KEY") or os.getenv("AI_API_KEY") or ""

    return os.getenv(provider_key) or os.getenv("AI_API_KEY") or ""


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

    return {
        "provider": provider,
        "model": current_model(),
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
    return os.getenv("MIMO_TTS_API_KEY") or os.getenv("MIMO_API_KEY") or ""


def current_tts_model():
    return os.getenv("MIMO_TTS_MODEL", MIMO_TTS_MODEL).strip() or "mimo-v2.5-tts"


def current_tts_voice():
    return os.getenv("MIMO_TTS_VOICE", MIMO_TTS_VOICE).strip() or "mimo_default"


def current_tts_response_format():
    response_format = os.getenv("MIMO_TTS_RESPONSE_FORMAT", MIMO_TTS_RESPONSE_FORMAT).strip()
    return response_format if response_format in ALLOWED_TTS_FORMATS else "mp3"


def tts_config_payload(include_secret=False):
    api_key = os.getenv("MIMO_TTS_API_KEY") or ""

    return {
        "model": current_tts_model(),
        "voice": current_tts_voice(),
        "apiKey": api_key if include_secret else "",
        "apiKeySet": bool(api_key),
        "fallbackApiKeySet": bool(os.getenv("MIMO_API_KEY")),
    }
