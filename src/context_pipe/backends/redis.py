import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Literal

import redis
import redis.asyncio as redis_async

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation, Message, Role, Summary


def _json_serializer(obj: object) -> str:
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class RedisBackend(AbstractBackend):
    """Redis backend for storing conversations."""

    GLOBAL_CONVERSATION_COUNTER_KEY = "conversation:id"
    GLOBAL_MESSAGE_COUNTER_KEY = "message:id"
    GLOBAL_SUMMARY_COUNTER_KEY = "summary:id"

    def __init__(
        self,
        client: redis.Redis | redis_async.Redis,
        prefix: str = "context-pipe:",
        ttl_seconds: int | None = None,
        conversation_id: int | None = None,
    ) -> None:
        super().__init__(conversation_id)
        self.client = client
        self.is_async = isinstance(client, redis_async.Redis)
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def _key(self, of: Literal["conversation", "message", "summary"]) -> str:
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
        return f"{self.prefix}{of}:{object_id}"

    @staticmethod
    def _deserialize_conversation(data: dict[str, object]) -> Conversation:
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

    def create(self) -> Conversation:
        if self.is_async:
            return asyncio.run(self.acreate())

        conversation_id = int(self.client.incr(self._key("conversation")))  # type: ignore[union-attr]

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        self.save(conversation)
        return conversation

    def save(self, conversation: Conversation) -> Conversation:
        if self.is_async:
            return asyncio.run(self.asave(conversation))
        else:
            key = self._build_object_key("conversation", conversation.id)
            data = json.dumps(
                asdict(conversation),
                default=_json_serializer,
            )

            if self.ttl_seconds:
                self.client.setex(key, self.ttl_seconds, data)  # type: ignore[union-attr]
            else:
                self.client.set(key, data)  # type: ignore[union-attr]
            return conversation

    def load(self, conversation_id: int | None = None) -> Conversation:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        if self.is_async:
            return asyncio.run(self.aload(cid))
        else:
            key = self._build_object_key("conversation", cid)
            data = self.client.get(key)  # type: ignore[union-attr]

            if data is None:
                raise KeyError(f"Conversation '{cid}' not found")

            parsed = json.loads(data)
            return self._deserialize_conversation(parsed)

    def delete(self, conversation_id: int | None = None) -> None:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        if self.is_async:
            asyncio.run(self.adelete(cid))
        else:
            key = self._build_object_key("conversation", cid)
            self.client.delete(key)  # type: ignore[union-attr]

    def exists(self, conversation_id: int | None = None) -> bool:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        if self.is_async:
            return asyncio.run(self.aexists(cid))
        else:
            key = self._build_object_key("conversation", cid)
            return bool(self.client.exists(key))  # type: ignore[union-attr]

    def update_token_counts(self, conversation_id: int | None = None) -> None:
        pass

    def add_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        pass

    def get_messages(self, conversation_id: int | None = None) -> list[Message]:
        pass

    def add_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        pass

    def get_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        pass

    async def acreate(self) -> Conversation:
        conversation_id = int(await self.client.incr(self._key("conversation")))  # type: ignore[union-attr]

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        await self.asave(conversation)
        return conversation

    async def asave(self, conversation: Conversation) -> Conversation:
        key = self._build_object_key("conversation", conversation.id)
        data = json.dumps(
            asdict(conversation),
            default=_json_serializer,
        )

        if self.ttl_seconds:
            await self.client.setex(key, self.ttl_seconds, data)  # type: ignore[union-attr]
        else:
            await self.client.set(key, data)  # type: ignore[union-attr]
        return conversation

    async def aload(self, conversation_id: int | None = None) -> Conversation:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        key = self._build_object_key("conversation", cid)
        data = await self.client.get(key)  # type: ignore[union-attr]

        if data is None:
            raise KeyError(f"Conversation '{cid}' not found")

        parsed = json.loads(data)
        return self._deserialize_conversation(parsed)

    async def adelete(self, conversation_id: int | None = None) -> None:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        key = self._build_object_key("conversation", cid)
        await self.client.delete(key)  # type: ignore[union-attr]

    async def aexists(self, conversation_id: int | None = None) -> bool:
        cid = conversation_id if conversation_id is not None else self.conversation_id
        if cid is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        key = self._build_object_key("conversation", cid)
        return bool(await self.client.exists(key))  # type: ignore[union-attr]

    async def aupdate_token_counts(self, conversation_id: int | None = None) -> None:
        pass

    async def aadd_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        pass

    async def aget_messages(self, conversation_id: int | None = None) -> list[Message]:
        pass

    async def aadd_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        pass

    async def aget_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        pass


__all__ = ["RedisBackend"]
