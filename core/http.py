import json


def json_response(handler, status_code, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def binary_response(handler, status_code, body, content_type):
    handler.send_response(status_code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler, max_size):
    content_length = int(handler.headers.get("Content-Length", "0"))

    if content_length > max_size:
        raise ValueError("请求内容过大")

    raw_body = handler.rfile.read(content_length).decode("utf-8") if content_length else "{}"
    return json.loads(raw_body)


def api_error(handler, error, fallback_message, provider_label="API"):
    response_text = error.read().decode("utf-8", errors="replace")
    print(f"[{provider_label}] HTTP {error.code}: {response_text}", flush=True)

    try:
        detail = json.loads(response_text)
    except json.JSONDecodeError:
        detail = {"raw": response_text}

    raw_message = (
        detail.get("error", {}).get("message")
        if isinstance(detail.get("error"), dict)
        else detail.get("message", fallback_message)
    )
    message = f"{provider_label}：{raw_message}" if raw_message else fallback_message
    json_response(handler, error.code, {"error": message, "detail": detail})
