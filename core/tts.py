import base64
import json
import struct
import urllib.parse
import urllib.request

from ai.common import endpoint_url

from .settings import (
    MAX_TTS_TEXT_LENGTH,
    SSL_CONTEXT,
    TTS_CONTENT_TYPES,
    current_tts_base_url,
    current_tts_model,
    current_tts_provider,
    current_tts_response_format,
    current_tts_voice,
)


def synthesize_tts(text, api_key, style=""):
    text = normalize_tts_text(text)
    provider = current_tts_provider()
    model = required_tts_value(current_tts_model(), "语音模型")
    base_url = required_tts_value(current_tts_base_url(), "语音 Base URL")
    voice = required_tts_value(current_tts_voice(), "音色")

    if provider == "openai":
        return call_openai_tts(api_key, base_url, model, voice, text)

    if provider == "gemini":
        return call_gemini_tts(api_key, base_url, model, voice, text, style)

    return call_xiaomi_tts(api_key, base_url, model, voice, text, style)


def normalize_tts_text(text):
    text = str(text or "").strip()

    if not text:
        raise ValueError("朗读内容不能为空")

    return text[:MAX_TTS_TEXT_LENGTH]


def required_tts_value(value, label):
    value = str(value or "").strip()

    if not value:
        raise ValueError(f"{label}不能为空，请先在左下角“修改语音配置”里填写")

    return value


def call_xiaomi_tts(api_key, base_url, model, voice, text, style):
    response_format = current_tts_response_format()
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": style or "请把下面的内容转换成语音。"},
            {"role": "assistant", "content": text},
        ],
        "audio": {
            "format": response_format,
            "voice": voice,
        },
    }
    data, content_type = post_json_or_audio(
        endpoint_url(base_url, "/chat/completions"),
        body,
        {"api-key": api_key, "Authorization": f"Bearer {api_key}"},
    )

    if isinstance(data, bytes):
        return data, content_type if content_type.startswith("audio/") else TTS_CONTENT_TYPES.get(response_format, "audio/mpeg")

    message = ((data.get("choices") or [{}])[0].get("message") or {}) if isinstance(data, dict) else {}
    audio = message.get("audio") or {}
    audio_base64 = audio.get("data") or data.get("data") or data.get("audio")

    return decode_audio(audio_base64, TTS_CONTENT_TYPES.get(response_format, "audio/mpeg"))


def call_openai_tts(api_key, base_url, model, voice, text):
    response_format = current_tts_response_format()
    body = {
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": response_format if response_format != "b64_json" else "mp3",
    }
    data, content_type = post_json_or_audio(
        endpoint_url(base_url, "/audio/speech"),
        body,
        {"Authorization": f"Bearer {api_key}"},
    )

    if isinstance(data, bytes):
        return data, content_type if content_type.startswith("audio/") else TTS_CONTENT_TYPES.get(response_format, "audio/mpeg")

    audio_base64 = data.get("data") or data.get("audio")
    return decode_audio(audio_base64, TTS_CONTENT_TYPES.get(response_format, "audio/mpeg"))


def call_gemini_tts(api_key, base_url, model, voice, text, style):
    body = {
        "contents": [{"parts": [{"text": f"{style}\n{text}".strip()}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice,
                    }
                }
            },
        },
    }
    model_path = urllib.parse.quote(model, safe="")
    url = f"{base_url.rstrip('/')}/models/{model_path}:generateContent"
    data, _ = post_json_or_audio(url, body, {"x-goog-api-key": api_key})

    if isinstance(data, bytes):
        return data, "audio/wav"

    for candidate in data.get("candidates") or []:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            inline_data = part.get("inlineData") or part.get("inline_data") or {}
            audio_base64 = inline_data.get("data")
            mime_type = inline_data.get("mimeType") or inline_data.get("mime_type") or "audio/wav"

            if audio_base64:
                audio_body = base64.b64decode(audio_base64)
                if "pcm" in mime_type.lower() or "audio/wav" in mime_type.lower():
                    return pcm_to_wav(audio_body), "audio/wav"

                return audio_body, mime_type

    raise ValueError("TTS 响应中没有音频数据")


def post_json_or_audio(url, body, headers):
    request_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_body,
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )

    with urllib.request.urlopen(request, timeout=120, context=SSL_CONTEXT) as response:
        response_body = response.read()
        content_type = response.headers.get_content_type()

        if content_type.startswith("audio/") or content_type == "application/octet-stream":
            return response_body, content_type

        try:
            return json.loads(response_body.decode("utf-8")), content_type
        except json.JSONDecodeError:
            return response_body, content_type


def decode_audio(audio_base64, content_type):
    if isinstance(audio_base64, dict):
        audio_base64 = audio_base64.get("data")

    if not audio_base64:
        raise ValueError("TTS 响应中没有音频数据")

    return base64.b64decode(audio_base64), content_type


def pcm_to_wav(pcm_data, sample_rate=24000, channels=1, bits_per_sample=16):
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_data)

    header = b"".join(
        [
            b"RIFF",
            struct.pack("<I", 36 + data_size),
            b"WAVE",
            b"fmt ",
            struct.pack("<I", 16),
            struct.pack("<H", 1),
            struct.pack("<H", channels),
            struct.pack("<I", sample_rate),
            struct.pack("<I", byte_rate),
            struct.pack("<H", block_align),
            struct.pack("<H", bits_per_sample),
            b"data",
            struct.pack("<I", data_size),
        ]
    )

    return header + pcm_data
