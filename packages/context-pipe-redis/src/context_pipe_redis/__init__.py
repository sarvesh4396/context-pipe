# packages/context-pipe-redis/src/context_pipe_redis/__init__.py

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Literal, Optional, Union

import redis
import redis.asyncio as redis_async

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation, Message, Role, Summary


def _json_serializer(obj: object) -> str:
    """Custom JSON serializer for objects not serializable by default.

    Args:
        obj: The object to serialize.

    Returns:
        The serialized string representation.
    """
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class RedisBackend(AbstractBackend):
    """Redis backend for storing conversations.

    Stores conversations as JSON strings in Redis with optional TTL.
    Supports both sync and async operations.
    """

    GLOBAL_CONVERSATION_COUNTER_KEY = "conversation:id"
    GLOBAL_MESSAGE_COUNTER_KEY = "message:id"
    GLOBAL_SUMMARY_COUNTER_KEY = "summary:id"

    def __init__(
        self,
        client: redis.Redis | redis_async.Redis,
        prefix: str = "context-pipe:",
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize the Redis backend.

        Args:
            client: The redis.Redis (sync) or redis.asyncio.Redis (async) client instance.
            prefix: The prefix for all Redis keys (default: "context-pipe:").
            ttl_seconds: Optional time-to-live in seconds for stored conversations.
        """
        self.client = client
        self.is_async = isinstance(client, redis_async.Redis)
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def _key(self, of: Literal["conversation", "message", "summary"]) -> str:
        """Generate a Redis key for a conversation, message, or summary.

        Args:
            of: The type of the entity ("conversation", "message", or "summary").

        Returns:
            The full Redis key.
        """
        if of == "conversation":
            return f"{self.prefix}{self.GLOBAL_CONVERSATION_COUNTER_KEY}"
        elif of == "message":
            return f"{self.prefix}{self.GLOBAL_MESSAGE_COUNTER_KEY}"
        elif of == "summary":
            return f"{self.prefix}{self.GLOBAL_SUMMARY_COUNTER_KEY}"
        else:
            raise ValueError(f"Unknown entity type: {of}")

    def _build_object_key(
        self, of: Literal["conversation", "message", "summary"], object_id: int | str
    ) -> str:
        """Build the Redis key for a specific conversation, message, or summary.

        Args:
            of: The type of the entity ("conversation", "message", or "summary").
            object_id: The ID of the specific object.

        Returns:
            The full Redis key for the object.
        """
        return f"{self.prefix}{of}:{object_id}"

    @staticmethod
    def _deserialize_conversation(data: dict[str, object]) -> Conversation:
        """Deserialize a stored conversation dict back to a Conversation object.

        Args:
            data: The stored conversation data (dict).

        Returns:
            A properly typed Conversation object.
        """
        # Deserialize messages
        messages = []
        for msg_dict in data.get("messages", []):  # type: ignore
            msg = Message(
                role=Role(msg_dict["role"])
                if isinstance(msg_dict["role"], str)
                else msg_dict["role"],
                content=msg_dict["content"],
                token_count=msg_dict.get("token_count", 0),
                metadata=msg_dict.get("metadata", {}),
                created_at=datetime.fromisoformat(msg_dict["created_at"])
                if isinstance(msg_dict["created_at"], str)
                else msg_dict["created_at"],
            )
            messages.append(msg)

        # Deserialize summaries
        summaries = []
        for s_dict in data.get("summaries", []):  # type: ignore
            s = Summary(
                text=s_dict["text"],
                span_start=s_dict["span_start"],
                span_end=s_dict["span_end"],
                compacted_at=datetime.fromisoformat(s_dict["compacted_at"])
                if isinstance(s_dict["compacted_at"], str)
                else s_dict["compacted_at"],
            )
            summaries.append(s)

        return Conversation(
            id=data["id"],  # type: ignore
            messages=messages,
            summaries=summaries,
        )

    # Sync versions
    def create(self) -> Conversation:
        """Create a new conversation with an auto-generated ID (sync).

        Returns:
            A new Conversation instance with auto-generated ID.
        """
        if self.is_async:
            return asyncio.run(self.acreate())

        # Atomic ID generation
        conversation_id = int(self.client.incr(self._key("conversation")))  # type: ignore[union-attr]

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        # Optional: persist immediately
        self.save(conversation)

        return conversation

    def save(self, conversation: Conversation) -> None:
        """Save a conversation to Redis (sync).

        Args:
            conversation: The conversation to save.
        """
        if self.is_async:
            asyncio.run(self.asave(conversation))
        else:
            key = self._key(conversation.id)
            data = json.dumps(
                asdict(conversation),
                default=_json_serializer,
            )

            if self.ttl_seconds:
                self.client.setex(key, self.ttl_seconds, data)  # type: ignore[union-attr]
            else:
                self.client.set(key, data)  # type: ignore[union-attr]

    def load(self, conversation_id: int) -> Conversation:
        """Load a conversation from Redis (sync).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        if self.is_async:
            return asyncio.run(self.aload(conversation_id))
        else:
            key = self._key(conversation_id)
            data = self.client.get(key)  # type: ignore[union-attr]

            if data is None:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            parsed = json.loads(data)
            return self._deserialize_conversation(parsed)

    def delete(self, conversation_id: int) -> None:
        """Delete a conversation from Redis (sync).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        if self.is_async:
            asyncio.run(self.adelete(conversation_id))
        else:
            key = self._key(conversation_id)
            self.client.delete(key)  # type: ignore[union-attr]

    def exists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in Redis (sync).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        if self.is_async:
            return asyncio.run(self.aexists(conversation_id))
        else:
            key = self._key(conversation_id)
            return bool(self.client.exists(key))  # type: ignore[union-attr]

    # Async versions
    async def acreate(self) -> Conversation:
        """Create a new conversation with an auto-generated ID (async).

        Returns:
            A new Conversation instance with auto-generated ID.
        """

        conversation_id = int(await self.client.incr(self._key("conversation")))  # type: ignore[union-attr]

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        # Optional: persist immediately
        await self.asave(conversation)

        return conversation

    async def asave(self, conversation: Conversation) -> None:
        """Save a conversation to Redis (async).

        Args:
            conversation: The conversation to save.
        """
        key = self._key(conversation.id)
        data = json.dumps(
            asdict(conversation),
            default=_json_serializer,
        )

        if self.ttl_seconds:
            await self.client.setex(key, self.ttl_seconds, data)  # type: ignore[union-attr]
        else:
            await self.client.set(key, data)  # type: ignore[union-attr]

    async def aload(self, conversation_id: int) -> Conversation:
        """Load a conversation from Redis (async).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        key = self._key(conversation_id)
        data = await self.client.get(key)  # type: ignore[union-attr]

        if data is None:
            raise KeyError(f"Conversation '{conversation_id}' not found")

        parsed = json.loads(data)
        return self._deserialize_conversation(parsed)

    async def adelete(self, conversation_id: int) -> None:
        """Delete a conversation from Redis (async).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        key = self._key(conversation_id)
        await self.client.delete(key)  # type: ignore[union-attr]

    async def aexists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in Redis (async).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        key = self._key(conversation_id)
        return bool(await self.client.exists(key))  # type: ignore[union-attr]


__all__ = ["RedisBackend"]
