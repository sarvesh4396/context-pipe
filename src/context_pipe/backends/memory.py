import asyncio
from threading import Lock

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation, Message, Summary

_conversations: dict[int, Conversation] = {}
_messages: dict[int, Message] = {}
_summaries: dict[int, Summary] = {}

_conversation_counter = 0
_message_counter = 0
_summary_counter = 0

_lock = Lock()
_async_lock = asyncio.Lock()


class MemoryBackend(AbstractBackend):
    def __init__(self, conversation_id: int | None = None) -> None:
        super().__init__(conversation_id)

    def create(self) -> Conversation:
        global _conversation_counter
        with _lock:
            _conversation_counter += 1
            conversation_id = _conversation_counter

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        self.save(conversation)
        return conversation

    def save(self, conversation: Conversation) -> Conversation:
        with _lock:
            _conversations[conversation.id] = conversation
        return conversation

    def load(self, conversation_id: int | None = None) -> Conversation:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id]

    def delete(self, conversation_id: int | None = None) -> None:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id in _conversations:
                del _conversations[conversation_id]

    def exists(self, conversation_id: int | None = None) -> bool:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            return conversation_id in _conversations

    def update_token_counts(self, conversation_id: int | None = None) -> None:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            conv = _conversations[conversation_id]
            for msg in conv.messages:
                if msg.token_count is None:
                    msg.token_count = 0

    def add_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        global _message_counter
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            _message_counter += 1
            message_id = _message_counter
            message.id = message_id

            _messages[message_id] = message
            _conversations[conversation_id].messages.append(message)

        return message

    def get_messages(self, conversation_id: int | None = None) -> list[Message]:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id].messages

    def add_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        global _summary_counter
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            _summary_counter += 1
            summary_id = _summary_counter
            summary.id = summary_id

            _summaries[summary_id] = summary
            _conversations[conversation_id].summaries.append(summary)

        return summary

    def get_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        with _lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id].summaries

    async def acreate(self) -> Conversation:
        global _conversation_counter
        async with _async_lock:
            _conversation_counter += 1
            conversation_id = _conversation_counter

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        await self.asave(conversation)
        return conversation

    async def asave(self, conversation: Conversation) -> Conversation:
        async with _async_lock:
            _conversations[conversation.id] = conversation
        return conversation

    async def aload(self, conversation_id: int | None = None) -> Conversation:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id]

    async def adelete(self, conversation_id: int | None = None) -> None:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id in _conversations:
                del _conversations[conversation_id]

    async def aexists(self, conversation_id: int | None = None) -> bool:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            return conversation_id in _conversations

    async def aupdate_token_counts(self, conversation_id: int | None = None) -> None:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            conv = _conversations[conversation_id]
            for msg in conv.messages:
                if msg.token_count is None:
                    msg.token_count = 0

    async def aadd_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        global _message_counter
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            _message_counter += 1
            message_id = _message_counter
            message.id = message_id

            _messages[message_id] = message
            _conversations[conversation_id].messages.append(message)

        return message

    async def aget_messages(self, conversation_id: int | None = None) -> list[Message]:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id].messages

    async def aadd_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        global _summary_counter
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            _summary_counter += 1
            summary_id = _summary_counter
            summary.id = summary_id

            _summaries[summary_id] = summary
            _conversations[conversation_id].summaries.append(summary)

        return summary

    async def aget_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        conversation_id = conversation_id or self.conversation_id
        if conversation_id is None:
            raise ValueError("conversation_id must be provided or set in __init__")
        async with _async_lock:
            if conversation_id not in _conversations:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return _conversations[conversation_id].summaries


__all__ = ["MemoryBackend"]
