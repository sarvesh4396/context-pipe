# src/context_pipe/schemas.py

"""Data schemas for context-pipe conversations.

This module defines the core data structures for managing conversation
context, including messages, summaries, and full conversations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Role(Enum):
    """Enum for message roles in a conversation."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


class WipeMode(Enum):
    """Enum for how to handle messages when wiping old messages."""

    WIPE = "wipe"
    KEEP = "keep"


@dataclass
class Message:
    """Represents a single message in a conversation.

    Attributes:
        role: The role of the message sender (user, assistant, or system).
        content: The text content of the message.
        token_count: The number of tokens in the message (default 0).
        metadata: Additional metadata associated with the message (default empty dict).
        created_at: Timestamp when the message was created (default current time).
    """

    role: Role
    content: str
    token_count: int = 0
    id: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Summary:
    """Represents a summary of a message span in a conversation.

    Attributes:
        text: The text content of the summary.
        span_start: The index of the first message in the summarized span.
        span_end: The index of the last message in the summarized span.
        compacted_at: Timestamp when the summary was created (default current time).
    """

    text: str
    span_start: int
    span_end: int
    id: int | None = None
    compacted_at: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """Represents a conversation with messages and summaries.

    Attributes:
        id: Unique identifier for the conversation.
        messages: List of messages in the conversation (default empty list).
        summaries: List of summaries of compacted message spans (default empty list).
    """

    id: int
    messages: list[Message] = field(default_factory=list)
    summaries: list[Summary] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        """Calculate the total number of tokens in the conversation.

        Returns:
            The sum of token counts across all messages.
        """
        return sum(msg.token_count for msg in self.messages)


@dataclass
class CompactionPolicy:
    """Defines the policy for compacting messages in a conversation.

    Attributes:
        strategy: The strategy to determine when to compact messages.
        wipe_mode: How to handle messages that are compacted (default WIPE).
    """

    token_budget: int = 4096
    trigger_at: float = 0.85
    keep_n_recent: int = 10
    wipe_mode: WipeMode = WipeMode.KEEP
