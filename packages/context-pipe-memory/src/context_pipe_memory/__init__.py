# packages/context-pipe-memory/src/context_pipe_memory/__init__.py

import asyncio
from dataclasses import asdict
from datetime import datetime
from threading import Lock

from context_pipe import AbstractBackend
from context_pipe.schemas import Conversation, Message, Role, Summary

CONVERSATIONS: dict[int, Conversation] = {}
MESSAGES: dict[int, Message] = {}  #
SUMMARIES: dict[int, Summary] = {}

CONVERSATION_COUNTER = 0
MESSAGE_COUNTER = 0
SUMMARY_COUNTER = 0

_lock = Lock()
_async_lock = asyncio.Lock()


class MemoryBackend(AbstractBackend):
    def __init__(self) -> None:
        pass

    def create(self) -> Conversation:
        global CONVERSATION_COUNTER
        with _lock:
            CONVERSATION_COUNTER += 1
            conversation_id = CONVERSATION_COUNTER

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        self.save(conversation)
        return conversation

    def save(self, conversation: Conversation) -> Conversation:
        with _lock:
            CONVERSATIONS[conversation.id] = conversation
        return conversation

    def load(self, conversation_id: int) -> Conversation:
        with _lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id]

    def delete(self, conversation_id: int) -> None:
        with _lock:
            if conversation_id in CONVERSATIONS:
                del CONVERSATIONS[conversation_id]

    def exists(self, conversation_id: int) -> bool:
        with _lock:
            return conversation_id in CONVERSATIONS

    def update_token_counts(self, conversation_id: int) -> None:
        """Not required here"""
        pass

    def add_message(self, message: Message, conversation_id: int) -> Message:
        global MESSAGE_COUNTER
        with _lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            MESSAGE_COUNTER += 1
            message_id = MESSAGE_COUNTER
            message.id = message_id

            MESSAGES[message_id] = message
            CONVERSATIONS[conversation_id].messages.append(message)

        return message

    def get_messages(self, conversation_id: int) -> list[Message]:
        with _lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id].messages

    def add_summary(self, conversation_id: int, summary: Summary) -> Summary:
        global SUMMARY_COUNTER
        with _lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            SUMMARY_COUNTER += 1
            summary_id = SUMMARY_COUNTER
            summary.id = summary_id

            SUMMARIES[summary_id] = summary
            CONVERSATIONS[conversation_id].summaries.append(summary)

        return summary

    def get_summaries(self, conversation_id: int) -> list[Summary]:
        with _lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id].summaries

    async def acreate(self) -> Conversation:
        global CONVERSATION_COUNTER
        async with _async_lock:
            CONVERSATION_COUNTER += 1
            conversation_id = CONVERSATION_COUNTER

        conversation = Conversation(
            id=conversation_id,
            messages=[],
            summaries=[],
        )

        await self.asave(conversation)
        return conversation

    async def asave(self, conversation: Conversation) -> Conversation:
        async with _async_lock:
            CONVERSATIONS[conversation.id] = conversation
        return conversation

    async def aload(self, conversation_id: int) -> Conversation:
        async with _async_lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id]

    async def adelete(self, conversation_id: int) -> None:
        async with _async_lock:
            if conversation_id in CONVERSATIONS:
                del CONVERSATIONS[conversation_id]

    async def aexists(self, conversation_id: int) -> bool:
        async with _async_lock:
            return conversation_id in CONVERSATIONS

    async def aupdate_token_counts(self, conversation_id: int) -> None:
        """Not required here"""
        pass

    async def aadd_message(self, message: Message, conversation_id: int) -> Message:
        global MESSAGE_COUNTER
        async with _async_lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            MESSAGE_COUNTER += 1
            message_id = MESSAGE_COUNTER
            message.id = message_id

            MESSAGES[message_id] = message
            CONVERSATIONS[conversation_id].messages.append(message)

        return message

    async def aget_messages(self, conversation_id: int) -> list[Message]:
        async with _async_lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id].messages

    async def aadd_summary(self, conversation_id: int, summary: Summary) -> Summary:
        global SUMMARY_COUNTER
        async with _async_lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            SUMMARY_COUNTER += 1
            summary_id = SUMMARY_COUNTER
            summary.id = summary_id

            SUMMARIES[summary_id] = summary
            CONVERSATIONS[conversation_id].summaries.append(summary)

        return summary

    async def aget_summaries(self, conversation_id: int) -> list[Summary]:
        async with _async_lock:
            if conversation_id not in CONVERSATIONS:
                raise KeyError(f"Conversation '{conversation_id}' not found")
            return CONVERSATIONS[conversation_id].summaries


__all__ = ["MemoryBackend"]
