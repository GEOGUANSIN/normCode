# Agent Customizing Panel - Implementation Plan

**Feature**: Enable customized agent bodies with configurable tools per inference  
**Target**: Canvas App Phase 4+  
**Date**: December 20, 2024  
**Status**: ✅ Initial Implementation Complete

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `agent_service.py` | ✅ Complete | AgentConfig, AgentRegistry, AgentMappingService, MonitoredToolProxy |
| `agent_router.py` | ✅ Complete | Full CRUD endpoints, mapping rules, tool call history |
| `agentStore.ts` | ✅ Complete | Zustand store with full state management |
| `AgentPanel.tsx` | ✅ Complete | Agent list, editor modal, tool call feed |
| `App.tsx` integration | ✅ Complete | Toggle button, panel display in canvas view |
| `useWebSocket.ts` | ✅ Complete | Handles tool call and agent events |
| `api.ts` | ✅ Complete | All agent API functions |
| Execution integration | ✅ Complete | Tool call monitoring wired to WebSocket events |

---

## Overview

### The Problem

Currently, NormCode uses a **single Body** instance throughout an entire plan execution:

```python
# Current pattern in orchestration_runner.py
body = Body(llm_name=llm_model, base_dir=base_dir)
orchestrator = Orchestrator(concept_repo, inference_repo, body, ...)
```

This means:
- All inferences use the same LLM model
- All inferences share the same tools (file_system, python_interpreter, etc.)
- No way to monitor/control individual tool calls per inference
- No per-inference agent customization

### The Solution

Introduce an **Agent Customizing Panel** that allows:
1. **Multiple Agent Configurations** - Define different agents with different tools
2. **Per-Inference Agent Assignment** - Assign specific agents to specific inferences
3. **Tool Monitoring** - Real-time visibility into tool calls during execution
4. **Custom Tool Injection** - Override default tools with UI-integrated versions

---

## Architecture

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Orchestrator                             │
├─────────────────────────────────────────────────────────────────┤
│  Body (single instance)                                         │
│  ├── llm: LanguageModel                                        │
│  ├── prompt_tool: PromptTool                                   │
│  ├── file_system: FileSystemTool                               │
│  ├── python_interpreter: PythonInterpreterTool                 │
│  ├── user_input: UserInputTool                                 │
│  ├── formatter_tool: FormatterTool                             │
│  ├── composition_tool: CompositionTool                         │
│  ├── perception_router: PerceptionRouter                       │
│  └── paradigm_tool: ParadigmTool                               │
├─────────────────────────────────────────────────────────────────┤
│  All Inferences → Same Body                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Orchestrator                             │
├─────────────────────────────────────────────────────────────────┤
│  AgentRegistry                                                  │
│  ├── "default": Body(llm="qwen-plus", ...)                     │
│  ├── "analyst": Body(llm="gpt-4o", custom_tools=...)           │
│  ├── "coder": Body(llm="claude-3", python_interpreter=...)     │
│  └── "reviewer": Body(llm="qwen-turbo", ...)                   │
├─────────────────────────────────────────────────────────────────┤
│  Inference → Agent Assignment                                   │
│  ├── flow_index "1.1" → "analyst"                              │
│  ├── flow_index "1.2" → "coder"                                │
│  └── flow_index "1.3" → "default"                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Agent Configuration Schema

```typescript
interface AgentConfig {
  id: string;                    // Unique identifier (e.g., "analyst", "coder")
  name: string;                  // Display name
  description?: string;          // Optional description
  
  // LLM Configuration
  llm: {
    model: string;               // Model name (e.g., "qwen-plus", "gpt-4o")
    temperature?: number;        // 0.0 - 2.0
    max_tokens?: number;         // Max response tokens
  };
  
  // Tool Overrides (optional - defaults to standard tools)
  tools?: {
    file_system?: {
      enabled: boolean;
      base_dir?: string;         // Override base directory
      allowed_extensions?: string[];
    };
    python_interpreter?: {
      enabled: boolean;
      timeout?: number;          // Execution timeout in seconds
    };
    user_input?: {
      enabled: boolean;
      mode: 'blocking' | 'async' | 'disabled';
    };
    prompt_tool?: {
      enabled: boolean;
      templates_dir?: string;    // Custom templates directory
    };
  };
  
  // Paradigm Overrides
  paradigm?: {
    directory?: string;          // Custom paradigm directory
    defaults?: Record<string, string>;  // Default paradigm for sequence types
  };
}
```

### 2. Inference-Agent Mapping

```typescript
interface InferenceAgentMapping {
  // Pattern-based assignment
  patterns: Array<{
    match: 'flow_index' | 'concept_name' | 'sequence_type';
    pattern: string;           // Regex or exact match
    agent_id: string;
  }>;
  
  // Explicit assignments (override patterns)
  explicit: Record<string, string>;  // flow_index → agent_id
  
  // Default agent
  default: string;
}
```

### 3. Tool Call Event

```typescript
interface ToolCallEvent {
  timestamp: string;
  flow_index: string;
  agent_id: string;
  tool_name: string;           // e.g., "llm", "file_system", "python_interpreter"
  method: string;              // e.g., "generate", "read", "execute"
  inputs: Record<string, any>; // Sanitized input summary
  outputs?: any;               // Result (if completed)
  duration_ms?: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}
```

---

## UI Design

### Agent Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NormCode Canvas                                                            │
├──────────┬────────────────────────────────────────────────┬─────────────────┤
│          │                                                │                 │
│  Agent   │            Graph Canvas                        │   Detail        │
│  Panel   │                                                │   Panel         │
│          │                                                │                 │
│ ┌──────┐ │  ┌──────┐     ┌──────┐     ┌──────┐          │ ┌─────────────┐ │
│ │Agent │ │  │Node 1│────→│Node 2│────→│Node 3│          │ │ Node Info   │ │
│ │ List │ │  └──────┘     └──────┘     └──────┘          │ │ Reference   │ │
│ │      │ │                                                │ │ Agent: ...  │ │
│ │ [+]  │ │                                                │ └─────────────┘ │
│ └──────┘ │                                                │                 │
│          │                                                │                 │
│ ┌──────┐ │                                                │                 │
│ │Tool  │ │                                                │                 │
│ │Calls │ │                                                │                 │
│ │Live  │ │                                                │                 │
│ │Feed  │ │                                                │                 │
│ └──────┘ │                                                │                 │
│          │                                                │                 │
├──────────┴────────────────────────────────────────────────┴─────────────────┤
│  [Canvas] [Editor] [Agents]                    Log Panel                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Panel Components

#### 1. Agent List

```
┌─────────────────────────────────┐
│ Agents                    [+ New]│
├─────────────────────────────────┤
│ ◉ default                  [⋮]  │
│   qwen-plus                     │
│   ─────────────────────────     │
│ ○ analyst                  [⋮]  │
│   gpt-4o                        │
│   ─────────────────────────     │
│ ○ coder                    [⋮]  │
│   claude-3-sonnet               │
└─────────────────────────────────┘
```

#### 2. Agent Editor (Modal/Slide-out)

```
┌─────────────────────────────────────────────────────────────┐
│ Edit Agent: analyst                                    [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Name: [analyst                    ]                         │
│ Description: [Analysis agent with GPT-4o    ]               │
│                                                             │
│ ▼ LLM Configuration                                         │
│   Model:       [gpt-4o            ▼]                        │
│   Temperature: [0.7     ] ═════●═══                         │
│   Max Tokens:  [4096    ]                                   │
│                                                             │
│ ▼ Tools                                                     │
│   ☑ File System                                             │
│     Base Dir: [/custom/path       ]                         │
│   ☑ Python Interpreter                                      │
│     Timeout:  [30s               ]                          │
│   ☑ User Input (blocking mode)                              │
│   ☑ Prompt Tool                                             │
│                                                             │
│ ▼ Paradigm                                                  │
│   Directory: [provision/paradigm  ]                         │
│                                                             │
│                          [Cancel] [Save]                    │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Agent Assignment View (in Detail Panel)

When a function node is selected:

```
┌─────────────────────────────────────────────────────────────┐
│ Node: ::(analyze investment opportunity)              [⤢][×]│
├─────────────────────────────────────────────────────────────┤
│ Flow Index: 1.2.1                                           │
│ Status: [pending] [imperative]                              │
│                                                             │
│ ▼ Agent Assignment                                          │
│   Current: [default          ▼]                             │
│            ○ default (qwen-plus)                            │
│            ● analyst (gpt-4o)      ← selected               │
│            ○ coder (claude-3)                               │
│                                                             │
│   Pattern Match: sequence_type=imperative → analyst         │
│   Override: [Use explicit assignment]                       │
│                                                             │
│ ▼ Paradigm                                                  │
│   h_PromptTemplate-c_GenerateJson-o_Normal                  │
│   ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

#### 4. Tool Call Monitor (Live Feed)

```
┌─────────────────────────────────────────────────────────────┐
│ Tool Calls                                      [⏸] [Clear] │
├─────────────────────────────────────────────────────────────┤
│ 10:32:15 │ 1.2.1 │ analyst │ llm.generate           │ ⏳   │
│          │       │         │ prompt: "Analyze..."   │      │
│ ─────────┼───────┼─────────┼────────────────────────┼──────│
│ 10:32:14 │ 1.2.1 │ analyst │ prompt.load            │ ✓    │
│          │       │         │ file: bullish_eval.md  │ 12ms │
│ ─────────┼───────┼─────────┼────────────────────────┼──────│
│ 10:32:13 │ 1.1.1 │ default │ file_system.read       │ ✓    │
│          │       │         │ path: data/input.json  │ 5ms  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase A: Backend Infrastructure

#### A1. Agent Registry Service

**File**: `canvas_app/backend/services/agent_service.py`

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from infra._agent._body import Body

@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    id: str
    name: str
    description: str = ""
    
    # LLM config
    llm_model: str = "qwen-plus"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    
    # Tool config
    file_system_enabled: bool = True
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = True
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = True
    user_input_mode: str = "blocking"  # blocking, async, disabled
    
    # Paradigm config
    paradigm_dir: Optional[str] = None


class AgentRegistry:
    """Registry of agent configurations and Body instances."""
    
    def __init__(self, default_base_dir: str = "."):
        self.default_base_dir = default_base_dir
        self.configs: Dict[str, AgentConfig] = {}
        self.bodies: Dict[str, Body] = {}
        self.tool_callbacks: Dict[str, Callable] = {}
        
        # Create default agent
        self.register(AgentConfig(id="default", name="Default Agent"))
    
    def register(self, config: AgentConfig) -> None:
        """Register an agent configuration."""
        self.configs[config.id] = config
        # Invalidate cached body
        if config.id in self.bodies:
            del self.bodies[config.id]
    
    def get_body(self, agent_id: str) -> Body:
        """Get or create Body instance for agent."""
        if agent_id not in self.bodies:
            config = self.configs.get(agent_id)
            if not config:
                raise ValueError(f"Unknown agent: {agent_id}")
            self.bodies[agent_id] = self._create_body(config)
        return self.bodies[agent_id]
    
    def _create_body(self, config: AgentConfig) -> Body:
        """Create Body instance from config."""
        base_dir = config.file_system_base_dir or self.default_base_dir
        
        # Create body with custom paradigm if specified
        paradigm_tool = None
        if config.paradigm_dir:
            paradigm_tool = self._create_paradigm_tool(config.paradigm_dir, base_dir)
        
        body = Body(
            llm_name=config.llm_model,
            base_dir=base_dir,
            paradigm_tool=paradigm_tool
        )
        
        # Inject monitored tools
        body.llm = self._wrap_tool(config.id, "llm", body.llm)
        body.file_system = self._wrap_tool(config.id, "file_system", body.file_system)
        body.python_interpreter = self._wrap_tool(config.id, "python_interpreter", body.python_interpreter)
        
        return body
    
    def _wrap_tool(self, agent_id: str, tool_name: str, tool: Any) -> Any:
        """Wrap tool to emit monitoring events."""
        # Implementation: proxy that emits tool call events
        return MonitoredToolProxy(agent_id, tool_name, tool, self._emit_tool_event)
    
    def _emit_tool_event(self, event: Dict[str, Any]) -> None:
        """Emit tool call event to registered callbacks."""
        for callback in self.tool_callbacks.values():
            callback(event)
    
    def register_tool_callback(self, callback_id: str, callback: Callable) -> None:
        """Register callback for tool call events."""
        self.tool_callbacks[callback_id] = callback
```

#### A2. Inference-Agent Mapping Service

**File**: `canvas_app/backend/services/agent_mapping_service.py`

```python
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class MappingRule:
    match_type: str  # 'flow_index', 'concept_name', 'sequence_type'
    pattern: str
    agent_id: str
    priority: int = 0

class AgentMappingService:
    """Maps inferences to agents based on rules."""
    
    def __init__(self):
        self.rules: List[MappingRule] = []
        self.explicit: Dict[str, str] = {}  # flow_index → agent_id
        self.default_agent: str = "default"
    
    def add_rule(self, rule: MappingRule) -> None:
        """Add a mapping rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)
    
    def set_explicit(self, flow_index: str, agent_id: str) -> None:
        """Set explicit agent assignment for an inference."""
        self.explicit[flow_index] = agent_id
    
    def clear_explicit(self, flow_index: str) -> None:
        """Remove explicit assignment."""
        self.explicit.pop(flow_index, None)
    
    def get_agent_for_inference(
        self,
        flow_index: str,
        concept_name: Optional[str] = None,
        sequence_type: Optional[str] = None
    ) -> str:
        """Determine which agent should handle an inference."""
        
        # Check explicit assignment first
        if flow_index in self.explicit:
            return self.explicit[flow_index]
        
        # Check rules
        for rule in self.rules:
            if self._matches_rule(rule, flow_index, concept_name, sequence_type):
                return rule.agent_id
        
        return self.default_agent
    
    def _matches_rule(
        self,
        rule: MappingRule,
        flow_index: str,
        concept_name: Optional[str],
        sequence_type: Optional[str]
    ) -> bool:
        """Check if rule matches the inference."""
        value = {
            'flow_index': flow_index,
            'concept_name': concept_name or '',
            'sequence_type': sequence_type or ''
        }.get(rule.match_type, '')
        
        return bool(re.match(rule.pattern, value))
```

#### A3. API Endpoints

**File**: `canvas_app/backend/routers/agent_router.py`

```python
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/agents", tags=["agents"])

class AgentConfigRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    llm_model: str = "qwen-plus"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    file_system_enabled: bool = True
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = True
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = True
    user_input_mode: str = "blocking"
    paradigm_dir: Optional[str] = None

class MappingRuleRequest(BaseModel):
    match_type: str
    pattern: str
    agent_id: str
    priority: int = 0

@router.get("/")
async def list_agents() -> List[dict]:
    """List all registered agents."""
    pass

@router.post("/")
async def create_agent(config: AgentConfigRequest) -> dict:
    """Create or update an agent configuration."""
    pass

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict:
    """Delete an agent configuration."""
    pass

@router.get("/mappings")
async def get_mappings() -> dict:
    """Get current agent mappings."""
    pass

@router.post("/mappings/rules")
async def add_mapping_rule(rule: MappingRuleRequest) -> dict:
    """Add a mapping rule."""
    pass

@router.post("/mappings/explicit/{flow_index}")
async def set_explicit_mapping(flow_index: str, agent_id: str) -> dict:
    """Set explicit agent assignment for an inference."""
    pass

@router.get("/tool-calls")
async def get_tool_calls(limit: int = 100) -> List[dict]:
    """Get recent tool call events."""
    pass
```

#### A4. WebSocket Events

Add new event types for agent/tool monitoring:

```python
# New WebSocket event types
"agent:registered"      # New agent registered
"agent:updated"         # Agent config updated
"agent:deleted"         # Agent deleted
"tool:call_started"     # Tool call started
"tool:call_completed"   # Tool call completed
"tool:call_failed"      # Tool call failed
```

---

### Phase B: Frontend Components

#### B1. Agent Store

**File**: `canvas_app/frontend/src/stores/agentStore.ts`

```typescript
import { create } from 'zustand';

interface AgentConfig {
  id: string;
  name: string;
  description: string;
  llm_model: string;
  llm_temperature: number;
  llm_max_tokens: number;
  file_system_enabled: boolean;
  file_system_base_dir?: string;
  python_interpreter_enabled: boolean;
  python_interpreter_timeout: number;
  user_input_enabled: boolean;
  user_input_mode: 'blocking' | 'async' | 'disabled';
  paradigm_dir?: string;
}

interface MappingRule {
  match_type: 'flow_index' | 'concept_name' | 'sequence_type';
  pattern: string;
  agent_id: string;
  priority: number;
}

interface ToolCallEvent {
  id: string;
  timestamp: string;
  flow_index: string;
  agent_id: string;
  tool_name: string;
  method: string;
  inputs: Record<string, any>;
  outputs?: any;
  duration_ms?: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}

interface AgentState {
  agents: Record<string, AgentConfig>;
  rules: MappingRule[];
  explicitMappings: Record<string, string>;
  defaultAgent: string;
  toolCalls: ToolCallEvent[];
  
  // Actions
  setAgents: (agents: Record<string, AgentConfig>) => void;
  addAgent: (config: AgentConfig) => void;
  updateAgent: (id: string, updates: Partial<AgentConfig>) => void;
  deleteAgent: (id: string) => void;
  
  addRule: (rule: MappingRule) => void;
  removeRule: (index: number) => void;
  setExplicitMapping: (flowIndex: string, agentId: string) => void;
  clearExplicitMapping: (flowIndex: string) => void;
  
  addToolCall: (event: ToolCallEvent) => void;
  clearToolCalls: () => void;
  
  getAgentForInference: (flowIndex: string, conceptName?: string, sequenceType?: string) => string;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: {},
  rules: [],
  explicitMappings: {},
  defaultAgent: 'default',
  toolCalls: [],
  
  // Implementation...
}));
```

#### B2. Agent Panel Component

**File**: `canvas_app/frontend/src/components/panels/AgentPanel.tsx`

```tsx
import React, { useState } from 'react';
import { useAgentStore } from '../../stores/agentStore';
import { Bot, Plus, Settings, Trash2, Activity } from 'lucide-react';

export function AgentPanel() {
  const { agents, toolCalls, addAgent, deleteAgent } = useAgentStore();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  return (
    <div className="h-full flex flex-col bg-slate-50 border-r">
      {/* Agent List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3 border-b flex items-center justify-between">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Bot size={16} /> Agents
          </h3>
          <button 
            onClick={() => setIsEditing(true)}
            className="p-1 hover:bg-slate-200 rounded"
          >
            <Plus size={16} />
          </button>
        </div>
        
        <div className="p-2 space-y-1">
          {Object.values(agents).map(agent => (
            <AgentListItem
              key={agent.id}
              agent={agent}
              isSelected={selectedAgent === agent.id}
              onSelect={() => setSelectedAgent(agent.id)}
              onEdit={() => { setSelectedAgent(agent.id); setIsEditing(true); }}
              onDelete={() => deleteAgent(agent.id)}
            />
          ))}
        </div>
      </div>
      
      {/* Tool Call Monitor */}
      <div className="h-1/2 border-t">
        <div className="p-3 border-b flex items-center justify-between">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Activity size={16} /> Tool Calls
          </h3>
        </div>
        <ToolCallFeed calls={toolCalls} />
      </div>
      
      {/* Agent Editor Modal */}
      {isEditing && (
        <AgentEditorModal
          agentId={selectedAgent}
          onClose={() => setIsEditing(false)}
        />
      )}
    </div>
  );
}
```

#### B3. Tool Call Feed Component

**File**: `canvas_app/frontend/src/components/panels/ToolCallFeed.tsx`

```tsx
import React from 'react';
import { ToolCallEvent } from '../../stores/agentStore';
import { Check, X, Loader2 } from 'lucide-react';

interface ToolCallFeedProps {
  calls: ToolCallEvent[];
}

export function ToolCallFeed({ calls }: ToolCallFeedProps) {
  return (
    <div className="h-full overflow-y-auto text-xs">
      {calls.map(call => (
        <div 
          key={call.id}
          className="p-2 border-b hover:bg-slate-100 flex items-start gap-2"
        >
          {/* Status Icon */}
          <div className="pt-0.5">
            {call.status === 'started' && (
              <Loader2 size={12} className="animate-spin text-blue-500" />
            )}
            {call.status === 'completed' && (
              <Check size={12} className="text-green-500" />
            )}
            {call.status === 'failed' && (
              <X size={12} className="text-red-500" />
            )}
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-slate-500">
                {call.timestamp.split('T')[1]?.slice(0, 8)}
              </span>
              <span className="font-mono text-purple-600">
                {call.flow_index}
              </span>
              <span className="text-slate-600">
                {call.agent_id}
              </span>
            </div>
            <div className="font-mono text-slate-800">
              {call.tool_name}.{call.method}
            </div>
            {call.duration_ms !== undefined && (
              <div className="text-slate-400">
                {call.duration_ms}ms
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### Phase C: Integration

#### C1. Modify Execution Service

Update `execution_service.py` to use AgentRegistry:

```python
class ExecutionController:
    def __init__(self):
        # ... existing code ...
        self.agent_registry = AgentRegistry()
        self.agent_mapping = AgentMappingService()
    
    async def _run_cycle_with_events(self):
        """Execute one cycle with per-inference agent assignment."""
        # Get next inference
        next_inference = self.orchestrator._get_next_ready_inference()
        if not next_inference:
            return None
        
        flow_index = next_inference.flow_info.get('flow_index', '')
        concept_name = next_inference.concept_to_infer.name
        sequence_type = next_inference.get_sequence_type()
        
        # Get appropriate agent
        agent_id = self.agent_mapping.get_agent_for_inference(
            flow_index, concept_name, sequence_type
        )
        body = self.agent_registry.get_body(agent_id)
        
        # Emit agent assignment event
        self._emit("inference:agent_assigned", {
            "flow_index": flow_index,
            "agent_id": agent_id
        })
        
        # Execute with assigned body
        # ... rest of execution logic ...
```

#### C2. Add Agent Panel to App Layout

Update `App.tsx`:

```tsx
// Add agent panel toggle
const [showAgentPanel, setShowAgentPanel] = useState(false);

// Add to header
<button
  onClick={() => setShowAgentPanel(!showAgentPanel)}
  className={`px-3 py-1.5 rounded ${showAgentPanel ? 'bg-purple-500 text-white' : ''}`}
>
  <Bot size={16} />
  Agents
</button>

// Add panel to layout
{showAgentPanel && (
  <div className="w-64 flex-shrink-0">
    <AgentPanel />
  </div>
)}
```

---

## Data Flow

### Agent Configuration Flow

```
┌─────────────┐    POST /api/agents    ┌─────────────┐
│  Frontend   │ ─────────────────────→ │   Backend   │
│ AgentPanel  │                        │ AgentRouter │
└─────────────┘                        └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │AgentRegistry│
                                       │ .register() │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ Body created│
                                       │ with config │
                                       └─────────────┘
```

### Tool Call Monitoring Flow

```
┌───────────────────────────────────────────────────────────────┐
│                     Execution                                  │
├───────────────────────────────────────────────────────────────┤
│  Inference 1.2.1 starts                                       │
│        │                                                       │
│        ▼                                                       │
│  AgentMapping.get_agent("1.2.1") → "analyst"                  │
│        │                                                       │
│        ▼                                                       │
│  AgentRegistry.get_body("analyst") → Body                     │
│        │                                                       │
│        ▼                                                       │
│  Body.llm.generate(prompt)                                    │
│        │                                                       │
│        ├──────────────────────────────────────────────────┐   │
│        │  MonitoredToolProxy                              │   │
│        │  ├── emit("tool:call_started", {...})           │   │
│        │  ├── actual_llm.generate(prompt)                │   │
│        │  └── emit("tool:call_completed", {...})         │   │
│        └──────────────────────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│                   WebSocket                                    │
│                         │                                      │
│                         ▼                                      │
│                   Frontend                                     │
│                   useAgentStore.addToolCall()                 │
│                         │                                      │
│                         ▼                                      │
│                   ToolCallFeed                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Implementation Timeline

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| **A1** | AgentRegistry service | 1 day |
| **A2** | AgentMappingService | 0.5 day |
| **A3** | API endpoints | 0.5 day |
| **A4** | WebSocket events | 0.5 day |
| **B1** | Agent store | 0.5 day |
| **B2** | AgentPanel component | 1 day |
| **B3** | ToolCallFeed component | 0.5 day |
| **C1** | Execution integration | 1 day |
| **C2** | App layout integration | 0.5 day |
| **Testing** | Integration testing | 1 day |

**Total Estimated Time**: 7-8 days

---

## Future Enhancements

### 1. Agent Templates
Pre-configured agent templates for common use cases:
- "Analyst" - GPT-4o for complex analysis
- "Coder" - Claude for code generation
- "Fast" - Qwen-turbo for simple tasks

### 2. Cost Tracking
Track token usage and costs per agent:
```typescript
interface AgentStats {
  agent_id: string;
  total_calls: number;
  total_tokens: number;
  estimated_cost: number;
}
```

### 3. Agent Profiles
Save/load agent configurations as profiles:
- Export to JSON
- Import from file
- Share between projects

### 4. Conditional Tool Enabling
Enable/disable tools per paradigm type:
```yaml
paradigm: h_PromptTemplate-c_GenerateJson-o_Normal
tools:
  llm: required
  python_interpreter: disabled
  file_system: optional
```

### 5. Human-in-the-Loop Panel
Dedicated UI for user input requests (like Streamlit's blocking UI):
- Shows pending input requests
- Form for user response
- History of past interactions

---

## References

- **Agent Sequences Documentation**: `documentation/current/updated/3_execution/agent_sequences.md`
- **Semantic Concepts**: `documentation/current/updated/2_grammar/semantic_concepts.md`
- **Body Implementation**: `infra/_agent/_body.py`
- **Streamlit User Input Tool**: `streamlit_app/tools/user_input_tool.py`
- **Orchestration Runner**: `streamlit_app/orchestration/orchestration_runner.py`

---

**Document Version**: 1.0  
**Author**: AI Assistant  
**Status**: Ready for Review

