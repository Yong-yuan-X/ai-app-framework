import mimetypes
import os
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ai import PROVIDER_API_KEY_ENV, PROVIDER_LABELS, PROVIDER_MODEL_SUGGESTIONS, call_provider_chat, normalize_provider
from core.http import api_error, binary_response, json_response, read_json_body
from core.messages import normalize_messages
from core.rate_limit import is_rate_limited
from core.settings import (
    HOST,
    LOCAL_USER,
    MAX_REQUEST_SIZE,
    PORT,
    SSL_CONTEXT,
    STATIC_DIR,
    config_payload,
    current_provider,
    provider_api_key,
    tts_api_key,
    tts_config_payload,
    update_env_file,
)
from core.storage import init_db, load_conversations, save_conversations
from core.tts import build_tts_request_body, call_tts_api


class AIAppHandler(BaseHTTPRequestHandler):
    server_version = "AIAppFramework/1.0"

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/auth/me":
            json_response(self, 200, {"user": LOCAL_USER})
            return

        if path == "/api/admin/users":
            json_response(self, 200, {"users": []})
            return

        if path == "/api/conversations":
            self.handle_get_conversations()
            return

        if path == "/api/config":
            json_response(self, 200, config_payload())
            return

        if path == "/api/tts-config":
            json_response(self, 200, tts_config_payload())
            return

        self.serve_static()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/chat":
            self.handle_chat()
            return

        if path == "/api/tts":
            self.handle_tts()
            return

        if path == "/api/conversations":
            self.handle_save_conversations()
            return

        if path == "/api/config":
            self.handle_save_config()
            return

        if path == "/api/tts-config":
            self.handle_save_tts_config()
            return

        if path in {"/api/auth/logout", "/api/auth/change-password"}:
            json_response(self, 200, {"message": "本地框架模式已处理"})
            return

        json_response(self, 404, {"error": "Not found"})

    def handle_get_conversations(self):
        try:
            json_response(self, 200, {"conversations": load_conversations()})
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "读取历史对话失败"})

    def handle_save_conversations(self):
        try:
            payload = read_json_body(self, MAX_REQUEST_SIZE)
            conversations = payload.get("conversations")

            if not isinstance(conversations, list):
                json_response(self, 400, {"error": "历史对话格式不正确"})
                return

            count = save_conversations(conversations)
            json_response(self, 200, {"message": "已保存", "count": count})
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "保存历史对话失败"})

    def handle_save_config(self):
        try:
            payload = read_json_body(self, 64 * 1024)
            provider = normalize_provider(payload.get("provider"))
            model = str(payload.get("model") or "").strip()
            api_key = str(payload.get("apiKey") or "").strip()

            if provider not in PROVIDER_LABELS:
                json_response(self, 400, {"error": "模型厂商不支持"})
                return

            if not model:
                json_response(self, 400, {"error": "模型不能为空"})
                return

            if "\n" in model or "\r" in model or "\n" in api_key or "\r" in api_key:
                json_response(self, 400, {"error": "配置内容不能包含换行"})
                return

            api_key_env = PROVIDER_API_KEY_ENV.get(provider, "AI_API_KEY")
            updates = {
                "AI_PROVIDER": provider,
                "AI_MODEL": model,
            }

            os.environ["AI_PROVIDER"] = provider
            os.environ["AI_MODEL"] = model

            if api_key:
                os.environ[api_key_env] = api_key
                updates[api_key_env] = api_key

            update_env_file(updates)
            json_response(self, 200, {"message": "配置已保存", "config": config_payload()})
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "保存配置失败"})

    def handle_save_tts_config(self):
        try:
            payload = read_json_body(self, 64 * 1024)
            model = str(payload.get("model") or "").strip()
            voice = str(payload.get("voice") or "").strip()
            api_key = str(payload.get("apiKey") or "").strip()

            if not model:
                json_response(self, 400, {"error": "语音模型不能为空"})
                return

            if not voice:
                json_response(self, 400, {"error": "音色不能为空"})
                return

            if "\n" in model or "\r" in model or "\n" in voice or "\r" in voice or "\n" in api_key or "\r" in api_key:
                json_response(self, 400, {"error": "语音配置不能包含换行"})
                return

            updates = {
                "MIMO_TTS_MODEL": model,
                "MIMO_TTS_VOICE": voice,
            }

            os.environ["MIMO_TTS_MODEL"] = model
            os.environ["MIMO_TTS_VOICE"] = voice

            if api_key:
                os.environ["MIMO_TTS_API_KEY"] = api_key
                updates["MIMO_TTS_API_KEY"] = api_key

            update_env_file(updates)
            json_response(self, 200, {"message": "语音配置已保存", "config": tts_config_payload()})
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "保存语音配置失败"})

    def handle_chat(self):
        if is_rate_limited(self):
            json_response(self, 429, {"error": "请求太频繁，请稍后再试"})
            return

        provider = current_provider()

        try:
            payload = read_json_body(self, MAX_REQUEST_SIZE)
            provider = normalize_provider(payload.get("provider") or current_provider())
            api_key = provider_api_key(provider)

            if not api_key:
                json_response(
                    self,
                    500,
                    {"error": f"本地未配置 {PROVIDER_API_KEY_ENV.get(provider, 'AI_API_KEY')}，请先在左下角“修改配置”里填写"},
                )
                return

            requested_model = str(payload.get("model") or "").strip()
            model = requested_model or PROVIDER_MODEL_SUGGESTIONS[provider][0]
            messages = normalize_messages(payload.get("messages"))

            if not messages:
                json_response(self, 400, {"error": "消息不能为空"})
                return

            result = call_provider_chat(
                provider,
                api_key,
                model,
                messages,
                {
                    "web_search": bool(payload.get("webSearch")),
                    "thinking": bool(payload.get("thinking")),
                },
                SSL_CONTEXT,
            )
            json_response(self, 200, result)
        except urllib.error.HTTPError as error:
            api_error(self, error, f"{PROVIDER_LABELS.get(provider, 'AI')} API 请求失败", PROVIDER_LABELS.get(provider, "AI"))
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "服务器处理失败"})

    def handle_tts(self):
        if is_rate_limited(self):
            json_response(self, 429, {"error": "请求太频繁，请稍后再试"})
            return

        api_key = tts_api_key()

        if not api_key:
            json_response(self, 500, {"error": "本地未配置 MIMO_TTS_API_KEY，请先在左下角“修改语音配置”里填写"})
            return

        try:
            payload = read_json_body(self, 64 * 1024)
            request_body, response_format = build_tts_request_body(payload.get("text"), payload.get("style"))
            audio_body, content_type = call_tts_api(api_key, request_body, response_format)
            binary_response(self, 200, audio_body, content_type)
        except urllib.error.HTTPError as error:
            api_error(self, error, "MiMo TTS 请求失败", "MiMo")
        except Exception as error:
            json_response(self, 500, {"error": str(error) or "语音生成失败"})

    def serve_static(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed_url.path)
        relative_path = "index.html" if path in {"/", ""} else path.lstrip("/")
        file_path = (STATIC_DIR / relative_path).resolve()

        if not str(file_path).startswith(str(STATIC_DIR)) or not file_path.is_file() or self.is_private_file(file_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Not found".encode("utf-8"))
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()

        with file_path.open("rb") as file:
            self.wfile.write(file.read())

    @staticmethod
    def is_private_file(file_path):
        return file_path.name.startswith(".") or "data" in file_path.parts


if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AIAppHandler)
    print(f"AI app framework listening on http://{HOST}:{PORT}")
    server.serve_forever()
