# packages/context-pipe-memory/src/context_pipe_memory/__init__.py

import asyncio
from dataclasses import asdict
from datetime import datetime
from threading import Lock

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation, Message, Role, Summary


class MemoryBackend(AbstractBackend):
    """In-process memory backend for storing conversations.

    Stores conversations in a dictionary protected by locks
    for thread-safe concurrent access. Supports both sync and async operations.
    """

    def __init__(self) -> None:
        """Initialize the memory backend."""
        self._store: dict[str, dict[str, object]] = {}
        self._lock = Lock()  # For sync operations
        self._async_lock = asyncio.Lock()  # For async operations

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
        for msg_dict in data.get("messages", []):
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
        for s_dict in data.get("summaries", []):
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
            id=data["id"],
            messages=messages,
            summaries=summaries,
        )

    # Sync versions
    def save(self, conversation: Conversation) -> None:
        """Save a conversation to memory (sync).

        Args:
            conversation: The conversation to save.
        """
        with self._lock:
            self._store[conversation.id] = asdict(conversation)

    def load(self, conversation_id: int) -> Conversation:
        """Load a conversation from memory (sync).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        with self._lock:
            if conversation_id not in self._store:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            data = self._store[conversation_id]
            return self._deserialize_conversation(data)

    def delete(self, conversation_id: int) -> None:
        """Delete a conversation from memory (sync).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        with self._lock:
            if conversation_id in self._store:
                del self._store[conversation_id]

    def exists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in memory (sync).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        with self._lock:
            return conversation_id in self._store

    # Async versions
    async def asave(self, conversation: Conversation) -> None:
        """Save a conversation to memory (async).

        Args:
            conversation: The conversation to save.
        """
        async with self._async_lock:
            self._store[conversation.id] = asdict(conversation)

    async def aload(self, conversation_id: int) -> Conversation:
        """Load a conversation from memory (async).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        async with self._async_lock:
            if conversation_id not in self._store:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            data = self._store[conversation_id]
            return self._deserialize_conversation(data)

    async def adelete(self, conversation_id: int) -> None:
        """Delete a conversation from memory (async).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        async with self._async_lock:
            if conversation_id in self._store:
                del self._store[conversation_id]

    async def aexists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in memory (async).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        async with self._async_lock:
            return conversation_id in self._store


__all__ = ["MemoryBackend"]
