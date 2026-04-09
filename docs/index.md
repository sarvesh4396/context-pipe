# context-pipe Documentation

Welcome to **context-pipe**, an extensible conversation context management toolkit for LLM applications.

## What is context-pipe?

context-pipe solves a critical problem in LLM applications: **managing conversation history within token budgets**.

As conversations grow, context windows fill up. context-pipe:

- **Stores messages** in a structured way with metadata and token counts
- **Triggers automatic summarization** when approaching token limits
- **Persists conversations** to pluggable backends (in-memory, Redis, SQL databases)
- **Remains provider-agnostic** — you inject whatever LLM call you want for summarization

## Key Features

- **Flexible Storage** — Choose from multiple backend implementations or write your own
- **Token Budget Management** — Define a token budget and let context-pipe handle the rest
- **Provider-Agnostic Compaction** — Bring your own LLM or summarization logic
- **Fully Async** — Built for modern async/await patterns
- **Type-Safe** — Full type hints with mypy strict mode support
- **Extensible** — Simple interfaces for custom backends and compactors

## Quick Start with Installation

```bash
# Base package only
pip install context-pipe

# With optional backends
pip install context-pipe[redis]
pip install context-pipe[sqlalchemy]
pip install context-pipe[all]
```

## 15-Line Usage Example

```python
import asyncio
from context_pipe import (
    Conversation, Message, Role, WindowPolicy, 
    CompactionEngine, AbstractCompactor
)
from context_pipe.memory import MemoryBackend

class MyCompactor(AbstractCompactor):
    async def summarize(self, messages):
        return f"Summary of {len(messages)} messages"

async def main():
    conv = Conversation(id="chat-1")
    conv.append(Message(Role.USER, "Hello", token_count=5))
    conv.append(Message(Role.ASSISTANT, "Hi!", token_count=3))
    
    engine = CompactionEngine(WindowPolicy(), MyCompactor())
    backend = MemoryBackend()
    
    await backend.save(conv)
    loaded = await backend.load("chat-1")
    compacted = await engine.maybe_compact(loaded)
    print(f"Tokens: {compacted.total_tokens()}")

asyncio.run(main())
```

## Architecture Overview

```
┌─────────────────────────────────────┐
│     Your LLM Application            │
└────────────┬────────────────────────┘
             │
        ┌────▼──────────────────────────┐
        │   CompactionEngine            │
        │  - Monitors token usage       │
        │  - Triggers compaction        │
        └────┬──────────────┬───────────┘
             │              │
        ┌────▼───┐      ┌───▼─────────┐
        │ Policy │      │  Compactor  │
        │        │      │ (Your LLM)  │
        └────────┘      └─────────────┘
             │
        ┌────▼──────────────────────────┐
        │   AbstractBackend             │
        │ (Memory, Redis, SQL, ...)     │
        └───────────────────────────────┘
```

The CompactionEngine sits between your application and a Backend, using a Compactor to summarize old messages when needed.

## Core Concepts

### Message
Represents a single message in a conversation with role, content, token count, and metadata.

```python
from context_pipe import Message, Role

msg = Message(
    role=Role.USER,
    content="What is AI?",
    token_count=10,
    metadata={"source": "chat"}
)
```

### Conversation
A container for messages and summaries.

```python
from context_pipe import Conversation

conv = Conversation(id="session-1")
conv.append(msg)
print(conv.total_tokens())
```

### WindowPolicy
Defines token budget and compaction thresholds.

```python
from context_pipe import WindowPolicy, WipeMode

policy = WindowPolicy(
    token_budget=4096,      # Limit
    trigger_at=0.85,        # 85% triggers compaction
    keep_n_recent=6,        # Keep last 6 messages
    wipe_mode=WipeMode.WIPE # Remove old messages
)
```

### Backends
Choose where to persist conversations.

```python
from context_pipe.memory import MemoryBackend
from context_pipe.redis import RedisBackend
from context_pipe.sqlalchemy import SQLAlchemyBackend
```

### Compactors
Implement your own summarization logic.

```python
from context_pipe import AbstractCompactor

class OpenAICompactor(AbstractCompactor):
    async def summarize(self, messages):
        # Call OpenAI API
        pass
```

## Next Steps

- [Getting Started Guide](getting-started.md) — Step-by-step setup and examples
- [API Reference](api/core.md) — Full API documentation
- [Backends](api/memory.md) — Storage options and examples

## Contributing

Contributions welcome! Open an issue or submit a PR on [GitHub](https://github.com/sarvesh4396/context-pipe).

## License

MIT License. See LICENSE file for details.
