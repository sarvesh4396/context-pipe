# Compaction Algorithms

context-pipe supports different strategies for managing conversation history within token budgets. This guide explores the implemented approach and alternatives.

## Current Implementation: Token-Based Compaction

### How It Works

The current `WindowPolicy` uses a **token budget** model:

```python
policy = WindowPolicy(
    token_budget=4096,          # Max tokens allowed
    trigger_at=0.85,            # Trigger compaction at 85% capacity
    keep_n_recent=6,            # Keep 6 most recent messages
    wipe_mode=WipeMode.WIPE     # Remove old messages after compacting
)
```

**Algorithm Flow:**
1. **Monitor**: Track total tokens across all messages
2. **Detect**: When `total_tokens >= token_budget * trigger_at` (80% threshold)
3. **Compact**: Summarize all messages except the last `keep_n_recent`
4. **Wipe**: Remove summarized messages (or keep them based on wipe_mode)

**Pros:**
- ✅ Accurate to LLM context windows
- ✅ Works with different token counts per message
- ✅ Provider-agnostic (you define token counting)
- ✅ Predictable memory usage

**Cons:**
- ❌ Requires accurate token counting
- ❌ Token counting varies by LLM provider (GPT, Claude, Llama)
- ❌ May over-trigger on long messages

### Example

```python
from context_pipe import (
    Conversation, Message, Role, 
    WindowPolicy, CompactionEngine, AbstractCompactor
)

class LLMCompactor(AbstractCompactor):
    async def asummarize(self, messages):
        # Call your LLM API to summarize
        summary = await openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Summarize: {msg.content}"}]
        )
        return summary.choices[0].message.content

# Set up
policy = WindowPolicy(token_budget=4096, trigger_at=0.85, keep_n_recent=5)
engine = CompactionEngine(policy=policy, compactor=LLMCompactor())

# Use
conv = Conversation(id="chat-1")
conv.append(Message(role=Role.USER, content="...", token_count=150))
# ... add more messages ...

compacted = await engine.maybe_compact(conv)
```

---

## Alternative: Sliding Window (Recent K Messages)

### How It Works

Instead of token budgets, keep a fixed number of recent messages and summarize older ones:

```python
policy = SlidingWindowPolicy(
    window_size=10,             # Keep last 10 messages
)
```

**Algorithm Flow:**
1. **Check**: If `len(messages) > window_size`
2. **Compact**: Summarize messages outside the window
3. **Keep**: Latest `window_size` messages always active

**Pros:**
- ✅ Simple to understand
- ✅ No token counting needed
- ✅ Predictable behavior
- ✅ Good for chat-heavy workloads

**Cons:**
- ❌ Ignores message length (short vs long messages treated equally)
- ❌ May run out of tokens with long messages
- ❌ Less accurate to actual context windows

### Example

```python
# Hypothetical SlidingWindowPolicy
policy = SlidingWindowPolicy(window_size=10)

conv = Conversation(id="chat-1")
for i in range(25):
    conv.append(Message(role=Role.USER, content=f"Message {i}", token_count=10))

# After compaction: keep last 10, summarize first 15
compacted = await engine.maybe_compact(conv)
assert len(compacted.active_messages()) <= 10
```

---

## Hybrid: Token-Aware Sliding Window

Combines both approaches:

```python
policy = HybridPolicy(
    token_budget=4096,
    window_size=10,
    # Trigger when EITHER condition is met:
    # - Total tokens >= 80% of budget
    # - Active messages > 10
)
```

**When to use:**
- Most LLM applications
- Balance between accuracy and simplicity
- Works across different message sizes

---

## Recommended Approach

**For most LLM applications: Token-Based (current)**

1. Accurately reflects real context limits
2. Works with all LLM providers
3. Requires only token counting (providers give this)
4. Most predictable behavior

**Implementation checklist:**
- ✅ Define `token_budget` (what's your actual context window?)
- ✅ Choose `trigger_at` (0.75-0.85 recommended)
- ✅ Set `keep_n_recent` (5-10 messages)
- ✅ Implement token counting (from provider docs)

---

## Future Extensions

To implement `SlidingWindowPolicy`:

```python
@dataclass
class SlidingWindowPolicy:
    """Fixed-size window of recent messages."""
    window_size: int = 10
    wipe_mode: WipeMode = WipeMode.WIPE

class SlidingWindowEngine:
    """Compact based on message count, not tokens."""
    
    async def maybe_compact(self, conv: Conversation) -> Conversation:
        if len(conv.messages) <= self.policy.window_size:
            return conv
        
        # Summarize everything except recent
        old_messages = conv.messages[:-self.policy.window_size]
        summary_text = await self.compactor.asummarize(old_messages)
        
        conv.summaries.append(Summary(
            text=summary_text,
            span_start=0,
            span_end=len(old_messages) - 1,
        ))
        
        if self.policy.wipe_mode == WipeMode.WIPE:
            conv.messages = conv.messages[-self.policy.window_size:]
        
        return conv
```

---

## Testing Locally

Run compaction tests:

```bash
make test-unit          # Run all unit tests
make test              # Run tests with services
```

Compare algorithms in a test:

```python
async def test_token_vs_sliding():
    conv = await create_conversation_with_varied_messages()
    
    # Token-based
    token_policy = WindowPolicy(token_budget=1000)
    token_engine = CompactionEngine(token_policy, compactor)
    token_result = await token_engine.maybe_compact(conv)
    
    # Sliding window (future)
    window_policy = SlidingWindowPolicy(window_size=5)
    window_engine = SlidingWindowEngine(window_policy, compactor)
    window_result = await window_engine.maybe_compact(conv)
    
    # Compare behaviors
```

---

## Choose Your Strategy

| Strategy | Accuracy | Simplicity | Best For |
|----------|----------|-----------|----------|
| **Token-Based** ⭐ | High | Medium | LLM apps, production |
| **Sliding Window** | Medium | High | Prototypes, testing |
| **Hybrid** | High | Medium | Complex needs |

Start with **Token-Based** — it's what production systems use.
