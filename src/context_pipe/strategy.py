from abc import ABC, abstractmethod

from context_pipe.schemas import CompactionPolicy, Conversation, Message


class AbstractCompactionStrategy(ABC):
    """Abstract base class for compaction triggering strategies.

    Strategies determine when compaction should be triggered based on
    conversation state (tokens, message count, etc.).
    """

    def __init__(self, compaction_policy: CompactionPolicy) -> None:
        self.compaction_policy = compaction_policy

    @abstractmethod
    def should_compact(self, conv: Conversation) -> bool:
        """Check if compaction should be triggered for this conversation.

        Args:
            conv: The conversation to evaluate.

        Returns:
            True if compaction should be performed, False otherwise.
        """

    @abstractmethod
    def get_messages_to_summarize(self, conv: Conversation) -> list[Message]:
        """Get the list of messages to summarize and potentially wipe.

        Args:
            conv: The conversation to process.

        Returns:
            List of messages that should be summarized.
        """

class TokenBasedStrategy(AbstractCompactionStrategy):
    """Compaction strategy based on token budget usage.

    Triggers compaction when the conversation reaches a percentage of
    the token budget (e.g., 85% of 4096 tokens).

    Attributes:
        token_budget: Maximum tokens allowed in the conversation.
        trigger_at: Ratio (0-1) of token budget that triggers compaction.
        keep_n_recent: Number of recent messages to preserve.
    """

    def should_compact(self, conv: Conversation) -> bool:
        """Check if token usage exceeds the trigger threshold."""
        threshold = self.compaction_policy.token_budget * self.compaction_policy.trigger_at
        return conv.total_tokens >= threshold

    def get_messages_to_summarize(self, conv: Conversation) -> list[Message]:
        """Return all messages except the most recent keep_n_recent."""
        return conv.messages[: -self.compaction_policy.keep_n_recent]


class MessageCountBasedStrategy(AbstractCompactionStrategy):
    """Compaction strategy based on total message count.

    Triggers compaction when the conversation exceeds a maximum number
    of messages (e.g., keep last 10 messages).

    Attributes:
        max_messages: Maximum number of messages allowed before compaction.
        keep_n_recent: Number of recent messages to preserve.
    """

    def should_compact(self, conv: Conversation) -> bool:
        """Check if message count exceeds the maximum."""
        return len(conv.messages) > self.compaction_policy.keep_n_recent

    def get_messages_to_summarize(self, conv: Conversation) -> list[Message]:
        """Return all messages except the most recent keep_n_recent."""
        return conv.messages[: -self.compaction_policy.keep_n_recent]
