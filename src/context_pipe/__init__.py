# src/context_pipe/__init__.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

from context_pipe.schemas import Conversation, Message, Role, Summary, WipeMode


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

    def __init__(self, conversation_id: int | None = None) -> None:
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
    def load(self, conversation_id: int) -> Conversation:
        """Load a conversation with all its messages and summaries (sync).

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    async def aload(self, conversation_id: int) -> Conversation:
        """Load a conversation with all its messages and summaries (async).

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    def delete(self, conversation_id: int) -> None:
        """Delete a conversation and all its messages and summaries (sync)."""

    @abstractmethod
    async def adelete(self, conversation_id: int) -> None:
        """Delete a conversation and all its messages and summaries (async)."""

    @abstractmethod
    def exists(self, conversation_id: int) -> bool:
        """Return True if the conversation exists (sync)."""

    @abstractmethod
    async def aexists(self, conversation_id: int) -> bool:
        """Return True if the conversation exists (async)."""

    @abstractmethod
    def update_token_counts(self, conversation_id: int) -> None:
        """Recalculate and update token counts for all messages in a conversation (sync)."""

    @abstractmethod
    async def aupdate_token_counts(self, conversation_id: int) -> None:
        """Recalculate and update token counts for all messages in a conversation (async)."""

    # --- Message operations ---

    @abstractmethod
    def add_message(self, message: Message, conversation_id: int) -> Message:
        """Add a message to a conversation, assigns message.id (sync).

        Returns:
            The message with its assigned id.
        """

    @abstractmethod
    async def aadd_message(self, message: Message, conversation_id: int) -> Message:
        """Add a message to a conversation, assigns message.id (async).

        Returns:
            The message with its assigned id.
        """

    @abstractmethod
    def get_messages(self, conversation_id: int) -> list[Message]:
        """Return all messages for a conversation ordered by insertion (sync)."""

    @abstractmethod
    async def aget_messages(self, conversation_id: int) -> list[Message]:
        """Return all messages for a conversation ordered by insertion (async)."""

    # --- Summary operations ---

    @abstractmethod
    def add_summary(self, conversation_id: int, summary: Summary) -> Summary:
        """Add a summary to a conversation, assigns summary.id (sync).

        Returns:
            The summary with its assigned id.
        """

    @abstractmethod
    async def aadd_summary(self, conversation_id: int, summary: Summary) -> Summary:
        """Add a summary to a conversation, assigns summary.id (async).

        Returns:
            The summary with its assigned id.
        """

    @abstractmethod
    def get_summaries(self, conversation_id: int) -> list[Summary]:
        """Return all summaries for a conversation ordered by insertion (sync)."""

    @abstractmethod
    async def aget_summaries(self, conversation_id: int) -> list[Summary]:
        """Return all summaries for a conversation ordered by insertion (async)."""


class AbstractCompactor(ABC):
    """Abstract base class for message compaction strategies.

    Compactors summarize a series of messages into a shorter summary
    to reduce context window usage. Implementations can use any LLM
    or heuristic algorithm to generate summaries.

    All compactors must implement both sync and async versions:
    - summarize/asummarize
    """

    @abstractmethod
    def summarize(self, messages: list[Message]) -> str:
        """Summarize a list of messages (sync).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.
        """

    @abstractmethod
    async def asummarize(self, messages: list[Message]) -> str:
        """Summarize a list of messages (async).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.
        """


@dataclass
class WindowPolicy:
    """Policy for managing conversation context within a token budget.

    Attributes:
        token_budget: The maximum number of tokens allowed in the conversation (default 4096).
        trigger_at: The ratio of token usage that triggers compaction (default 0.85 = 85%).
        keep_n_recent: The number of recent messages to keep when wiping old messages (default 6).
        wipe_mode: How to handle old messages when compacting (default WipeMode.WIPE).
    """

    token_budget: int = 4096
    trigger_at: float = 0.85
    keep_n_recent: int = 6
    wipe_mode: WipeMode = WipeMode.WIPE


class CompactionEngine:
    """Engine for compacting conversations when approaching token limits.

    Takes a WindowPolicy and an AbstractCompactor to manage conversation
    history within token budgets.
    """

    def __init__(self, policy: WindowPolicy, compactor: AbstractCompactor) -> None:
        """Initialize the compaction engine.

        Args:
            policy: The window policy for token budget management.
            compactor: The compactor instance for summarizing messages.
        """
        self.policy = policy
        self.compactor = compactor

    async def maybe_compact(self, conv: Conversation) -> Conversation:
        """Check if compaction is needed and compact if threshold is met.

        Checks if the conversation has reached the trigger threshold (e.g., 85%
        of the token budget). If so, summarizes old messages and applies the
        wipe mode to remove them if configured.

        Args:
            conv: The conversation to potentially compact.

        Returns:
            The conversation after compaction (if applicable).
        """
        total_tokens = conv.total_tokens
        threshold = self.policy.token_budget * self.policy.trigger_at

        if total_tokens < threshold:
            return conv

        # Summarize old messages
        messages_to_summarize = conv.messages[: -self.policy.keep_n_recent]
        if messages_to_summarize:
            summary_text = await self.compactor.asummarize(messages_to_summarize)
            summary = Summary(
                text=summary_text,
                span_start=0,
                span_end=len(messages_to_summarize) - 1,
            )
            conv.summaries.append(summary)

            # Apply wipe mode
            if self.policy.wipe_mode == WipeMode.WIPE:
                conv.messages = conv.messages[-self.policy.keep_n_recent :]

        return conv


__all__ = [
    "Role",
    "WipeMode",
    "Message",
    "Summary",
    "Conversation",
    "AbstractBackend",
    "AbstractCompactor",
    "WindowPolicy",
    "CompactionEngine",
]
