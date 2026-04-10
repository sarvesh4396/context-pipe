# src/context_pipe/__init__.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

from context_pipe.compactors import AbstractCompactor
from context_pipe.schemas import CompactionPolicy, Conversation, Message, Role, Summary, WipeMode
from context_pipe.strategy import AbstractCompactionStrategy


class AbstractBackend(ABC):
    """Abstract base class for conversation persistence backends.

    Backends store conversations, messages, and summaries as separate entities
    with relationships managed by the backend (not embedded in the schema).

    All backends must implement both sync and async versions of:
    - create/acreate: create a new conversation, returns Conversation with assigned id
    - save/asave: persist a conversation and all its messages/summaries
    - load/aload: load a conversation with all its messages and summaries
    - delete/adelete: delete a conversation and all related messages/summaries
    - exists/aexists: check if a conversation exists
    - add_message/aadd_message: add a single message to a conversation
    - add_summary/aadd_summary: add a single summary to a conversation
    - get_messages/aget_messages: fetch messages for a conversation
    - get_summaries/aget_summaries: fetch summaries for a conversation
    """

    def __init__(self, conversation_id: int | None = None, compact_engine) -> None:
        """Initialize the backend."""
        self.conversation_id = conversation_id

    # --- Conversation lifecycle ---

    @abstractmethod
    def create(self) -> Conversation:
        """Create and persist a new empty conversation (sync)."""

    @abstractmethod
    async def acreate(self) -> Conversation:
        """Create and persist a new empty conversation (async)."""

    @abstractmethod
    def save(self, conversation: Conversation) -> Conversation:
        """Persist a conversation and sync all its messages/summaries (sync)."""

    @abstractmethod
    async def asave(self, conversation: Conversation) -> Conversation:
        """Persist a conversation and sync all its messages/summaries (async)."""

    @abstractmethod
    def load(self, conversation_id: int | None = None) -> Conversation:
        """Load a conversation with all its messages and summaries (sync).

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    async def aload(self, conversation_id: int | None = None) -> Conversation:
        """Load a conversation with all its messages and summaries (async).

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    def delete(self, conversation_id: int | None = None) -> None:
        """Delete a conversation and all its messages and summaries (sync)."""

    @abstractmethod
    async def adelete(self, conversation_id: int | None = None) -> None:
        """Delete a conversation and all its messages and summaries (async)."""

    @abstractmethod
    def exists(self, conversation_id: int | None = None) -> bool:
        """Return True if the conversation exists (sync)."""

    @abstractmethod
    async def aexists(self, conversation_id: int | None = None) -> bool:
        """Return True if the conversation exists (async)."""

    @abstractmethod
    def update_token_counts(self, conversation_id: int | None = None) -> None:
        """Recalculate and update token counts for all messages in a conversation (sync)."""

    @abstractmethod
    async def aupdate_token_counts(self, conversation_id: int | None = None) -> None:
        """Recalculate and update token counts for all messages in a conversation (async)."""

    # --- Message operations ---

    @abstractmethod
    def add_message(self, message: Message, conversation_id: int | None = None) -> Message:
        """Add a message to a conversation, assigns message.id (sync).

        Returns:
            The message with its assigned id.
        """

    @abstractmethod
    async def aadd_message(self, message: Message, conversation_id: int | None = None) -> Message:
        """Add a message to a conversation, assigns message.id (async).

        Returns:
            The message with its assigned id.
        """

    @abstractmethod
    def get_messages(self, conversation_id: int | None = None) -> list[Message]:
        """Return all messages for a conversation ordered by insertion (sync)."""

    @abstractmethod
    async def aget_messages(self, conversation_id: int | None = None) -> list[Message]:
        """Return all messages for a conversation ordered by insertion (async)."""

    # --- Summary operations ---

    @abstractmethod
    def add_summary(self, summary: Summary, conversation_id: int | None = None) -> Summary:
        """Add a summary to a conversation, assigns summary.id (sync).

        Returns:
            The summary with its assigned id.
        """

    @abstractmethod
    async def aadd_summary(self, summary: Summary, conversation_id: int | None = None) -> Summary:
        """Add a summary to a conversation, assigns summary.id (async).

        Returns:
            The summary with its assigned id.
        """

    @abstractmethod
    def get_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        """Return all summaries for a conversation ordered by insertion (sync)."""

    @abstractmethod
    async def aget_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        """Return all summaries for a conversation ordered by insertion (async)."""





class CompactionEngine:
    """Engine for compacting conversations using a configurable strategy.

    Takes a CompactionStrategy and an AbstractCompactor to manage conversation
    history according to the selected strategy (token-based, message-count, etc).
    """

    def __init__(
        self,
        strategy: AbstractCompactionStrategy,
        compactor: AbstractCompactor,
        policy: CompactionPolicy,
    ) -> None:
        """Initialize the compaction engine.

        Args:
            strategy: The compaction strategy that determines when to compact.
            compactor: The compactor instance for summarizing messages.
            policy: The window policy for wipe behavior (uses defaults if not provided).
        """
        self.strategy = strategy
        self.compactor = compactor
        self.policy = policy

    async def maybe_compact(self, conv: Conversation) -> Conversation:
        """Check if compaction is needed and compact if threshold is met.

        Uses the configured strategy to determine if compaction is needed.
        If triggered, summarizes old messages and applies the wipe mode.

        Args:
            conv: The conversation to potentially compact.

        Returns:
            The conversation after compaction (if applicable).
        """
        if not self.strategy.should_compact(conv):
            return conv

        # Get messages to summarize according to strategy
        messages_to_summarize = self.strategy.get_messages_to_summarize(conv)
        if not messages_to_summarize:
            return conv

        # Summarize old messages
        summary_text = await self.compactor.asummarize(messages_to_summarize)
        summary = Summary(
            text=summary_text,
            span_start=0,
            span_end=len(messages_to_summarize) - 1,
        )
        conv.summaries.append(summary)

        # Apply wipe mode
        if self.policy.wipe_mode == WipeMode.WIPE:
            keep_n = self.policy.keep_n_recent
            conv.messages = conv.messages[-keep_n:]

        return conv


__all__ = [
    "Role",
    "WipeMode",
    "Message",
    "Summary",
    "Conversation",
    "AbstractBackend",
    "AbstractCompactor",
    "AbstractCompactionStrategy",
    "CompactionEngine",
]
