import base64
import json
import urllib.request

from .settings import (
    MAX_TTS_TEXT_LENGTH,
    MIMO_TTS_API_URL,
    SSL_CONTEXT,
    TTS_CONTENT_TYPES,
    current_tts_model,
    current_tts_response_format,
    current_tts_voice,
)


def build_tts_request_body(text, style=""):
    text = str(text or "").strip()
    style = str(style or "").strip()

    if not text:
        raise ValueError("朗读内容不能为空")

    if len(text) > MAX_TTS_TEXT_LENGTH:
        text = text[:MAX_TTS_TEXT_LENGTH]

    response_format = current_tts_response_format()
    return (
        {
            "model": current_tts_model(),
            "messages": [
                {"role": "user", "content": style or "请把下面的内容转换成语音。"},
                {"role": "assistant", "content": text},
            ],
            "audio": {
                "format": response_format,
                "voice": current_tts_voice(),
            },
        },
        response_format,
    )


def call_tts_api(api_key, request_body, response_format):
    body = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        MIMO_TTS_API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(request, timeout=120, context=SSL_CONTEXT) as response:
        response_body = response.read()
        content_type = response.headers.get_content_type()

        if content_type.startswith("audio/"):
            return response_body, content_type

        data = json.loads(response_body.decode("utf-8"))
        message = ((data.get("choices") or [{}])[0].get("message") or {}) if isinstance(data, dict) else {}
        audio = message.get("audio") or {}
        audio_base64 = audio.get("data") or data.get("data") or data.get("audio")

        if isinstance(audio_base64, dict):
            audio_base64 = audio_base64.get("data")

        if not audio_base64:
            raise ValueError("TTS 响应中没有音频数据")

        return base64.b64decode(audio_base64), TTS_CONTENT_TYPES.get(response_format, "audio/mpeg")
