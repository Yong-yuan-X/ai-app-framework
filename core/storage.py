import json
import sqlite3
import time

from .settings import (
    CONVERSATION_RETENTION_SECONDS,
    DATA_DIR,
    DB_PATH,
    LOCAL_USER,
    MAX_CONVERSATION_MESSAGES,
    MAX_CONVERSATIONS,
)


def db_connection():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_conversations (
              id TEXT NOT NULL,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              messages_json TEXT NOT NULL,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL,
              PRIMARY KEY (user_id, id)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_conversations_updated ON ai_conversations (updated_at)"
        )


def cleanup_old_conversations(connection):
    cutoff = int((time.time() - CONVERSATION_RETENTION_SECONDS) * 1000)
    connection.execute("DELETE FROM ai_conversations WHERE updated_at < ?", (cutoff,))


def clean_message_for_storage(message):
    if not isinstance(message, dict):
        return None

    role = message.get("role")

    if role not in {"user", "assistant"}:
        return None

    cleaned = {"role": role}

    for key in ("content", "displayContent", "reasoning", "warning", "time"):
        value = message.get(key)

        if isinstance(value, str):
            cleaned[key] = value[:40000]

    usage = message.get("usage")

    if isinstance(usage, dict):
        cleaned["usage"] = usage

    if not cleaned.get("content"):
        return None

    return cleaned


def clean_conversation_for_storage(conversation):
    if not isinstance(conversation, dict):
        return None

    conversation_id = str(conversation.get("id", "")).strip()[:80]
    messages = [clean_message_for_storage(item) for item in conversation.get("messages", [])]
    messages = [item for item in messages if item][-MAX_CONVERSATION_MESSAGES:]

    if not conversation_id or not messages:
        return None

    now_ms = int(time.time() * 1000)

    return {
        "id": conversation_id,
        "title": str(conversation.get("title") or "新对话")[:80],
        "messages": messages,
        "createdAt": int(conversation.get("createdAt") or now_ms),
        "updatedAt": int(conversation.get("updatedAt") or now_ms),
    }


def load_conversations():
    conversations = []

    with db_connection() as connection:
        cleanup_old_conversations(connection)
        rows = connection.execute(
            """
            SELECT id, title, messages_json, created_at, updated_at
            FROM ai_conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (LOCAL_USER["id"], MAX_CONVERSATIONS),
        ).fetchall()

        for row in rows:
            try:
                messages = json.loads(row["messages_json"])
            except json.JSONDecodeError:
                messages = []

            conversations.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "messages": messages,
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                }
            )

    return conversations


def save_conversations(conversations):
    cleaned_conversations = [
        clean_conversation_for_storage(conversation) for conversation in conversations[:MAX_CONVERSATIONS]
    ]
    cleaned_conversations = [conversation for conversation in cleaned_conversations if conversation]

    with db_connection() as connection:
        cleanup_old_conversations(connection)

        for conversation in cleaned_conversations:
            connection.execute(
                """
                INSERT INTO ai_conversations (
                  id, user_id, title, messages_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, id) DO UPDATE SET
                  title = excluded.title,
                  messages_json = excluded.messages_json,
                  updated_at = excluded.updated_at
                """,
                (
                    conversation["id"],
                    LOCAL_USER["id"],
                    conversation["title"],
                    json.dumps(conversation["messages"], ensure_ascii=False),
                    conversation["createdAt"],
                    conversation["updatedAt"],
                ),
            )

        if cleaned_conversations:
            connection.execute(
                """
                DELETE FROM ai_conversations
                WHERE user_id = ?
                AND id NOT IN (
                  SELECT id FROM ai_conversations
                  WHERE user_id = ?
                  ORDER BY updated_at DESC
                  LIMIT ?
                )
                """,
                (LOCAL_USER["id"], LOCAL_USER["id"], MAX_CONVERSATIONS),
            )

    return len(cleaned_conversations)
