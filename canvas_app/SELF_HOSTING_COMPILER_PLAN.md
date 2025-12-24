# Self-Hosting Compiler Plan

**Goal**: Build a minimal self-hosted NormCode compiler where the compiler itself is a NormCode plan that interacts with the user via Chat and displays artifacts on the Canvas.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      CHAT PANEL                                  │   │
│   │   (Primary interaction - user <-> compiler conversation)        │   │
│   │                                                                  │   │
│   │   [User] Compile: <- summary <= summarize <- doc                │   │
│   │   [Compiler] Deriving structure... Found 2 concepts.            │   │
│   │   [Compiler] Is <summary> semantic or syntactic?                │   │
│   │   [User] semantic                                                │   │
│   │   [Compiler] ✓ Compiled! View graph →                           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              ↑↓                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │             COMPILER NORMCODE PLAN (runs "under" chat)           │   │
│   │                                                                  │   │
│   │   Uses: ChatTool   - read/write messages, get user input        │   │
│   │   Uses: CanvasTool - display graph, show artifacts              │   │
│   │   Uses: LLMTool    - derivation, formalization                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    CANVAS (GRAPH VIEW)                           │   │
│   │   (Shows compiled plan structure, artifacts)                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Principle: "Under-Chat"

The NormCode compiler plan **drives** the conversation. The chat is both:
1. **Display** - shows messages from the compiler
2. **Input** - provides user responses to the compiler

```
NormCode Plan Execution
    │
    ├── chat.write("Paste your draft")    → Message appears in UI
    ├── chat.read_code()                  → Waits for user to paste code
    │       ↓
    │   [User pastes .ncds in chat]
    │       ↓
    ├── llm.ask(derive_prompt, draft)     → LLM derives structure
    ├── canvas.show_structure(concepts)   → Graph appears on canvas
    ├── chat.ask("Is X semantic?")        → Question appears, waits
    │       ↓
    │   [User responds]
    │       ↓
    └── ... continues ...
```

---

## Phase 1: Chat Tool (Priority: HIGH)

### 1.1 ChatTool Backend

**File**: `canvas_app/backend/tools/chat_tool.py`

```python
class CanvasChatTool:
    """
    Tool for NormCode plans to interact with the chat interface.
    
    The chat is both an output (display messages) and input (receive user responses).
    """
    
    def __init__(self, emit_callback=None):
        self._emit_callback = emit_callback
        self._pending_reads = {}  # request_id -> threading.Event
        self._responses = {}      # request_id -> response value
        self._lock = threading.Lock()
    
    # =========================================================================
    # Output Methods (write to chat)
    # =========================================================================
    
    def write(self, message: str, role: str = "assistant") -> None:
        """Write a plain text message to the chat."""
        # Emits: chat:message
        
    def write_code(self, code: str, language: str = "ncd", title: str = None) -> None:
        """Write a code block to the chat."""
        # Emits: chat:code_block
        
    def write_artifact(self, data: Any, artifact_type: str = "json", title: str = None) -> None:
        """Write a structured artifact (collapsible JSON, table, tree, etc.)."""
        # Emits: chat:artifact
    
    def write_error(self, message: str) -> None:
        """Write an error message to the chat."""
        # Emits: chat:message with role="error"
    
    def write_success(self, message: str) -> None:
        """Write a success message to the chat."""
        # Emits: chat:message with role="success"
    
    # =========================================================================
    # Input Methods (read from chat)
    # =========================================================================
    
    def read(self, prompt: str = None) -> str:
        """Wait for user's next text message."""
        # Emits: chat:input_request with type="text"
        # Blocks until: chat:input_response received
        
    def read_code(self, prompt: str = None, language: str = "ncd") -> str:
        """Request code input from user (opens code editor in chat)."""
        # Emits: chat:input_request with type="code"
        # Blocks until: chat:input_response received
        
    def ask(self, question: str, options: list = None) -> str:
        """Ask a question and wait for response. Options create buttons."""
        # Emits: chat:input_request with type="question" and options
        # Blocks until: chat:input_response received
        
    def confirm(self, message: str) -> bool:
        """Ask for yes/no confirmation."""
        # Emits: chat:input_request with type="confirm"
        # Returns True/False
    
    def select(self, prompt: str, choices: list) -> str:
        """Show a selection dropdown/list."""
        # Emits: chat:input_request with type="select"
    
    # =========================================================================
    # Response Handling (called by REST API)
    # =========================================================================
    
    def submit_response(self, request_id: str, response: Any) -> bool:
        """Submit user's response to unblock the waiting read."""
        
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending read request."""
        
    def get_pending_requests(self) -> list:
        """Get all pending input requests."""
```

### 1.2 WebSocket Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `chat:message` | Server→Client | `{role, content, timestamp}` | Text message |
| `chat:code_block` | Server→Client | `{code, language, title}` | Code block |
| `chat:artifact` | Server→Client | `{data, type, title}` | Structured artifact |
| `chat:input_request` | Server→Client | `{request_id, type, prompt, options}` | Request user input |
| `chat:input_response` | Client→Server | `{request_id, response}` | User's response |
| `chat:input_cancelled` | Client→Server | `{request_id}` | User cancelled |

### 1.3 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chat/messages` | Get chat history |
| `POST` | `/api/chat/send` | Send message from user |
| `GET` | `/api/chat/pending` | Get pending input requests |
| `POST` | `/api/chat/respond/{request_id}` | Submit response |
| `POST` | `/api/chat/cancel/{request_id}` | Cancel request |
| `DELETE` | `/api/chat/clear` | Clear chat history |

### 1.4 Files to Create

```
canvas_app/backend/
├── tools/
│   └── chat_tool.py              # ChatTool implementation
├── routers/
│   └── chat_router.py            # REST API endpoints
└── schemas/
    └── chat_schemas.py           # Pydantic models
```

---

## Phase 2: Chat Panel Frontend (Priority: HIGH)

### 2.1 Component Structure

```
canvas_app/frontend/src/components/panels/
└── ChatPanel.tsx
    ├── MessageList
    │   ├── TextMessage
    │   ├── CodeBlockMessage
    │   ├── ArtifactMessage (collapsible)
    │   └── SystemMessage (info/success/error)
    ├── InputArea
    │   ├── TextInput (default)
    │   ├── CodeEditor (when code requested)
    │   ├── OptionButtons (when options provided)
    │   └── ConfirmButtons (Yes/No)
    └── PendingIndicator (typing/waiting)
```

### 2.2 Chat Store

**File**: `canvas_app/frontend/src/stores/chatStore.ts`

```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error' | 'success';
  content: string;
  timestamp: number;
  // For code blocks
  code?: string;
  language?: string;
  // For artifacts
  artifact?: any;
  artifactType?: string;
  title?: string;
}

interface PendingInput {
  requestId: string;
  type: 'text' | 'code' | 'question' | 'confirm' | 'select';
  prompt: string;
  options?: string[];
  language?: string;
}

interface ChatStore {
  messages: ChatMessage[];
  pendingInput: PendingInput | null;
  isWaiting: boolean;
  
  // Actions
  addMessage: (msg: ChatMessage) => void;
  setPendingInput: (input: PendingInput | null) => void;
  sendMessage: (content: string) => Promise<void>;
  sendCode: (code: string) => Promise<void>;
  respond: (requestId: string, response: any) => Promise<void>;
  cancel: (requestId: string) => Promise<void>;
  clearChat: () => void;
}
```

### 2.3 UI Design

```
┌──────────────────────────────────────────────────────────────┐
│ 💬 Chat                                              [Clear] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 🤖 Welcome! Paste your NormCode draft to compile.       │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 👤 <- summary                                            │ │
│ │    <= summarize this                                     │ │
│ │    <- document                                           │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 🤖 Deriving structure...                                 │ │
│ │ Found 2 concepts: summary, document                      │ │
│ │ ▼ View Structure                                         │ │
│ │   ┌──────────────────────────────────────────────────┐   │ │
│ │   │ { "concepts": [...], "inferences": [...] }      │   │ │
│ │   └──────────────────────────────────────────────────┘   │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ 🤖 Is `summarize this` a semantic or syntactic function? │ │
│ │   [Semantic]  [Syntactic]                               │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ [Code] │____________________________│ [Send]                │
└──────────────────────────────────────────────────────────────┘
```

### 2.4 Files to Create

```
canvas_app/frontend/src/
├── components/panels/
│   └── ChatPanel.tsx             # Main chat panel
├── stores/
│   └── chatStore.ts              # Chat state management
└── types/
    └── chat.ts                   # TypeScript types
```

---

## Phase 3: Canvas Tool (Priority: MEDIUM)

### 3.1 CanvasTool Backend

**File**: `canvas_app/backend/tools/canvas_tool.py`

```python
class CanvasDisplayTool:
    """
    Tool for NormCode plans to display artifacts on the Canvas.
    
    Unlike ChatTool (interactive), CanvasTool is primarily for display.
    """
    
    def __init__(self, emit_callback=None, project_context=None):
        self._emit_callback = emit_callback
        self._project_context = project_context
    
    # =========================================================================
    # Display Methods
    # =========================================================================
    
    def show_source(self, code: str, language: str = "ncds", title: str = None) -> None:
        """Display source code in a source viewer panel."""
        # Emits: canvas:show_source
        
    def show_structure(self, structure: dict, title: str = None) -> None:
        """Display a concept/inference structure as a tree or graph."""
        # Emits: canvas:show_structure
        
    def load_plan(self, concepts: list, inferences: list) -> None:
        """Load a compiled plan into the graph view."""
        # Emits: canvas:load_plan
        
    def highlight_node(self, flow_index: str, style: str = "focus") -> None:
        """Highlight a specific node in the graph."""
        # Emits: canvas:highlight_node
        
    def add_annotation(self, flow_index: str, text: str, type: str = "info") -> None:
        """Add an annotation to a node."""
        # Emits: canvas:add_annotation
        
    def clear(self) -> None:
        """Clear the canvas display."""
        # Emits: canvas:clear
    
    # =========================================================================
    # State Methods
    # =========================================================================
    
    def get_selected_node(self) -> Optional[dict]:
        """Get currently selected node info."""
        
    def get_graph_state(self) -> dict:
        """Get current graph state (nodes, edges, selection)."""
```

### 3.2 WebSocket Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `canvas:show_source` | Server→Client | `{code, language, title}` | Show source viewer |
| `canvas:show_structure` | Server→Client | `{structure, title}` | Show structure tree |
| `canvas:load_plan` | Server→Client | `{concepts, inferences}` | Load graph |
| `canvas:highlight_node` | Server→Client | `{flowIndex, style}` | Highlight node |
| `canvas:add_annotation` | Server→Client | `{flowIndex, text, type}` | Add annotation |
| `canvas:clear` | Server→Client | `{}` | Clear display |

---

## Phase 4: Minimal Compiler NormCode Plan (Priority: HIGH)

### 4.1 Plan Structure

The compiler is itself a NormCode plan that uses chat and canvas tools:

```
compiler/
├── compiler.ncds                 # Draft of the compiler plan
├── compiler.concept.json         # Compiled concept repository
├── compiler.inference.json       # Compiled inference repository
├── paradigms/
│   ├── chat_read.json           # Paradigm for reading from chat
│   ├── chat_ask.json            # Paradigm for asking questions
│   ├── llm_derive.json          # Paradigm for LLM derivation
│   └── llm_formalize.json       # Paradigm for LLM formalization
└── prompts/
    ├── derive.md                 # Derivation prompt
    ├── formalize.md              # Formalization prompt
    └── activate.md               # Activation prompt
```

### 4.2 Compiler Plan (Draft)

```ncds
# compiler.ncds - The NormCode Compiler as a NormCode Plan

<- compilation result
    <= report: send success message and show graph
    <- activated plan
        <= activate: generate concept.json and inference.json
        <- confirmed structure
            <= confirm: ask user to approve formalized structure
            <- formalized plan
                <= formalize: add types, operators, paradigms
                <- confirmed derivation
                    <= confirm: ask user to approve derived concepts
                    <- derived structure
                        <= derive: parse input into concepts and inferences
                        <- user input
                            <= read: get draft from user via chat
                            <- chat welcome
                                <= greet: display welcome message
```

### 4.3 Inference Working Interpretations

Each inference uses specific tools:

```json
{
  "inferences": [
    {
      "to_infer": "chat_welcome",
      "function_concept": "greet",
      "working_interpretation": {
        "paradigm": "chat_write",
        "tool": "chat",
        "method": "write",
        "message": "Welcome! Paste your NormCode draft (.ncds) to compile."
      }
    },
    {
      "to_infer": "user_input",
      "function_concept": "read",
      "value_concepts": ["chat_welcome"],
      "working_interpretation": {
        "paradigm": "chat_read_code",
        "tool": "chat",
        "method": "read_code",
        "prompt": "Paste your draft:",
        "language": "ncds"
      }
    },
    {
      "to_infer": "derived_structure",
      "function_concept": "derive",
      "value_concepts": ["user_input"],
      "working_interpretation": {
        "paradigm": "llm_derive",
        "prompt_location": "prompts/derive.md",
        "tool": "llm",
        "method": "ask"
      }
    }
  ]
}
```

### 4.4 Custom Paradigms

**chat_write.json** - Write message to chat:
```json
{
  "name": "chat_write",
  "description": "Write a message to the chat interface",
  "sequence": ["python_execute"],
  "script": "result = Body.chat.write(message)",
  "inputs": {
    "message": "The message to write"
  }
}
```

**chat_read_code.json** - Read code from chat:
```json
{
  "name": "chat_read_code",
  "description": "Request code input from user via chat",
  "sequence": ["python_execute"],
  "script": "result = Body.chat.read_code(prompt, language)",
  "inputs": {
    "prompt": "The prompt to show",
    "language": "The code language"
  }
}
```

**chat_ask.json** - Ask question with options:
```json
{
  "name": "chat_ask",
  "description": "Ask user a question via chat",
  "sequence": ["python_execute"],
  "script": "result = Body.chat.ask(question, options)",
  "inputs": {
    "question": "The question to ask",
    "options": "List of options (optional)"
  }
}
```

---

## Phase 5: Integration & Self-Hosting (Priority: LOW)

### 5.1 Tool Injection

The Chat and Canvas tools must be injected into Body during execution:

```python
# In execution_service.py

def _create_body_with_tools(self, emit_callback):
    """Create Body with all canvas tools including chat and canvas."""
    body = Body(...)
    
    # Existing tools
    body.llm = CanvasLLMTool(emit_callback=emit_callback, ...)
    body.python_interpreter = CanvasPythonInterpreterTool(...)
    body.file_system = CanvasFileSystemTool(...)
    body.user_input = CanvasUserInputTool(...)
    
    # New tools
    body.chat = CanvasChatTool(emit_callback=emit_callback)
    body.canvas = CanvasDisplayTool(emit_callback=emit_callback)
    
    return body
```

### 5.2 Self-Hosting Flow

1. **Open compiler project** in Canvas App
2. **Compiler's own graph** is visible
3. **Type in chat**: User starts interaction
4. **Compiler plan executes**, using chat/canvas tools
5. **User can modify compiler** (edit the NormCode plan)
6. **Re-run** to see effect of changes

### 5.3 Dual-Project Support (Future)

- Tab-based project switching
- Cross-project tool access
- Meta-compilation (compiler compiling itself)

---

## Implementation Order

### Week 1-2: Chat Foundation

| Priority | Task | Files | Effort |
|----------|------|-------|--------|
| P0 | `CanvasChatTool` backend | `tools/chat_tool.py` | 4h |
| P0 | Chat WebSocket events | `websocket_router.py` | 2h |
| P0 | Chat REST API | `routers/chat_router.py` | 2h |
| P0 | `ChatPanel` component | `ChatPanel.tsx` | 6h |
| P0 | `chatStore` state | `stores/chatStore.ts` | 2h |
| P0 | Chat WebSocket handlers | `useWebSocket.ts` | 2h |

### Week 3: Canvas Tool

| Priority | Task | Files | Effort |
|----------|------|-------|--------|
| P1 | `CanvasDisplayTool` backend | `tools/canvas_tool.py` | 3h |
| P1 | Canvas WebSocket events | `websocket_router.py` | 2h |
| P1 | Source viewer component | `SourceViewer.tsx` | 3h |
| P1 | Structure tree component | `StructureTree.tsx` | 3h |

### Week 4: Minimal Compiler

| Priority | Task | Files | Effort |
|----------|------|-------|--------|
| P1 | Compiler plan draft | `compiler.ncds` | 4h |
| P1 | Chat paradigms | `paradigms/chat_*.json` | 2h |
| P1 | Derive prompt | `prompts/derive.md` | 2h |
| P1 | Tool injection | `execution_service.py` | 2h |
| P1 | End-to-end test | - | 4h |

---

## Success Criteria

### Minimum Viable

- [ ] User can type in chat, compiler responds
- [ ] Compiler can read code from chat
- [ ] Compiler can ask questions with options
- [ ] Compiler can display artifacts on canvas
- [ ] Simple plan can be compiled via chat

### Full Feature

- [ ] Compiler plan is itself viewable on canvas
- [ ] User can modify compiler and see changes
- [ ] Derivation → Formalization → Activation works
- [ ] Compiled plan loads into graph view

---

## Technical Notes

### Thread Safety

ChatTool uses same pattern as UserInputTool:
- `threading.Event` for blocking reads
- `threading.Lock` for shared state
- REST API unblocks waiting threads

### Message History

Chat messages stored in memory during session. Future:
- Persist to project config
- Export chat log
- Replay conversations

### Artifact Types

Supported artifact types:
- `json` - Collapsible JSON viewer
- `tree` - Expandable tree structure
- `table` - Data table
- `diff` - Side-by-side diff
- `graph` - Mini graph preview

---

## Related Documents

- [Canvas App Overview](documentation/current/5_tools/canvas_app_overview.md)
- [Tools README](canvas_app/backend/tools/README.md)
- [Implementation Journal](canvas_app/IMPLEMENTATION_JOURNAL.md)
- [NormCode Overview](documentation/current/1_intro/overview.md)

---

**Created**: December 24, 2024  
**Status**: Planning

