"""Compactor implementations for summarizing conversation messages."""

from abc import ABC, abstractmethod

from context_pipe.schemas import Message


class AbstractCompactor(ABC):
    """Abstract base class for message compaction strategies.

    Compactors summarize a series of messages into a shorter summary
    to reduce context window usage. Implementations can use any LLM
    or heuristic algorithm to generate summaries.

    Could be configured according to llms.

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


class OpenAICompactor:
    """Compactor that uses OpenAI API to summarize messages.

    Uses GPT models to generate natural language summaries of message spans.

    Attributes:
        client: OpenAI client instance.
        model: The model to use for summarization (default "gpt-4o-mini").
        system_prompt: System prompt for the summarization task.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
    ) -> None:
        """Initialize the OpenAI compactor.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: Model to use for summarization (default "gpt-4o-mini").
            system_prompt: Custom system prompt for summarization task.
        """
        try:
            from openai import AsyncOpenAI, OpenAI
        except ImportError:
            raise ImportError("openai package is required for OpenAICompactor. Install it with: pip install openai")

        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

        self.system_prompt = system_prompt

    def _format_messages(self, messages: list[Message]) -> str:
        """Format messages into a readable string for summarization.

        Args:
            messages: List of messages to format.

        Returns:
            Formatted string representation of messages.
        """
        formatted = []
        for msg in messages:
            role = msg.role.value.upper()
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def summarize(self, messages: list[Message]) -> str:
        """Summarize a list of messages using OpenAI API (sync).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.

        Raises:
            ValueError: If messages list is empty.
        """
        if not messages:
            raise ValueError("Cannot summarize empty message list")

        formatted_messages = self._format_messages(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Please summarize the following conversation:\n\n{formatted_messages}"},
            ],
            temperature=0.3,
        )

        return (response.choices[0].message.content or "" ).strip() or "Unable to generate summary"

    async def asummarize(self, messages: list[Message]) -> str:
        """Summarize a list of messages using OpenAI API (async).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.

        Raises:
            ValueError: If messages list is empty.
        """
        if not messages:
            raise ValueError("Cannot summarize empty message list")

        formatted_messages = self._format_messages(messages)

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Please summarize the following conversation:\n\n{formatted_messages}"},
            ],
            temperature=0.3,
        )

        return (response.choices[0].message.content or "" ).strip() or "Unable to generate summary"


class SimpleCompactor:
    """Basic compactor that creates simple summaries without LLM.

    Useful for testing or when you want lightweight summarization.
    Extracts key information from messages based on simple heuristics.
    """

    def summarize(self, messages: list[Message]) -> str:
        """Summarize messages using simple heuristics (sync).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.
        """
        if not messages:
            return "No messages to summarize"

        # Extract unique speakers and message count
        roles = set(msg.role.value for msg in messages)

        # Get first and last message snippets
        first_content = messages[0].content[:100]
        last_content = messages[-1].content[:100]

        return (
            f"Summary: {len(messages)} messages between {', '.join(roles)}. "
            f"Started with: '{first_content}...' "
            f"Ended with: '{last_content}...'"
        )

    async def asummarize(self, messages: list[Message]) -> str:
        """Summarize messages using simple heuristics (async).

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary string of the messages.
        """
        return self.summarize(messages)


__all__ = ["OpenAICompactor", "SimpleCompactor"]
