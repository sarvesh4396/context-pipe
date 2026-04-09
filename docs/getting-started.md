# Getting Started

Let's build a chatbot that manages conversation history within a token budget.

## Step 1: Installation

```bash
# Install context-pipe with the memory backend
pip install context-pipe[memory]
```

## Step 2: Define Your Compactor

A compactor is responsible for summarizing messages when the token budget is reached. Here's a simple example:

```python
# compactor.py
from context_pipe import AbstractCompactor, Message

class SimpleCompactor(AbstractCompactor):
    """A simple compactor that joins all messages."""

    async def summarize(self, messages: list[Message]) -> str:
        """Summarize messages by listing them."""
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            lines.append(f"{msg.role.value}: {msg.content}")
        
        return f"Previous exchange:\n" + "\n".join(lines)
```

For production, you'd replace this with calls to Claude, GPT-4, or another LLM:

```python
class OpenAICompactor(AbstractCompactor):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def summarize(self, messages: list[Message]) -> str:
        import openai
        
        msgs = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize this conversation concisely."},
                *msgs,
            ],
        )
        
        return response.choices[0].message.content
```

## Step 3: Pick a Backend

Choose where to store conversations:

### Memory (In-Process)

Perfect for development and testing:

```python
from context_pipe.memory import MemoryBackend

backend = MemoryBackend()
```

### Redis

For distributed systems:

```python
import redis.asyncio as redis
from context_pipe.redis import RedisBackend

client = redis.from_url("redis://localhost")
backend = RedisBackend(client=client, prefix="chat:")
```

### SQLAlchemy

For traditional databases:

```python
from sqlalchemy.ext.asyncio import create_async_engine
from context_pipe.sqlalchemy import SQLAlchemyBackend

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
backend = SQLAlchemyBackend(engine=engine)
```

## Step 4: Wire It Up

```python
import asyncio
from context_pipe import (
    Conversation,
    Message,
    Role,
    WindowPolicy,
    CompactionEngine,
)
from context_pipe.memory import MemoryBackend
from compactor import SimpleCompactor

async def main():
    # Initialize
    backend = MemoryBackend()
    compactor = SimpleCompactor()
    
    policy = WindowPolicy(
        token_budget=200,      # Small budget for demo
        trigger_at=0.8,        # Compact at 80%
        keep_n_recent=2,       # Always keep last 2 messages
    )
    engine = CompactionEngine(policy=policy, compactor=compactor)
    
    # Create a conversation
    conv = Conversation(id="chatbot-session-1")
    
    # Add messages
    conv.append(Message(Role.USER, "What is Python?", token_count=50))
    conv.append(Message(
        Role.ASSISTANT,
        "Python is a high-level programming language.",
        token_count=60,
    ))
    conv.append(Message(Role.USER, "Tell me more.", token_count=40))
    
    print(f"Before: {conv.total_tokens()} tokens, {len(conv.messages)} messages")
    
    # Save
    await backend.save(conv)
    
    # Load and compact
    loaded = await backend.load("chatbot-session-1")
    compacted = await engine.maybe_compact(loaded)
    
    print(f"After: {compacted.total_tokens()} tokens, {len(compacted.messages)} messages")
    print(f"Summaries: {len(compacted.summaries)}")
    
    # Save again
    await backend.save(compacted)

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Use in Your Application

Integrate into a chatbot loop:

```python
async def chat_loop():
    """Run a simple chat loop with context management."""
    backend = MemoryBackend()
    engine = CompactionEngine(WindowPolicy(), SimpleCompactor())
    
    conv = Conversation(id=f"session-{uuid4()}")
    
    while True:
        user_input = input("You: ")
        
        # Add user message
        conv.append(Message(
            role=Role.USER,
            content=user_input,
            token_count=len(user_input.split()),
        ))
        
        # Get LLM response (pseudo-code)
        response = await llm_call(conv)
        conv.append(Message(
            role=Role.ASSISTANT,
            content=response,
            token_count=len(response.split()),
        ))
        
        # Compact if needed
        conv = await engine.maybe_compact(conv)
        
        # Persist
        await backend.save(conv)
        
        print(f"Assistant: {response}")
```

## Common Patterns

### Load or Create

```python
async def load_or_create(backend, conv_id):
    """Load conversation or create if it doesn't exist."""
    if await backend.exists(conv_id):
        return await backend.load(conv_id)
    else:
        return Conversation(id=conv_id)
```

### Custom Token Counting

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

msg = Message(
    role=Role.USER,
    content="Hello!",
    token_count=count_tokens("Hello!"),
)
```

### Error Handling

```python
async def save_safely(backend, conv):
    """Save with retry logic."""
    for attempt in range(3):
        try:
            await backend.save(conv)
            return
        except Exception as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)
```

## Next Steps

- Read the [API Reference](api/core.md) for full documentation
- Check out [Backend Options](api/memory.md) for more storage choices
- Browse [examples](https://github.com/sarvesh4396/context-pipe/tree/main/examples)

## Troubleshooting

**Messages aren't being compacted:**
- Check that `trigger_at` is reasonable (e.g., 0.85 for 85%)
- Verify token counts are set correctly on messages
- Ensure your compactor doesn't raise exceptions

**Backend errors:**
- For Redis: ensure `redis-py` is installed and server is running
- For SQLAlchemy: check database connection string and run migrations

**Async errors:**
- All context-pipe operations are async; use `asyncio.run()` in scripts
- In FastAPI/Starlette, run within existing event loop

Have questions? Open an issue on [GitHub](https://github.com/sarvesh4396/context-pipe).
