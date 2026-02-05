# Muse Bio AI Agent - Technical Documentation

## Table of Contents

1. [Tech Stack Overview](#tech-stack-overview)
2. [System Architecture](#system-architecture)
3. [Claude SDK Deep Dive](#claude-sdk-deep-dive)
4. [Agent Design Patterns](#agent-design-patterns)
5. [Knowledge Base Integration](#knowledge-base-integration)
6. [Conversation Management](#conversation-management)
7. [PDF Handling System](#pdf-handling-system)
8. [Web Interface Architecture](#web-interface-architecture)
9. [Security Considerations](#security-considerations)
10. [Performance Optimization](#performance-optimization)

---

## Tech Stack Overview

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.10+ | Core application runtime |
| AI SDK | Anthropic Python SDK | 0.40.0+ | Interface to Claude API |
| Web Framework | FastAPI | 0.109.0+ | REST API and static file serving |
| ASGI Server | Uvicorn | 0.27.0+ | Production-grade async server |
| Data Validation | Pydantic | 2.5.0+ | Request/response validation |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Markup | HTML5 | Page structure |
| Styling | CSS3 (Custom Properties) | Theming and layout |
| JavaScript | Vanilla ES6+ | Client-side interactivity |
| Markdown | marked.js | Render markdown in chat |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| Virtual Environment | Dependency isolation |
| Session Storage | In-memory dict (production: Redis) |
| File Storage | Local filesystem for PDFs and KB |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │   HTML/CSS    │  │  JavaScript   │  │    marked.js      │   │
│  │  (Interface)  │  │  (app.js)     │  │  (MD Rendering)   │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (Uvicorn)                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │  /chat POST   │  │  /pdfs GET    │  │  /static/* GET    │   │
│  │  (Chat API)   │  │  (PDF Serve)  │  │  (Static Files)   │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Session Manager                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ Session #1  │  │ Session #2  │  │ Session #N  │       │  │
│  │  │Agent Inst. │  │ Agent Inst. │  │ Agent Inst. │       │  │
│  │  │ Conv. Hist. │  │ Conv. Hist. │  │ Conv. Hist. │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS API Call
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Anthropic Claude API                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Claude Sonnet Model                      │  │
│  │  • System Prompt (KB + Instructions)                       │  │
│  │  • Conversation History                                    │  │
│  │  • Response Generation                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **User Input** → Browser captures message
2. **HTTP POST** → `/chat` endpoint receives request
3. **Session Lookup** → Find or create session with agent instance
4. **Agent Processing** → User type detection, PDF matching
5. **Claude API Call** → Send system prompt + history + user message
6. **Response Processing** → Parse response, attach PDF suggestions
7. **HTTP Response** → Return JSON to browser
8. **UI Update** → Render markdown, show PDF previews

---

## Claude SDK Deep Dive

### What is the Anthropic SDK?

The Anthropic Python SDK is the official client library for interacting with Claude models via the Anthropic API. It provides a clean, typed interface for:

- Sending messages to Claude
- Managing conversations
- Handling streaming responses
- Error handling and retries

### SDK Installation

```python
pip install anthropic
```

### Core SDK Components

#### 1. Client Initialization

```python
import anthropic

# Initialize with API key (from environment or explicit)
client = anthropic.Anthropic(api_key="sk-ant-...")

# Or use environment variable ANTHROPIC_API_KEY
client = anthropic.Anthropic()
```

**What happens internally:**
- Creates an HTTP client with proper headers
- Sets up authentication
- Configures retry logic and timeouts
- Validates API key format

#### 2. Message Creation

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

**Parameters Explained:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | str | Model identifier (e.g., "claude-sonnet-4-20250514") |
| `max_tokens` | int | Maximum tokens in response (1-4096 typical) |
| `system` | str | System prompt - sets behavior and context |
| `messages` | list | Conversation history as role/content pairs |
| `temperature` | float | Randomness (0.0-1.0, default ~1.0) |
| `top_p` | float | Nucleus sampling parameter |
| `stop_sequences` | list | Strings that stop generation |

#### 3. Response Structure

```python
# Response object structure
response.id          # Unique message ID
response.type        # "message"
response.role        # "assistant"
response.content     # List of content blocks
response.model       # Model used
response.stop_reason # Why generation stopped
response.usage       # Token counts

# Extracting text
text = response.content[0].text
```

#### 4. Conversation History Format

```python
messages = [
    {"role": "user", "content": "What is Muse Bio?"},
    {"role": "assistant", "content": "Muse Bio is a biotech company..."},
    {"role": "user", "content": "Tell me about the programs."},
]
```

**Rules:**
- Messages must alternate between "user" and "assistant"
- First message must be from "user"
- System prompt is separate (not in messages array)

### How Claude Processes Requests

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Processing Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. TOKENIZATION                                                 │
│     ├── System prompt → tokens                                   │
│     ├── Conversation history → tokens                            │
│     └── User message → tokens                                    │
│                                                                   │
│  2. CONTEXT WINDOW                                               │
│     ├── All tokens combined into context                         │
│     ├── Model: claude-sonnet-4 has 200K token context            │
│     └── Our KB (~8K words) ≈ 10-12K tokens                       │
│                                                                   │
│  3. ATTENTION MECHANISM                                          │
│     ├── Self-attention across all tokens                         │
│     ├── System prompt has persistent influence                   │
│     └── Recent messages weighted more heavily                    │
│                                                                   │
│  4. GENERATION                                                   │
│     ├── Token-by-token prediction                                │
│     ├── Temperature affects randomness                           │
│     └── Stop at max_tokens or stop_sequence                      │
│                                                                   │
│  5. POST-PROCESSING                                              │
│     ├── Detokenization to text                                   │
│     └── Safety filtering                                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Token Economics

| Component | Approximate Tokens |
|-----------|-------------------|
| System prompt (with KB) | ~12,000 |
| Average user message | 20-100 |
| Average response | 200-800 |
| Context limit (Sonnet) | 200,000 |

**Cost Calculation:**
- Input tokens: $3 per million (Sonnet)
- Output tokens: $15 per million (Sonnet)
- Average conversation (10 turns): ~$0.02-0.05

---

## Agent Design Patterns

### 1. System Prompt Engineering

The system prompt is the foundation of agent behavior. Our implementation uses a structured approach:

```python
def _build_system_prompt(self) -> str:
    return f"""
    [ROLE DEFINITION]
    You are the Muse Bio AI Assistant...

    [CRITICAL CONSTRAINTS]
    NEVER provide medical advice...

    [TONE GUIDELINES]
    Talk like a friendly, knowledgeable friend...

    [USER CONTEXT]
    {user_type_specific_instructions}

    [KNOWLEDGE BASE]
    {self.knowledge_base}

    [RESPONSE GUIDELINES]
    For DONORS: ...
    For INVESTORS: ...
    For PARTNERS: ...
    """
```

**Why This Structure Works:**

1. **Role Definition First** - Sets the identity before any instructions
2. **Constraints Before Capabilities** - Negative constraints are more reliably followed when stated early
3. **Dynamic Context Injection** - User type context adapts the prompt
4. **Knowledge Base Embedding** - Full KB in system prompt for consistent access

### 2. User Type Detection

```python
USER_TYPE_KEYWORDS = {
    "donor": ["donate", "donation", "cup", "sample", ...],
    "investor": ["invest", "funding", "equity", ...],
    "partner": ["partner", "collaborate", "distribution", ...]
}

def _detect_user_type(self, message: str) -> Optional[str]:
    message_lower = message.lower()
    scores = {"donor": 0, "investor": 0, "partner": 0}

    for user_type, keywords in USER_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                scores[user_type] += 1

    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)
    return None
```

**Algorithm:**
1. Keyword frequency scoring
2. Highest score wins
3. Tie-breaking by dict order
4. None if no keywords match

**Why keyword matching over ML classification:**
- Deterministic and explainable
- No additional model calls
- Fast (O(n) string matching)
- Easy to modify keywords
- Sufficient for 3 clear categories

### 3. Stateful Conversation Management

```python
class MuseBioAgent:
    def __init__(self):
        self.conversation_history = []  # Persists across calls
        self.detected_user_type = None  # Sticky after first detection
        self.offered_pdfs = set()       # Track to avoid repetition

    def chat(self, user_message: str) -> str:
        # Append to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # API call with full history
        response = self.client.messages.create(
            messages=self.conversation_history,
            ...
        )

        # Append response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content[0].text
        })
```

**State Management Principles:**

| State | Scope | Purpose |
|-------|-------|---------|
| `conversation_history` | Per-session | Context for Claude |
| `detected_user_type` | Per-session, sticky | Adapt instructions |
| `offered_pdfs` | Per-session | Avoid repetition |

---

## Knowledge Base Integration

### Why Embed KB in System Prompt?

**Alternative Approaches:**

| Approach | Pros | Cons |
|----------|------|------|
| **System Prompt Embedding** (our choice) | Always available, consistent, no latency | Uses tokens, static |
| **RAG (Retrieval)** | Dynamic, saves tokens | Added latency, complexity, retrieval errors |
| **Fine-tuning** | Fast inference | Expensive, can't update easily |
| **Function Calling** | Structured data | Extra API calls |

**Our Choice Rationale:**
- KB is ~8K words (fits easily in 200K context)
- Information needs to be consistently available
- No retrieval latency
- Simpler architecture
- KB updates just require file edit

### KB Structure

```markdown
# Knowledge Base Layout

## CRITICAL CONSTRAINTS (Top)
- Medical boundaries
- What agent must NEVER do

## TONE GUIDELINES
- Voice characteristics
- Example phrases

## FACTUAL CONTENT (Bulk)
- Company info
- Program details
- Eligibility requirements
- Procedures

## QUICK REFERENCE (Bottom)
- Key phrases
- Red flags
- Escalation triggers
```

**Why This Order:**
1. Constraints at top = higher attention weight
2. Tone before content = consistent voice
3. Details in middle = searchable context
4. Quick reference at end = easy lookup

---

## Conversation Management

### Session Architecture

```python
# In-memory session storage
sessions: dict[str, dict] = {}

# Session structure
sessions[session_id] = {
    "agent": MuseBioAgent(),      # Dedicated agent instance
    "created_at": datetime.now(),  # For cleanup
    "message_count": 0             # Analytics
}
```

**Why Per-Session Agent Instances:**
- Isolated conversation history
- Independent state tracking
- Clean session reset
- Memory predictability

### Session Lifecycle

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Create  │────▶│ Active  │────▶│ Idle    │────▶│ Cleanup │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │
     │               │               │               │
  No session_id   Messages      No activity      TTL expired
  in request      exchanged     for period       (24 hours)
```

### Cleanup Strategy

```python
SESSION_TIMEOUT_HOURS = 24

def cleanup_old_sessions():
    cutoff = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)
    expired = [
        sid for sid, data in sessions.items()
        if data.get("created_at", datetime.now()) < cutoff
    ]
    for sid in expired:
        del sessions[sid]
```

**Triggered:** On every chat request (background task)

---

## PDF Handling System

### PDF Resource Configuration

```python
PDF_RESOURCES = {
    "menstrual_cup_guide": {
        "file": "How_to_use_a_menstrual_cup.pdf",
        "description": "Complete Guide: How to Use a Menstrual Cup",
        "triggers": ["cup", "menstrual cup", "how to use", "insertion"]
    },
    ...
}
```

### Trigger Matching Algorithm

```python
def _find_relevant_pdfs(self, message: str) -> list[dict]:
    message_lower = message.lower()
    relevant = []

    for pdf_key, pdf_info in PDF_RESOURCES.items():
        # Skip already offered
        if pdf_key in self.offered_pdfs:
            continue

        # Check triggers
        for trigger in pdf_info["triggers"]:
            if trigger in message_lower:
                relevant.append({...})
                break  # One match is enough

    return relevant
```

**Deduplication:** `offered_pdfs` set prevents repeated suggestions

### PDF Serving for Embedding

```python
@app.get("/pdfs/{pdf_key}")
async def download_pdf(pdf_key: str):
    ...
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            # CRITICAL: "inline" allows browser embedding
            "Content-Disposition": f"inline; filename=\"{filename}\"",
        }
    )
```

**Content-Disposition Values:**
- `attachment` - Forces download
- `inline` - Allows browser rendering/embedding

---

## Web Interface Architecture

### Component Structure

```
static/
├── index.html    # Structure and semantic markup
├── styles.css    # Visual design and theming
└── app.js        # Behavior and API communication
```

### CSS Architecture (Custom Properties)

```css
:root {
    /* Design tokens */
    --primary: #d4577a;           /* Muse Bio pink */
    --primary-hover: #c44a6d;
    --primary-light: #fdf2f4;

    /* Semantic tokens */
    --gray-50 through --gray-900  /* Neutral scale */

    /* Layout tokens */
    --sidebar-width: 280px;
    --header-height: 64px;
}
```

**Benefits:**
- Single source of truth for colors
- Easy theme modifications
- Consistent spacing

### JavaScript Architecture

```javascript
// State
let sessionId = null;
let isLoading = false;

// Core functions
async function sendMessage(message) { ... }
function addMessage(content, role, pdfs) { ... }
function createPdfPreview(pdf) { ... }

// Event-driven
chatForm.addEventListener('submit', handleSubmit);
```

**Pattern:** Vanilla JS with async/await, no framework overhead

### Markdown Rendering

```javascript
// Configure marked.js
marked.setOptions({
    breaks: true,      // \n becomes <br>
    gfm: true,         // GitHub Flavored Markdown
    headerIds: false,  // No auto IDs on headers
    mangle: false      // Don't escape emails
});

// Clean and render
let cleanContent = content
    .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')  // Remove emojis
    .replace(/:\)/g, '');                      // Remove text emotes

textDiv.innerHTML = marked.parse(cleanContent);
```

### PDF Preview Implementation

```javascript
// Using <object> tag for better PDF rendering
container.innerHTML = `
    <object
        class="pdf-preview-frame"
        data="${API_BASE_URL}/pdfs/${pdf.key}"
        type="application/pdf"
    >
        <p>PDF preview not available.
           <a href="..." target="_blank">Click here</a>
        </p>
    </object>
`;
```

**Why `<object>` over `<iframe>`:**
- Better native PDF rendering
- Graceful fallback content
- More consistent cross-browser

---

## Security Considerations

### API Key Protection

```python
# NEVER hardcode
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Validate presence
if not api_key:
    raise ValueError("API key not configured")
```

**Best Practices:**
- Environment variables only
- Never commit keys to git
- Rotate keys if exposed
- Use `.env` files locally (gitignored)

### Input Validation

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
```

**Pydantic Provides:**
- Type validation
- Length constraints
- Automatic error responses

### Medical Boundary Enforcement

```
System Prompt:
"MUSE BIO IS NOT A MEDICAL PRACTICE. You CANNOT and DO NOT
provide medical advice, diagnosis, or treatment.

NEVER:
- Diagnose any medical condition
- Interpret test results or symptoms
- Recommend treatments or medications
..."
```

**Multi-layer Enforcement:**
1. System prompt constraints (primary)
2. Example responses in prompt
3. Red flag detection patterns
4. Human escalation triggers

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendation:**
```python
allow_origins=["https://yourdomain.com"]
```

---

## Performance Optimization

### Latency Breakdown

| Component | Typical Latency | Optimization |
|-----------|----------------|--------------|
| Network to Claude | 100-300ms | Can't optimize |
| Claude processing | 1-5s | Reduce max_tokens |
| PDF serving | 10-50ms | File caching |
| Session lookup | <1ms | In-memory dict |

### Token Optimization

```python
# Response length control
response = client.messages.create(
    max_tokens=1024,  # Cap response length
    ...
)
```

**Trade-off:** Shorter responses = faster + cheaper, but may truncate

### Caching Strategies

| What | How | Benefit |
|------|-----|---------|
| Knowledge Base | Load once at init | No file I/O per request |
| PDF file list | Load at startup | Fast sidebar rendering |
| Static files | Browser caching | Reduced server load |

### Async Architecture

```python
# FastAPI is async by default
@app.post("/chat")
async def chat(request: ChatRequest):
    # Non-blocking I/O
    response = await some_async_operation()
```

**Uvicorn Workers:**
```bash
uvicorn musebio_api:app --workers 4  # Multi-process
```

---

## Deployment Considerations

### Production Checklist

- [ ] Set `ANTHROPIC_API_KEY` securely
- [ ] Configure CORS for specific origins
- [ ] Use Redis for session storage
- [ ] Set up HTTPS (TLS)
- [ ] Add rate limiting
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Use production ASGI server

### Docker Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "musebio_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
LOG_LEVEL=INFO
SESSION_TIMEOUT_HOURS=24
MAX_TOKENS=1024
```

---

## Summary

This agent demonstrates a production-ready pattern for building conversational AI applications:

1. **Claude SDK** provides clean API access to powerful language models
2. **System Prompt Engineering** shapes behavior without fine-tuning
3. **Stateful Sessions** maintain conversation context
4. **Knowledge Base Embedding** ensures consistent, accurate responses
5. **User Type Detection** enables personalized experiences
6. **FastAPI Backend** offers modern, async API infrastructure
7. **Clean Frontend** provides accessible user interface

The architecture prioritizes simplicity, maintainability, and user experience while leveraging Claude's capabilities for nuanced, context-aware conversations.

---

*Document Version: 1.0*
*Last Updated: February 2026*
*Author: Technical Documentation*
