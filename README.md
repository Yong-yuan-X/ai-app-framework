# 自用 AI 独立框架

<img width="2718" height="1704" alt="img_v3_0211b_cf86d7dd-c5b3-4f36-b8ca-543c7c66a9bg" src="https://github.com/user-attachments/assets/c47a5c9d-8de1-4707-a892-3de8071a5ae5" />

 [English](README.en.md)。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

打开 `http://localhost:8080`。如需换端口：

```bash
PORT=8081 python3 app.py
```

## 配置

在页面左下角可修改聊天模型配置和语音配置；配置会保存到本地 `.env`。

聊天厂商：小米、豆包、千问、GPT、Claude、Gemini、DeepSeek。每个厂商可自行填写模型名、Base URL 和 API Key，并可开启联网搜索或 Thinking。

语音厂商：小米、OpenAI、Gemini。每个厂商可自行填写语音模型名、Base URL、音色和 API Key。其他模型暂时没有支持

常用环境变量：

```text
AI_PROVIDER
AI_MODEL
TTS_PROVIDER
MIMO_API_KEY
DOUBAO_API_KEY
QWEN_API_KEY
OPENAI_API_KEY
DEEPSEEK_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
MIMO_TTS_API_KEY
MIMO_TTS_API_URL
MIMO_TTS_MODEL
MIMO_TTS_VOICE
OPENAI_TTS_API_KEY
OPENAI_TTS_API_URL
GEMINI_TTS_API_KEY
GEMINI_TTS_API_URL
AI_RATE_LIMIT_PER_HOUR
AI_MAX_REQUEST_SIZE_BYTES
```

## 功能

- 多厂商聊天模型切换
- 联网搜索和 Thinking 开关
- 回答播放语音、复制回复
- 附件选择和拖拽添加，不限制数量和大小
- 本地历史对话存储

历史记录保存在 `data/ai_app.db`，默认保留 30 天。


现在测试过了小米、豆包的模型没有问题。如果使用其他模型的时候遇到问题，可以自行尝试解决PR上来或者写一下issue说明遇到的问题，我看到后会及时地修复


如果除了这几个模型还有其他的，欢迎各位新添API接入测试后放上来


如果遇到bug或者页面修改建议，欢迎提出issue
