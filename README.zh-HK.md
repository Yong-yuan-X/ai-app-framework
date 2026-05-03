# 自用 AI 獨立框架

輕量 Python 後端 + 靜態前端的本地 AI 聊天框架。另有 [簡體中文](README.md) 和 [English](README.en.md)。

## 運行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

開啟 `http://localhost:8080`。如需更改端口：

```bash
PORT=8081 python3 app.py
```

## 配置

可在頁面左下角修改聊天模型配置和語音配置；配置會儲存到本地 `.env`。

聊天廠商：小米、豆包、千問、GPT、Claude、Gemini。每個廠商可自行填寫模型名稱和 API Key，並可開啟聯網搜尋或 Thinking。

常用環境變數：

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

語音朗讀目前使用小米 MiMo TTS。未配置 `MIMO_TTS_API_KEY` 時，會嘗試複用 `MIMO_API_KEY`。

## 功能

- 多廠商聊天模型切換
- 聯網搜尋和 Thinking 開關
- 回答播放語音、複製回覆
- 附件選擇和拖拽添加，不限制數量和大小
- 本地歷史對話儲存

歷史記錄保存在 `data/ai_app.db`，默認保留 30 天。

目前已測試小米、豆包的模型，沒有發現問題。如果使用其他模型時遇到問題，可以自行嘗試解決後提交 PR，或者提交 issue 說明遇到的問題，我看到後會及時修復。

如果除了這幾個模型還有其他模型，歡迎新增 API 接入，測試後提交上來。

如果遇到 bug 或者有頁面修改建議，歡迎提出 issue。
