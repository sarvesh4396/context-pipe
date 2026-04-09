# src/context_pipe/__init__.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

from context_pipe.schemas import Conversation, Message, Role, Summary, WipeMode


class AbstractBackend(ABC):
    """Abstract base class for conversation persistence backends.

    Backends are responsible for storing and retrieving conversations
    to pluggable storage systems (memory, Redis, SQL databases, etc.).

    All backends must implement both sync and async versions of methods:
    - save/asave, load/aload, delete/adelete, exists/aexists
    - create/acreate for creating new conversations with auto-generated IDs
    """

    def create(self) -> None:
        """Create a new conversation with an auto-generated ID (sync).

        Returns:
            A new Conversation instance with auto-generated ID.
        """

    async def acreate(self) -> None:
        """Create a new conversation with an auto-generated ID (async).

        Returns:
            A new Conversation instance with auto-generated ID.
        """

    # Sync versions
    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        """Save a conversation to the backend (sync).

        Args:
            conversation: The conversation to save.
        """

    @abstractmethod
    def load(self, conversation_id: int) -> Conversation:
        """Load a conversation from the backend (sync).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    def delete(self, conversation_id: int) -> None:
        """Delete a conversation from the backend (sync).

        Args:
            conversation_id: The ID of the conversation to delete.
        """

    @abstractmethod
    def exists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in the backend (sync).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """

    # Async versions
    @abstractmethod
    async def asave(self, conversation: Conversation) -> None:
        """Save a conversation to the backend (async).

        Args:
            conversation: The conversation to save.
        """

    @abstractmethod
    async def aload(self, conversation_id: int) -> Conversation:
        """Load a conversation from the backend (async).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """

    @abstractmethod
    async def adelete(self, conversation_id: int) -> None:
        """Delete a conversation from the backend (async).

        Args:
            conversation_id: The ID of the conversation to delete.
        """

    @abstractmethod
    async def aexists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in the backend (async).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """


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
        total_tokens = conv.total_tokens()
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
