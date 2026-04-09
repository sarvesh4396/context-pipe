# packages/context-pipe-redis/src/context_pipe_redis/__init__.py

import asyncio
import json
from dataclasses import asdict
from typing import Optional, Union

import redis
import redis.asyncio as redis_async

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation


class RedisBackend(AbstractBackend):
    """Redis backend for storing conversations.

    Stores conversations as JSON strings in Redis with optional TTL.
    Supports both sync and async operations.
    """

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

    def _key(self, conversation_id: int) -> str:
        """Generate a Redis key for a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            The full Redis key.
        """
        return f"{self.prefix}{conversation_id}"

    # Sync versions
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
                default=str,  # Handle datetime serialization
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
            return Conversation(**parsed)

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
    async def asave(self, conversation: Conversation) -> None:
        """Save a conversation to Redis (async).

        Args:
            conversation: The conversation to save.
        """
        key = self._key(conversation.id)
        data = json.dumps(
            asdict(conversation),
            default=str,  # Handle datetime serialization
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
        return Conversation(**parsed)

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
