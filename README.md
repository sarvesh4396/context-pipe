# context-pipe

[![PyPI - Version](https://img.shields.io/pypi/v/context-pipe.svg)](https://pypi.org/project/context-pipe/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/context-pipe.svg)](https://pypi.org/project/context-pipe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI/CD](https://github.com/sarvesh4396/context-pipe/actions/workflows/ci.yml/badge.svg)](https://github.com/sarvesh4396/context-pipe/actions)

**Extensible conversation context management toolkit for LLM applications.**

context-pipe manages conversation history within token budgets — storing messages, triggering summarization when the context window fills up, and persisting conversations to pluggable backends. Compaction logic is provider-agnostic: you inject whatever LLM call you want.

## Installation

Install the base package:

```bash
uv add context-pipe
```

Or with optional backend support:

```bash
# With in-memory backend
uv add context-pipe[memory]

# With Redis backend
uv add context-pipe[redis]

# With SQLAlchemy backend
uv add context-pipe[sqlalchemy]

# With all backends
uv add context-pipe[all]
```

## Quick Start

```python
import asyncio
from context_pipe import (
    Conversation,
    Message,
    Role,
    WindowPolicy,
    CompactionEngine,
    AbstractCompactor,
)
from context_pipe_memory import MemoryBackend


class SimpleCompactor(AbstractCompactor):
    """A simple compactor that summarizes messages."""

    def summarize(self, messages: list[Message]) -> str:
        """Summarize messages by taking the first and last (sync)."""
        if not messages:
            return ""
        return f"Summary of {len(messages)} messages: {messages[0].content} ... {messages[-1].content}"

    async def asummarize(self, messages: list[Message]) -> str:
        """Summarize messages by taking the first and last (async)."""
        if not messages:
            return ""
        return f"Summary of {len(messages)} messages: {messages[0].content} ... {messages[-1].content}"


# Async example
async def async_example():
    # Create a conversation
    conv = Conversation(id="conv-1")

    # Add messages
    conv.append(
        Message(
            role=Role.USER,
            content="What is the capital of France?",
            token_count=10,
        )
    )
    conv.append(
        Message(
            role=Role.ASSISTANT,
            content="The capital of France is Paris.",
            token_count=12,
        )
    )

    # Set up compaction with a token budget
    policy = WindowPolicy(token_budget=100, trigger_at=0.8, keep_n_recent=2)
    compactor = SimpleCompactor()
    engine = CompactionEngine(policy=policy, compactor=compactor)

    # Use the backend to persist (async)
    backend = MemoryBackend()
    await backend.asave(conv)

    # Load and compact
    loaded = await backend.aload("conv-1")
    compacted = await engine.maybe_compact(loaded)
    await backend.asave(compacted)

    print(f"Total tokens: {compacted.total_tokens()}")
    print(f"Active messages: {len(compacted.active_messages())}")
    print(f"Summaries: {len(compacted.summaries)}")


# Sync example
def sync_example():
    # Create a conversation
    conv = Conversation(id="conv-2")

    # Add messages
    conv.append(
        Message(
            role=Role.USER,
            content="What is the capital of Germany?",
            token_count=10,
        )
    )
    conv.append(
        Message(
            role=Role.ASSISTANT,
            content="The capital of Germany is Berlin.",
            token_count=12,
        )
    )

    # Use the backend to persist (sync)
    backend = MemoryBackend()
    backend.save(conv)

    # Load (sync)
    loaded = backend.load("conv-2")
    print(f"Loaded conversation with {len(loaded.messages)} messages")


if __name__ == "__main__":
    # Run async example
    asyncio.run(async_example())
    
    # Run sync example
    sync_example()
```

### Sync and Async APIs

context-pipe provides **both synchronous and asynchronous** versions of all backend methods and compactors, following Django's async conventions:

- **Async methods** use an `a` prefix: `asave()`, `aload()`, `adelete()`, `aexists()`, `asummarize()`
- **Sync methods** use regular names: `save()`, `load()`, `delete()`, `exists()`, `summarize()`

This allows you to use the same library in both async-first and sync-first applications:

```python
# Async usage
backend = MemoryBackend()
await backend.asave(conversation)
loaded = await backend.aload(conv_id)

# Sync usage (same backend instance)
backend = MemoryBackend()
backend.save(conversation)
loaded = backend.load(conv_id)
```

## Documentation

For detailed documentation, visit [the full docs](https://sarvesh4396.github.io/context-pipe/) or see [Getting Started](https://sarvesh4396.github.io/context-pipe/getting-started/).

## Features

- **Flexible Storage** — In-memory, Redis, SQLAlchemy, or custom backends
- **Sync/Async Dual API** — Use the same library in sync-first or async-first applications
- **Token Budget Management** — Automatic compaction when approaching context limits
- **Provider-Agnostic Compaction** — Bring your own LLM or summarization logic
- **Type-Safe** — Full type hints and mypy strict mode support
- **Extensible** — Simple interfaces for custom backends and compactors

## Contributing

We welcome contributions, suggestions, and ideas! context-pipe is designed to be extensible, and we're particularly interested in:

- **New Backend Implementations** — Add support for additional storage systems
- **Compaction Algorithms** — Propose or implement novel message summarization strategies
- **Token Counting Strategies** — Different tokenization approaches for various LLM providers
- **Performance Optimizations** — Improve compaction efficiency and backend speed
- **Documentation & Examples** — Help us document use cases and best practices
- **Bug Reports & Feature Requests** — Let us know how we can improve

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-algorithm`)
3. Make your changes and ensure tests pass (`uv run pytest`)
4. Submit a pull request with a clear description

### Algorithm Contributions

If you're implementing a new compaction algorithm or backend strategy:

- Add comprehensive docstrings explaining the approach
- Include unit tests demonstrating the behavior
- Update documentation with performance characteristics
- Consider async/await patterns for consistency

See the [Getting Started guide](https://github.com/heysarvesh/context-pipe/blob/main/docs/getting-started.md) for development setup.

## License

MIT
