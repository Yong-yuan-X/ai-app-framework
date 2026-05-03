const form = document.getElementById("chatForm");
const input = document.getElementById("chatInput");
const conversation = document.getElementById("conversation");
const chatHero = document.querySelector(".chat-hero");
const newChatButton = document.getElementById("newChatButton");
const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");
const thinkingToggle = document.getElementById("thinkingToggle");
const searchToggle = document.getElementById("searchToggle");
const chatError = document.getElementById("chatError");
const sendButton = form?.querySelector(".send-button");
const historyList = document.getElementById("historyList");
const historyEmpty = document.getElementById("historyEmpty");
const attachButton = document.getElementById("attachButton");
const fileInput = document.getElementById("fileInput");
const attachmentList = document.getElementById("attachmentList");
const voiceButton = document.getElementById("voiceButton");
const settingsButton = document.querySelector(".settings-button");
const settingsMenu = document.getElementById("settingsMenu");
const profileName = document.getElementById("profileName");
const configModal = document.getElementById("configModal");
const ttsConfigModal = document.getElementById("ttsConfigModal");
const configOpen = document.getElementById("configOpen");
const ttsConfigOpen = document.getElementById("ttsConfigOpen");
const configCancel = document.getElementById("configCancel");
const ttsConfigCancel = document.getElementById("ttsConfigCancel");
const configForm = document.getElementById("configForm");
const ttsConfigForm = document.getElementById("ttsConfigForm");
const configProviderSelect = document.getElementById("configProviderSelect");
const configModelInput = document.getElementById("configModelInput");
const configApiKeyInput = document.getElementById("configApiKeyInput");
const configHint = document.getElementById("configHint");
const ttsConfigModelInput = document.getElementById("ttsConfigModelInput");
const ttsConfigVoiceInput = document.getElementById("ttsConfigVoiceInput");
const ttsConfigApiKeyInput = document.getElementById("ttsConfigApiKeyInput");
const ttsConfigHint = document.getElementById("ttsConfigHint");
const modelSuggestions = document.getElementById("modelSuggestions");
const adminOnlyLinks = document.querySelectorAll(".admin-only");
const reviewLinks = [...document.querySelectorAll(".admin-only")].filter((item) => item.textContent.includes("审核"));

const storageKeyPrefix = "foreverHubAiConversations";
const textFilePattern = /^(text\/|application\/(json|xml|javascript|x-javascript))/;
const readableExtensions = /\.(txt|md|csv|json|js|ts|tsx|jsx|py|java|go|rs|c|cpp|h|css|html|xml|yaml|yml|sql|log)$/i;

const systemPrompt = {
  role: "system",
  content:
    "回答要清晰、实用，默认使用中文。直接回答用户问题，不要寒暄，不要自我介绍，不要使用“你好呀”“我是小米的MiMo”“很高兴为你服务”等固定开场。可以使用 Markdown 组织内容，例如标题、列表、代码块和加粗。不要使用 emoji、颜文字或装饰性表情符号。",
};

let conversations = [];
let activeConversationId = null;
let pendingAttachments = [];
let recognition = null;
let voiceBaseText = "";
let currentUser = null;
let activeAudio = null;
let activeAudioUrl = "";
let activeSpeechButton = null;
let activeChatController = null;
let isGenerating = false;
let saveConversationsTimer = null;
let aiConfig = {
  provider: "xiaomi",
  model: "mimo-v2.5",
  providers: [
    { value: "xiaomi", label: "小米", models: ["mimo-v2.5", "mimo-v2-pro"] },
    { value: "doubao", label: "豆包", models: ["doubao-seed-1.6"] },
    { value: "qwen", label: "千问", models: ["qwen-plus", "qwen-max", "qwen3-max"] },
    { value: "gpt", label: "GPT", models: ["gpt-5.5", "gpt-5.4", "gpt-4.1-mini"] },
    { value: "claude", label: "Claude", models: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-opus-4-6"] },
    { value: "gemini", label: "Gemini", models: ["gemini-2.5-pro", "gemini-2.5-flash"] },
  ],
};
let ttsConfig = {
  model: "mimo-v2.5-tts",
  voice: "mimo_default",
  apiKeySet: false,
  fallbackApiKeySet: false,
};
const speechStore = new Map();
const copyStore = new Map();

const sendIcon = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M22 2L11 13" />
    <path d="M22 2L15 22L11 13L2 9L22 2Z" />
  </svg>
`;
const stopIcon = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M8 8H16V16H8Z" />
  </svg>
`;

const getStorageKey = () => `${storageKeyPrefix}:${currentUser?.id || currentUser?.username || "guest"}`;

const savedConversations = (items = conversations) => {
  return items.filter((item) => Array.isArray(item.messages) && item.messages.length > 0).slice(0, 30);
};

const loadLocalConversations = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(getStorageKey()) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
};

const saveLocalConversations = (items = conversations) => {
  localStorage.setItem(getStorageKey(), JSON.stringify(savedConversations(items)));
};

const persistConversations = async (items = conversations) => {
  const data = savedConversations(items);
  saveLocalConversations(data);

  await fetch("/api/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversations: data }),
  });
};

async function loadConversations() {
  const localConversations = loadLocalConversations();

  try {
    const response = await fetch("/api/conversations");

    if (!response.ok) {
      return localConversations;
    }

    const data = await response.json();
    const serverConversations = Array.isArray(data.conversations) ? data.conversations : [];

    if (serverConversations.length) {
      saveLocalConversations(serverConversations);
      return serverConversations;
    }

    if (localConversations.some((item) => item.messages?.length)) {
      persistConversations(localConversations).catch(() => {});
    }

    return localConversations;
  } catch {
    return localConversations;
  }
}

function saveConversations() {
  clearTimeout(saveConversationsTimer);
  saveLocalConversations();
  saveConversationsTimer = setTimeout(() => {
    persistConversations().catch(() => {});
  }, 350);
}

const providerByValue = (value) => {
  return aiConfig.providers.find((provider) => provider.value === value) || aiConfig.providers[0];
};

const modelOptionsForProvider = (providerValue = aiConfig.provider) => {
  const provider = providerByValue(providerValue);
  return Array.isArray(provider?.models) ? provider.models : [];
};

const renderModelSuggestions = (providerValue = aiConfig.provider) => {
  if (!modelSuggestions) {
    return;
  }

  modelSuggestions.innerHTML = modelOptionsForProvider(providerValue)
    .map((model) => `<option value="${escapeHtml(model)}"></option>`)
    .join("");
};

const renderProviderOptions = () => {
  const optionsHtml = aiConfig.providers
    .map((provider) => `<option value="${escapeHtml(provider.value)}">${escapeHtml(provider.label)}</option>`)
    .join("");

  if (configProviderSelect) {
    configProviderSelect.innerHTML = optionsHtml;
  }

  if (providerSelect) {
    providerSelect.innerHTML = optionsHtml;
  }
};

const renderComposerModelOptions = () => {
  if (!modelSelect) {
    return;
  }

  const models = modelOptionsForProvider();
  const uniqueModels = [...new Set([aiConfig.model, ...models].filter(Boolean))];
  modelSelect.innerHTML = uniqueModels
    .map((model) => `<option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`)
    .join("");
  modelSelect.value = aiConfig.model;
};

const applyConfigToUi = () => {
  renderProviderOptions();
  renderModelSuggestions();
  renderComposerModelOptions();

  if (configProviderSelect) {
    configProviderSelect.value = aiConfig.provider;
  }

  if (providerSelect) {
    providerSelect.value = aiConfig.provider;
  }

  if (configModelInput) {
    configModelInput.value = aiConfig.model;
  }

  if (configApiKeyInput) {
    configApiKeyInput.value = "";
  }

  if (configHint) {
    configHint.textContent = aiConfig.apiKeySet
      ? "已保存 API_KEY；留空保存时不会覆盖现有 Key。"
      : "当前没有保存 API_KEY，请填写后保存。";
  }
};

const loadConfig = async () => {
  try {
    const response = await fetch("/api/config");

    if (!response.ok) {
      applyConfigToUi();
      return;
    }

    const data = await response.json();
    aiConfig = {
      ...aiConfig,
      ...data,
      providers: Array.isArray(data.providers) && data.providers.length ? data.providers : aiConfig.providers,
    };
    applyConfigToUi();
  } catch {
    applyConfigToUi();
  }
};

const applyTtsConfigToUi = () => {
  if (ttsConfigModelInput) {
    ttsConfigModelInput.value = ttsConfig.model || "mimo-v2.5-tts";
  }

  if (ttsConfigVoiceInput) {
    ttsConfigVoiceInput.value = ttsConfig.voice || "mimo_default";
  }

  if (ttsConfigApiKeyInput) {
    ttsConfigApiKeyInput.value = "";
  }

  if (ttsConfigHint) {
    if (ttsConfig.apiKeySet) {
      ttsConfigHint.textContent = "已保存语音 API_KEY；留空保存时不会覆盖现有 Key。";
    } else if (ttsConfig.fallbackApiKeySet) {
      ttsConfigHint.textContent = "未单独保存语音 API_KEY，当前会复用 MIMO_API_KEY。";
    } else {
      ttsConfigHint.textContent = "当前没有保存语音 API_KEY，请填写后保存。";
    }
  }
};

const loadTtsConfig = async () => {
  try {
    const response = await fetch("/api/tts-config");

    if (!response.ok) {
      applyTtsConfigToUi();
      return;
    }

    const data = await response.json();
    ttsConfig = {
      ...ttsConfig,
      ...data,
    };
    applyTtsConfigToUi();
  } catch {
    applyTtsConfigToUi();
  }
};

function currentConversation() {
  return conversations.find((item) => item.id === activeConversationId);
}

const updateHeroVisibility = () => {
  const active = currentConversation();

  if (chatHero) {
    chatHero.hidden = Boolean(active?.messages.length);
  }
};

function createConversation() {
  const conversationItem = {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    title: "新对话",
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  conversations.unshift(conversationItem);
  activeConversationId = conversationItem.id;
  saveConversations();
  return conversationItem.id;
}

const formatTime = () => {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
};

const escapeHtml = (value) => {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

const multilineHtml = (value) => {
  return escapeHtml(value).replace(/\n/g, "<br />");
};

const stripCitations = (value) => {
  return value
    .replace(/[（(]\s*citation:\s*\d+\s*[）)]/gi, "")
    .replace(/[【\[]\s*citation:\s*\d+\s*[】\]]/gi, "")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
};

const normalizeMarkdown = (value) => {
  return stripCitations(value)
    .replace(/^你好[呀啊，,!\s！。]*我是小米的?MiMo[。！!，,\s]*/i, "")
    .replace(/^你好[呀啊，,!\s！。]*我是MiMo[。！!，,\s]*/i, "")
    .replace(/^很高兴为你服务[。！!，,\s]*/i, "")
    .replace(/^\s*#{1,6}\s*$/gm, "")
    .replace(/([^\n])(\s*#{1,3}\s+)/g, "$1\n\n$2")
    .replace(/([^\n])(\s+\d+[.、]\s+)/g, "$1\n$2")
    .replace(/([^\n])(\s+[-*]\s+)/g, "$1\n$2")
    .replace(/([。！？；])\s+(?=\S)/g, "$1\n\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
};

const speechText = (value) => {
  return normalizeMarkdown(value)
    .replace(/```[\s\S]*?```/g, "这里有一段代码，已省略朗读。")
    .replace(/[`*_>#]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .slice(0, 3000);
};

const registerSpeechText = (value) => {
  const id = crypto.randomUUID ? crypto.randomUUID() : `speech-${Date.now()}-${speechStore.size}`;
  speechStore.set(id, speechText(value));
  return id;
};

const registerCopyText = (value) => {
  const id = crypto.randomUUID ? crypto.randomUUID() : `copy-${Date.now()}-${copyStore.size}`;
  copyStore.set(id, normalizeMarkdown(value));
  return id;
};

const renderMarkdown = (value) => {
  value = normalizeMarkdown(value);
  const blocks = [];
  const lines = value.split("\n");
  let paragraph = [];
  let listItems = [];
  let codeLines = [];
  let tableRows = [];
  let inCode = false;

  const inlineMarkdown = (text) => {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  };

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push(`<p>${paragraph.map(inlineMarkdown).join("<br />")}</p>`);
      paragraph = [];
    }
  };

  const flushList = () => {
    if (listItems.length) {
      blocks.push(`<ul>${listItems.map((item) => `<li>${inlineMarkdown(item)}</li>`).join("")}</ul>`);
      listItems = [];
    }
  };

  const flushCode = () => {
    if (codeLines.length) {
      blocks.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
      codeLines = [];
    }
  };

  const isTableSeparator = (line) => {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  };

  const isHorizontalRule = (line) => {
    return /^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line);
  };

  const parseTableRow = (line) => {
    const trimmed = line.trim();

    if (!trimmed.includes("|")) {
      return null;
    }

    const cells = trimmed
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());

    return cells.length > 1 ? cells : null;
  };

  const flushTable = () => {
    if (tableRows.length < 2) {
      tableRows.forEach((row) => paragraph.push(row.join(" | ")));
      tableRows = [];
      return;
    }

    const [headers, ...rows] = tableRows;
    blocks.push(`
      <div class="table-wrap">
        <table>
          <thead>
            <tr>${headers.map((cell) => `<th>${inlineMarkdown(cell)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${rows.map((row) => `<tr>${row.map((cell) => `<td>${inlineMarkdown(cell)}</td>`).join("")}</tr>`).join("")}
          </tbody>
        </table>
      </div>
    `);
    tableRows = [];
  };

  lines.forEach((line) => {
    if (line.trim().startsWith("```")) {
      if (inCode) {
        flushCode();
        inCode = false;
      } else {
        flushParagraph();
        flushList();
        flushTable();
        inCode = true;
      }
      return;
    }

    if (inCode) {
      codeLines.push(line);
      return;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    const list = line.match(/^\s*(?:[-*]|\d+[.、])\s+(.+)$/);
    const tableRow = parseTableRow(line);

    if (!line.trim()) {
      flushParagraph();
      flushList();
      flushTable();
      return;
    }

    if (isHorizontalRule(line)) {
      flushParagraph();
      flushList();
      flushTable();
      return;
    }

    if (tableRow || (tableRows.length && isTableSeparator(line))) {
      flushParagraph();
      flushList();

      if (!isTableSeparator(line)) {
        tableRows.push(tableRow);
      }

      return;
    }

    if (heading) {
      flushParagraph();
      flushList();
      flushTable();
      const level = Math.min(heading[1].length + 2, 5);
      blocks.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      return;
    }

    if (list) {
      flushParagraph();
      flushTable();
      listItems.push(list[1]);
      return;
    }

    flushList();
    flushTable();
    paragraph.push(line);
  });

  flushParagraph();
  flushList();
  flushTable();
  flushCode();

  return blocks.join("");
};

const scrollToLatest = () => {
  conversation.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "end" });
};

const resizeInput = () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 105)}px`;
};

const setLoading = (isLoading) => {
  isGenerating = isLoading;

  if (sendButton) {
    sendButton.disabled = false;
    sendButton.classList.toggle("stop-button", isLoading);
    sendButton.setAttribute("aria-label", isLoading ? "停止生成" : "发送");
    sendButton.innerHTML = isLoading ? stopIcon : sendIcon;
  }
};

const setError = (message = "") => {
  chatError.textContent = message;
};

const messageActions = (speechId = "", copyId = "") => {
  return `
    <div class="message-actions">
      <button class="speech-button" type="button" aria-label="朗读回复" data-speech-id="${speechId}">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M11 5L6 9H3V15H6L11 19V5Z" />
          <path d="M16 9.5A4 4 0 0 1 16 14.5" />
          <path d="M19 7A8 8 0 0 1 19 17" />
        </svg>
      </button>
      <button class="copy-button" type="button" aria-label="复制" data-copy-id="${copyId}">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M8 8H19V19H8Z" />
          <path d="M5 16H4A1 1 0 0 1 3 15V5A1 1 0 0 1 4 4H14A1 1 0 0 1 15 5V6" />
        </svg>
      </button>
    </div>
  `;
};

const tokenUsageText = (usage = null) => {
  if (!usage || typeof usage !== "object") {
    return "";
  }

  const promptTokens = usage.prompt_tokens ?? usage.promptTokens ?? usage.input_tokens ?? usage.inputTokens;
  const completionTokens =
    usage.completion_tokens ?? usage.completionTokens ?? usage.output_tokens ?? usage.outputTokens;
  const totalTokens = usage.total_tokens ?? usage.totalTokens ?? usage.total;
  const parts = [];

  if (Number.isFinite(Number(promptTokens))) {
    parts.push(`输入 ${Number(promptTokens)}`);
  }

  if (Number.isFinite(Number(completionTokens))) {
    parts.push(`输出 ${Number(completionTokens)}`);
  }

  if (Number.isFinite(Number(totalTokens))) {
    parts.push(`总计 ${Number(totalTokens)}`);
  }

  return parts.length ? `Token：${parts.join(" / ")}` : "";
};

const addUserMessage = (message, time = formatTime()) => {
  conversation.insertAdjacentHTML(
    "beforeend",
    `
      <article class="message-row user-row">
        <div class="message-bubble user-bubble">
          <p>${multilineHtml(message)}</p>
          <time>${time}</time>
        </div>
        <span class="avatar user-avatar">L</span>
      </article>
    `
  );
  return conversation.lastElementChild;
};

const addAssistantMessage = (message, reasoning = "", time = formatTime(), warning = "", usage = null) => {
  message = normalizeMarkdown(message);
  reasoning = normalizeMarkdown(reasoning);
  warning = normalizeMarkdown(warning);
  const speechId = registerSpeechText(message);
  const copyId = registerCopyText(message);
  const usageText = tokenUsageText(usage);
  const reasoningBlock = reasoning
    ? `
      <details class="reasoning-block">
        <summary>思考过程</summary>
        <div class="markdown-body">${renderMarkdown(reasoning)}</div>
      </details>
    `
    : "";
  const warningBlock = warning ? `<p class="response-warning">${multilineHtml(warning)}</p>` : "";
  const usageBlock = usageText ? `<p class="token-usage">${escapeHtml(usageText)}</p>` : "";

  conversation.insertAdjacentHTML(
    "beforeend",
    `
      <article class="message-row assistant-row">
        <span class="bot-avatar" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M9 7V5A3 3 0 0 1 15 5V7" />
            <path d="M6 10A3 3 0 0 1 9 7H15A3 3 0 0 1 18 10V15A5 5 0 0 1 13 20H11A5 5 0 0 1 6 15V10Z" />
            <path d="M9 12H9.01" />
            <path d="M15 12H15.01" />
            <path d="M10 16C11.25 17 12.75 17 14 16" />
          </svg>
        </span>
        <div class="message-bubble assistant-bubble">
          <div class="markdown-body">${renderMarkdown(message)}</div>
          ${warningBlock}
          ${reasoningBlock}
          ${messageActions(speechId, copyId)}
          ${usageBlock}
          <time>${time}</time>
        </div>
      </article>
    `
  );
  return conversation.lastElementChild;
};

const stopSpeech = () => {
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.removeAttribute("src");
  }

  if (activeAudioUrl) {
    URL.revokeObjectURL(activeAudioUrl);
  }

  activeSpeechButton?.classList.remove("loading", "playing");
  activeAudio = null;
  activeAudioUrl = "";
  activeSpeechButton = null;
};

const playSpeech = async (button) => {
  const text = speechStore.get(button.dataset.speechId);

  if (!text) {
    setError("没有可朗读的内容。");
    return;
  }

  if (activeSpeechButton === button && activeAudio) {
    stopSpeech();
    return;
  }

  stopSpeech();
  setError("");
  button.classList.add("loading");
  activeSpeechButton = button;

  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        style: "",
      }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const detailMessage =
        data.detail?.error?.message || data.detail?.message || data.detail?.raw || data.error || "语音生成失败";
      throw new Error(detailMessage);
    }

    const blob = await response.blob();
    activeAudioUrl = URL.createObjectURL(blob);
    activeAudio = new Audio(activeAudioUrl);
    button.classList.remove("loading");
    button.classList.add("playing");

    activeAudio.addEventListener("ended", stopSpeech, { once: true });
    activeAudio.addEventListener("error", () => {
      setError("音频播放失败，请稍后重试。");
      stopSpeech();
    });

    await activeAudio.play();
  } catch (error) {
    setError(error.message || "语音生成失败");
    stopSpeech();
  }
};

const copyText = async (button) => {
  const text = copyStore.get(button.dataset.copyId);

  if (!text) {
    setError("没有可复制的内容。");
    return;
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
    }

    setError("");
    button.classList.add("copied");
    button.setAttribute("aria-label", "已复制");
    setTimeout(() => {
      button.classList.remove("copied");
      button.setAttribute("aria-label", "复制");
    }, 1200);
  } catch {
    setError("复制失败，请检查浏览器剪贴板权限。");
  }
};

const addThinkingMessage = () => {
  const id = `thinking-${Date.now()}`;
  conversation.insertAdjacentHTML(
    "beforeend",
    `
      <article class="message-row assistant-row thinking-row" id="${id}">
        <span class="bot-avatar" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M9 7V5A3 3 0 0 1 15 5V7" />
            <path d="M6 10A3 3 0 0 1 9 7H15A3 3 0 0 1 18 10V15A5 5 0 0 1 13 20H11A5 5 0 0 1 6 15V10Z" />
            <path d="M9 12H9.01" />
            <path d="M15 12H15.01" />
            <path d="M10 16C11.25 17 12.75 17 14 16" />
          </svg>
        </span>
        <div class="message-bubble assistant-bubble thinking-bubble">
          <span class="thinking-spinner" aria-hidden="true"></span>
          <span>正在思考</span>
        </div>
      </article>
    `
  );
  return document.getElementById(id);
};

const renderConversation = () => {
  const active = currentConversation();
  conversation.innerHTML = "";
  updateHeroVisibility();

  active?.messages.forEach((message) => {
    if (message.role === "user") {
      addUserMessage(message.displayContent || message.content, message.time);
    }

    if (message.role === "assistant") {
      addAssistantMessage(
        message.content,
        message.reasoning || "",
        message.time,
        message.warning || "",
        message.usage || null
      );
    }
  });
};

const renderHistory = () => {
  const realConversations = conversations.filter((item) => item.messages.length > 0);
  historyList.innerHTML = "";
  historyEmpty.hidden = realConversations.length > 0;

  realConversations.forEach((item) => {
    historyList.insertAdjacentHTML(
      "beforeend",
      `
        <button class="history-item ${item.id === activeConversationId ? "active" : ""}" type="button" data-id="${item.id}">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M21 15A4 4 0 0 1 17 19H8L3 22V7A4 4 0 0 1 7 3H17A4 4 0 0 1 21 7Z" />
          </svg>
          ${escapeHtml(item.title)}
        </button>
      `
    );
  });
};

const updateConversationMeta = (userMessage) => {
  const active = currentConversation();
  active.updatedAt = Date.now();

  if (active.title === "新对话") {
    active.title = userMessage.slice(0, 24);
  }

  conversations = [active, ...conversations.filter((item) => item.id !== active.id)];
  activeConversationId = active.id;
};

const renderAttachments = () => {
  attachmentList.innerHTML = pendingAttachments
    .map(
      (file, index) => `
        <span class="attachment-chip">
          ${escapeHtml(file.name)}
          <button type="button" aria-label="移除附件" data-attachment-index="${index}">×</button>
        </span>
      `
    )
    .join("");
};

const readAttachment = (file) => {
  return new Promise((resolve) => {
    const isReadable = textFilePattern.test(file.type) || readableExtensions.test(file.name);

    if (!isReadable) {
      resolve(`附件：${file.name}，类型：${file.type || "未知"}，大小：${file.size} bytes。非文本附件已记录文件信息。`);
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      resolve(`附件：${file.name}\n${String(reader.result || "")}`);
    };

    reader.onerror = () => {
      resolve(`附件：${file.name} 读取失败。`);
    };

    reader.readAsText(file);
  });
};

const addAttachments = (files = []) => {
  const nextFiles = Array.from(files).filter(Boolean);

  if (!nextFiles.length) {
    return;
  }

  pendingAttachments = [...pendingAttachments, ...nextFiles];
  setError("");
  renderAttachments();
};

const buildUserContent = async (message) => {
  if (!pendingAttachments.length) {
    return message;
  }

  const attachmentTexts = await Promise.all(pendingAttachments.map(readAttachment));
  return `${message}\n\n以下是本轮用户上传的附件内容：\n${attachmentTexts.join("\n\n---\n\n")}`;
};

const requestReply = async (signal) => {
  const active = currentConversation();
  const response = await fetch("/api/chat", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      provider: providerSelect?.value || aiConfig.provider,
      model: modelSelect.value,
      thinking: thinkingToggle.checked,
      webSearch: currentUser?.role === "admin" && searchToggle?.checked,
      messages: [systemPrompt, ...active.messages.map(({ role, content }) => ({ role, content }))],
    }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || "AI 请求失败");
  }

  return {
    content: data.content || "没有收到有效回复。",
    reasoning: data.reasoning || "",
    finishReason: data.finishReason || "",
    usage: data.usage || null,
  };
};

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (isGenerating) {
    activeChatController?.abort();
    return;
  }

  const message = input.value.trim();

  if (!message && !pendingAttachments.length) {
    return;
  }

  const active = currentConversation();
  const displayContent = pendingAttachments.length
    ? `${message || "请分析附件"}\n\n附件：${pendingAttachments.map((file) => file.name).join("、")}`
    : message;

  setError("");
  setLoading(true);

  try {
    const content = await buildUserContent(message || "请分析附件");
    const time = formatTime();
    active.messages.push({ role: "user", content, displayContent, time });
    updateHeroVisibility();
    updateConversationMeta(message || pendingAttachments[0]?.name || "附件对话");
    addUserMessage(displayContent, time);
    input.value = "";
    pendingAttachments = [];
    renderAttachments();
    resizeInput();
    renderHistory();
    scrollToLatest();

    const thinkingMessage = addThinkingMessage();
    activeChatController = new AbortController();
    scrollToLatest();
    const reply = await requestReply(activeChatController.signal);
    reply.content = normalizeMarkdown(reply.content);
    reply.reasoning = normalizeMarkdown(reply.reasoning);
    const isTruncated = ["length", "max_tokens", "content_filter"].includes(reply.finishReason);
    const warning = isTruncated ? "回复可能因为长度限制没有完整生成，可以让我“继续上面的内容”。" : "";
    thinkingMessage?.remove();
    const replyTime = formatTime();
    active.messages.push({
      role: "assistant",
      content: reply.content,
      reasoning: reply.reasoning,
      warning,
      usage: reply.usage,
      time: replyTime,
    });
    active.updatedAt = Date.now();
    saveConversations();
    addAssistantMessage(reply.content, reply.reasoning, replyTime, warning, reply.usage);
  } catch (error) {
    document.querySelector(".thinking-row")?.remove();

    if (error.name === "AbortError") {
      setError("");
      return;
    }

    const fallback = error.message || "请求失败，请稍后再试。";
    setError(fallback);
    addAssistantMessage(`请求失败：${fallback}`);
  } finally {
    activeChatController = null;
    saveConversations();
    renderHistory();
    setLoading(false);
    input.focus();
    scrollToLatest();
  }
});

input?.addEventListener("input", resizeInput);

input?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    form.requestSubmit();
  }
});

historyList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-id]");

  if (!button) {
    return;
  }

  activeConversationId = button.dataset.id;
  stopSpeech();
  setError("");
  renderConversation();
  renderHistory();
  scrollToLatest();
});

conversation?.addEventListener("click", (event) => {
  const speechButton = event.target.closest("[data-speech-id]");
  const copyButton = event.target.closest("[data-copy-id]");

  if (speechButton) {
    playSpeech(speechButton);
    return;
  }

  if (copyButton) {
    copyText(copyButton);
  }
});

newChatButton?.addEventListener("click", () => {
  activeConversationId = createConversation();
  stopSpeech();
  pendingAttachments = [];
  input.value = "";
  setError("");
  renderAttachments();
  renderConversation();
  renderHistory();
  input.focus();
});

attachButton?.addEventListener("click", () => {
  fileInput.click();
});

fileInput?.addEventListener("change", () => {
  addAttachments(fileInput.files || []);
  fileInput.value = "";
});

const handleDroppedFiles = (event) => {
  const files = Array.from(event.dataTransfer?.files || []);

  if (!files.length) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();
  addAttachments(files);
};

["dragenter", "dragover"].forEach((eventName) => {
  document.addEventListener(eventName, (event) => {
    if (event.dataTransfer?.types?.includes("Files")) {
      event.preventDefault();
      form?.classList.add("drag-over");
    }
  });

  form?.addEventListener(eventName, (event) => {
    event.preventDefault();
    form.classList.add("drag-over");
  });

  conversation?.addEventListener(eventName, (event) => {
    if (event.dataTransfer?.types?.includes("Files")) {
      event.preventDefault();
      form?.classList.add("drag-over");
    }
  });
});

["dragleave", "drop"].forEach((eventName) => {
  document.addEventListener(eventName, (event) => {
    if (eventName === "drop") {
      form?.classList.remove("drag-over");
    }
  });

  form?.addEventListener(eventName, () => {
    form.classList.remove("drag-over");
  });

  conversation?.addEventListener(eventName, () => {
    form?.classList.remove("drag-over");
  });
});

form?.addEventListener("drop", handleDroppedFiles);
conversation?.addEventListener("drop", handleDroppedFiles);
document.addEventListener("drop", handleDroppedFiles);

attachmentList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-attachment-index]");

  if (!button) {
    return;
  }

  pendingAttachments.splice(Number(button.dataset.attachmentIndex), 1);
  renderAttachments();
});

voiceButton?.addEventListener("click", () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    setError("当前浏览器不支持语音转文字，建议使用 Chrome 或 Edge。");
    return;
  }

  if (!recognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "zh-CN";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event) => {
      const text = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join("");
      input.value = `${voiceBaseText}${text}`;
      resizeInput();
    };

    recognition.onerror = () => {
      setError("语音识别失败，请检查麦克风权限。");
      voiceButton.classList.remove("recording");
    };

    recognition.onend = () => {
      voiceButton.classList.remove("recording");
    };
  }

  setError("");
  voiceBaseText = input.value;
  voiceButton.classList.add("recording");
  recognition.start();
});

settingsButton?.addEventListener("click", () => {
  settingsMenu.classList.toggle("open");
});

configOpen?.addEventListener("click", () => {
  settingsMenu.classList.remove("open");
  applyConfigToUi();
  configModal.hidden = false;
  configModelInput?.focus();
});

ttsConfigOpen?.addEventListener("click", () => {
  settingsMenu.classList.remove("open");
  applyTtsConfigToUi();
  ttsConfigModal.hidden = false;
  ttsConfigModelInput?.focus();
});

configCancel?.addEventListener("click", () => {
  configModal.hidden = true;
  configForm.reset();
  applyConfigToUi();
});

ttsConfigCancel?.addEventListener("click", () => {
  ttsConfigModal.hidden = true;
  ttsConfigForm.reset();
  applyTtsConfigToUi();
});

providerSelect?.addEventListener("change", () => {
  aiConfig.provider = providerSelect.value;
  const models = modelOptionsForProvider(providerSelect.value);

  if (models.length) {
    aiConfig.model = models[0];
  }

  renderModelSuggestions(providerSelect.value);
  renderComposerModelOptions();

  if (configProviderSelect) {
    configProviderSelect.value = aiConfig.provider;
  }

  if (configModelInput) {
    configModelInput.value = aiConfig.model;
  }
});

configProviderSelect?.addEventListener("change", () => {
  const models = modelOptionsForProvider(configProviderSelect.value);
  renderModelSuggestions(configProviderSelect.value);

  if (models.length) {
    configModelInput.value = models[0];
  }
});

configForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const formData = new FormData(configForm);
    const response = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: formData.get("provider"),
        model: formData.get("model"),
        apiKey: formData.get("apiKey"),
      }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setError(data.error || "保存配置失败");
      return;
    }

    aiConfig = {
      ...aiConfig,
      ...(data.config || {}),
      providers:
        Array.isArray(data.config?.providers) && data.config.providers.length
          ? data.config.providers
          : aiConfig.providers,
    };
    applyConfigToUi();
    setError("配置已保存");
    configModal.hidden = true;
    configForm.reset();
  } catch (error) {
    setError(error.message || "保存配置失败");
  }
});

ttsConfigForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const formData = new FormData(ttsConfigForm);
    const response = await fetch("/api/tts-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: formData.get("model"),
        voice: formData.get("voice"),
        apiKey: formData.get("apiKey"),
      }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setError(data.error || "保存语音配置失败");
      return;
    }

    ttsConfig = {
      ...ttsConfig,
      ...(data.config || {}),
    };
    applyTtsConfigToUi();
    setError("语音配置已保存");
    ttsConfigModal.hidden = true;
    ttsConfigForm.reset();
  } catch (error) {
    setError(error.message || "保存语音配置失败");
  }
});

const ensureAuth = async () => {
  await loadConfig();
  await loadTtsConfig();
  const response = await fetch("/api/auth/me");

  if (!response.ok) {
    window.location.href = "/";
    return;
  }

  const data = await response.json();
  currentUser = data.user;
  profileName.textContent = currentUser.displayName || currentUser.username;
  adminOnlyLinks.forEach((item) => {
    item.hidden = currentUser.role !== "admin";
  });

  if (searchToggle) {
    const canUseSearch = currentUser.role === "admin";
    searchToggle.disabled = !canUseSearch;
    searchToggle.checked = false;
    searchToggle.closest(".search-control")?.classList.toggle("disabled-control", !canUseSearch);
  }

  if (currentUser.role === "admin") {
    refreshPendingBadge();
  }
  conversations = await loadConversations();
  activeConversationId = conversations[0]?.id || createConversation();
  renderConversation();
  renderHistory();
  renderAttachments();
};

const refreshPendingBadge = async () => {
  const response = await fetch("/api/admin/users");

  if (!response.ok) {
    return;
  }

  const data = await response.json();
  const hasPending = (data.users || []).some((user) => user.status === "pending");
  reviewLinks.forEach((item) => {
    item.classList.toggle("has-pending", hasPending);
  });
};

ensureAuth();
