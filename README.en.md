# Personal AI App Framework

A local AI chat framework with a lightweight Python backend and a static frontend. Also available in [Simplified Chinese](README.md) and [Traditional Chinese](README.zh-HK.md).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

Open `http://localhost:8080`. To use another port:

```bash
PORT=8081 python3 app.py
```

## Configuration

Use the bottom-left settings menu to configure chat models and voice settings. Values are saved to the local `.env` file.

Supported chat providers: Xiaomi, Doubao, Qwen, GPT, Claude, and Gemini. You can enter your own model name and API key for each provider, and toggle web search or Thinking when supported.

Common environment variables:

```text
AI_PROVIDER
AI_MODEL
MIMO_API_KEY
DOUBAO_API_KEY
QWEN_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
MIMO_TTS_API_KEY
MIMO_TTS_MODEL
MIMO_TTS_VOICE
AI_RATE_LIMIT_PER_HOUR
AI_MAX_REQUEST_SIZE_BYTES
```

Voice playback currently uses Xiaomi MiMo TTS. If `MIMO_TTS_API_KEY` is not set, the backend will try to reuse `MIMO_API_KEY`.

## Features

- Switch between multiple chat providers
- Web search and Thinking toggles
- Play assistant replies as speech, copy replies
- Add attachments by file picker or drag and drop, with no count or size limit
- Local conversation history

Conversation history is stored in `data/ai_app.db` and kept for 30 days by default.

Xiaomi and Doubao models have been tested and work as expected. If you run into issues with other providers, feel free to fix them and open a PR, or open an issue describing the problem. I will take a look and fix it when I can.

If you want to add support for more models, contributions are welcome. Please test the API integration before submitting it.

Bug reports and UI improvement suggestions are also welcome via issues.
