"""
Stateful conversation management with Redis support.

This module provides conversation history management with support for
both in-memory and Redis-backed storage.
"""
import json
import logging
import time
import uuid
from typing import Optional
from dataclasses import dataclass, asdict

from modules.config.gemini_config import (
    GEMINI_CONVERSATION_ENABLED,
    GEMINI_CONVERSATION_STORAGE,
    GEMINI_CONVERSATION_EXPIRATION_HOURS,
    GEMINI_CONVERSATION_MAX_MESSAGES,
    GEMINI_CONVERSATION_MAX_TOKENS,
    DEFAULT_MODEL,
    FALLBACK_MODEL,
)
from modules.utils.gemini_utils import execute_gemini_with_retry

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    model: Optional[str] = None
    tokens: int = 0


@dataclass
class Conversation:
    """Represents a conversation with its history."""
    conversation_id: str
    title: Optional[str]
    description: Optional[str]
    tags: list[str]
    messages: list[Message]
    created_at: float
    updated_at: float
    expiration_hours: int
    total_tokens: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "messages": [asdict(m) for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expiration_hours": self.expiration_hours,
            "total_tokens": self.total_tokens,
            "message_count": len(self.messages),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Create from dictionary."""
        messages = [
            Message(**m) if isinstance(m, dict) else m
            for m in data.get("messages", [])
        ]
        return cls(
            conversation_id=data["conversation_id"],
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", []),
            messages=messages,
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
            expiration_hours=data.get("expiration_hours", GEMINI_CONVERSATION_EXPIRATION_HOURS),
            total_tokens=data.get("total_tokens", 0),
        )


class ConversationStorage:
    """Base class for conversation storage backends."""

    def save(self, conversation: Conversation) -> bool:
        raise NotImplementedError

    def load(self, conversation_id: str) -> Optional[Conversation]:
        raise NotImplementedError

    def delete(self, conversation_id: str) -> bool:
        raise NotImplementedError

    def list_all(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    def cleanup_expired(self) -> int:
        raise NotImplementedError


class MemoryStorage(ConversationStorage):
    """In-memory conversation storage."""

    def __init__(self):
        self._conversations: dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> bool:
        self._conversations[conversation.conversation_id] = conversation
        return True

    def load(self, conversation_id: str) -> Optional[Conversation]:
        conv = self._conversations.get(conversation_id)
        if conv:
            # Check expiration
            expiration_time = conv.created_at + (conv.expiration_hours * 3600)
            if time.time() > expiration_time:
                self.delete(conversation_id)
                return None
        return conv

    def delete(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def list_all(self, limit: int = 100) -> list[dict]:
        self.cleanup_expired()
        conversations = sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )[:limit]
        return [c.to_dict() for c in conversations]

    def cleanup_expired(self) -> int:
        current_time = time.time()
        expired = [
            cid for cid, conv in self._conversations.items()
            if current_time > conv.created_at + (conv.expiration_hours * 3600)
        ]
        for cid in expired:
            del self._conversations[cid]
        return len(expired)


class RedisStorage(ConversationStorage):
    """Redis-backed conversation storage."""

    def __init__(self):
        self._client = None
        self._prefix = "gemini:conversation:"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Redis client."""
        try:
            from modules.services.redis_cache import get_redis_client
            self._client = get_redis_client()
            logger.info("Redis storage initialized")
        except ImportError:
            logger.warning("Redis cache module not available, falling back to memory")
            self._client = None

    def _key(self, conversation_id: str) -> str:
        return f"{self._prefix}{conversation_id}"

    def save(self, conversation: Conversation) -> bool:
        if not self._client:
            return False
        try:
            key = self._key(conversation.conversation_id)
            data = json.dumps(conversation.to_dict())
            ttl = conversation.expiration_hours * 3600
            self._client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis save error: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[Conversation]:
        if not self._client:
            return None
        try:
            key = self._key(conversation_id)
            data = self._client.get(key)
            if data:
                return Conversation.from_dict(json.loads(data))
            return None
        except Exception as e:
            logger.error(f"Redis load error: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        if not self._client:
            return False
        try:
            key = self._key(conversation_id)
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def list_all(self, limit: int = 100) -> list[dict]:
        if not self._client:
            return []
        try:
            keys = self._client.keys(f"{self._prefix}*")
            conversations = []
            for key in keys[:limit]:
                data = self._client.get(key)
                if data:
                    conv_dict = json.loads(data)
                    conversations.append(conv_dict)
            return sorted(conversations, key=lambda c: c.get("updated_at", 0), reverse=True)
        except Exception as e:
            logger.error(f"Redis list error: {e}")
            return []

    def cleanup_expired(self) -> int:
        # Redis handles expiration automatically via TTL
        return 0


class ConversationManager:
    """Manages conversations with configurable storage backend."""

    def __init__(self):
        self.enabled = GEMINI_CONVERSATION_ENABLED
        self._storage = self._create_storage()
        self._stats = {
            "conversations_created": 0,
            "messages_added": 0,
            "conversations_cleared": 0,
        }

    def _create_storage(self) -> ConversationStorage:
        """Create appropriate storage backend."""
        if GEMINI_CONVERSATION_STORAGE.lower() == "redis":
            storage = RedisStorage()
            if storage._client:
                return storage
            logger.warning("Redis not available, using memory storage")

        return MemoryStorage()

    def create_conversation(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expiration_hours: int = GEMINI_CONVERSATION_EXPIRATION_HOURS
    ) -> dict:
        """Create a new conversation."""
        if not self.enabled:
            return {"error": "Conversations are disabled"}

        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = time.time()

        conversation = Conversation(
            conversation_id=conversation_id,
            title=title or f"Conversation {conversation_id}",
            description=description,
            tags=tags or [],
            messages=[],
            created_at=now,
            updated_at=now,
            expiration_hours=expiration_hours,
        )

        self._storage.save(conversation)
        self._stats["conversations_created"] += 1

        return conversation.to_dict()

    async def continue_conversation(
        self,
        conversation_id: str,
        prompt: str,
        model: Optional[str] = None
    ) -> dict:
        """Continue an existing conversation with a new message."""
        if not self.enabled:
            return {"error": "Conversations are disabled"}

        conversation = self._storage.load(conversation_id)
        if not conversation:
            return {"error": f"Conversation {conversation_id} not found or expired"}

        model = model or DEFAULT_MODEL

        # Build context from conversation history
        context = self._build_context(conversation)

        # Create the full prompt with context
        full_prompt = f"{context}\n\nUser: {prompt}\n\nAssistant:"

        # Execute the prompt
        args = ["--model", model, "--prompt", full_prompt]

        try:
            result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)

            # Add user message
            user_message = Message(
                role="user",
                content=prompt,
                timestamp=time.time(),
                tokens=len(prompt.split())  # Rough estimate
            )
            conversation.messages.append(user_message)

            # Add assistant response
            response_content = result.get("stdout", "")
            assistant_message = Message(
                role="assistant",
                content=response_content,
                timestamp=time.time(),
                model=model,
                tokens=len(response_content.split())  # Rough estimate
            )
            conversation.messages.append(assistant_message)

            # Update conversation
            conversation.updated_at = time.time()
            conversation.total_tokens += user_message.tokens + assistant_message.tokens

            # Prune if necessary
            self._prune_conversation(conversation)

            # Save
            self._storage.save(conversation)
            self._stats["messages_added"] += 2

            return {
                "status": "success",
                "conversation_id": conversation_id,
                "response": response_content,
                "message_count": len(conversation.messages),
                "total_tokens": conversation.total_tokens,
            }

        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            return {"error": str(e)}

    def _build_context(self, conversation: Conversation) -> str:
        """Build context string from conversation history."""
        if not conversation.messages:
            return ""

        context_parts = []
        for message in conversation.messages[-GEMINI_CONVERSATION_MAX_MESSAGES:]:
            role = "User" if message.role == "user" else "Assistant"
            context_parts.append(f"{role}: {message.content}")

        return "\n\n".join(context_parts)

    def _prune_conversation(self, conversation: Conversation):
        """Prune conversation to stay within limits."""
        # Prune by message count
        while len(conversation.messages) > GEMINI_CONVERSATION_MAX_MESSAGES * 2:
            removed = conversation.messages.pop(0)
            conversation.total_tokens -= removed.tokens

        # Prune by token count
        while conversation.total_tokens > GEMINI_CONVERSATION_MAX_TOKENS and conversation.messages:
            removed = conversation.messages.pop(0)
            conversation.total_tokens -= removed.tokens

    def list_conversations(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> list[dict]:
        """List all conversations."""
        conversations = self._storage.list_all(limit)

        if status_filter == "active":
            now = time.time()
            conversations = [
                c for c in conversations
                if now < c.get("created_at", 0) + (c.get("expiration_hours", 24) * 3600)
            ]

        return conversations

    def clear_conversation(self, conversation_id: str) -> dict:
        """Clear/delete a conversation."""
        if self._storage.delete(conversation_id):
            self._stats["conversations_cleared"] += 1
            return {"status": "success", "message": f"Conversation {conversation_id} cleared"}
        return {"status": "error", "message": f"Conversation {conversation_id} not found"}

    def get_stats(self) -> dict:
        """Get conversation system statistics."""
        return {
            **self._stats,
            "storage_backend": type(self._storage).__name__,
            "enabled": self.enabled,
            "active_conversations": len(self._storage.list_all()),
            "max_messages_per_conversation": GEMINI_CONVERSATION_MAX_MESSAGES,
            "max_tokens_per_conversation": GEMINI_CONVERSATION_MAX_TOKENS,
            "default_expiration_hours": GEMINI_CONVERSATION_EXPIRATION_HOURS,
        }
