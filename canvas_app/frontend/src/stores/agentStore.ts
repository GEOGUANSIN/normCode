import { create } from 'zustand';

// ============================================================================
// Types
// ============================================================================

// Tool configuration types (tool-centric design)
export interface LLMToolConfig {
  model: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ParadigmToolConfig {
  dir?: string;
}

export interface FileSystemToolConfig {
  enabled: boolean;
  base_dir?: string;
}

export interface PythonInterpreterToolConfig {
  enabled: boolean;
  timeout: number;
}

export interface UserInputToolConfig {
  enabled: boolean;
  mode: 'blocking' | 'async' | 'disabled';
}

// Custom tool config for extensibility
export interface CustomToolConfig {
  type_id: string;
  enabled: boolean;
  settings: Record<string, unknown>;
}

export interface AgentToolsConfig {
  llm: LLMToolConfig;
  paradigm: ParadigmToolConfig;
  file_system: FileSystemToolConfig;
  python_interpreter: PythonInterpreterToolConfig;
  user_input: UserInputToolConfig;
  // Custom/injectable tools
  custom?: Record<string, CustomToolConfig>;
}

export interface AgentConfig {
  id: string;
  name: string;
  description: string;
  tools: AgentToolsConfig;
}

export interface MappingRule {
  match_type: 'flow_index' | 'concept_name' | 'sequence_type';
  pattern: string;
  agent_id: string;
  priority: number;
}

export interface ToolCallEvent {
  id: string;
  timestamp: string;
  flow_index: string;
  agent_id: string;
  tool_name: string;
  method: string;
  inputs: Record<string, unknown>;
  outputs?: unknown;
  duration_ms?: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}

// ============================================================================
// Store State
// ============================================================================

interface AgentState {
  // Agent configurations
  agents: Record<string, AgentConfig>;
  
  // Mapping state
  rules: MappingRule[];
  explicitMappings: Record<string, string>;  // flow_index -> agent_id
  defaultAgent: string;
  
  // Tool call monitoring
  toolCalls: ToolCallEvent[];
  maxToolCalls: number;
  
  // UI state
  selectedAgentId: string | null;
  isEditorOpen: boolean;
  
  // Actions - Agents
  setAgents: (agents: Record<string, AgentConfig>) => void;
  addAgent: (config: AgentConfig) => void;
  updateAgent: (id: string, updates: Partial<AgentConfig>) => void;
  updateAgentTools: (id: string, toolUpdates: Partial<AgentToolsConfig>) => void;
  deleteAgent: (id: string) => void;
  
  // Actions - Mappings
  setRules: (rules: MappingRule[]) => void;
  addRule: (rule: MappingRule) => void;
  removeRule: (index: number) => void;
  clearRules: () => void;
  setExplicitMapping: (flowIndex: string, agentId: string) => void;
  clearExplicitMapping: (flowIndex: string) => void;
  clearAllExplicitMappings: () => void;
  setDefaultAgent: (agentId: string) => void;
  
  // Actions - Tool Calls
  addToolCall: (event: ToolCallEvent) => void;
  updateToolCall: (id: string, updates: Partial<ToolCallEvent>) => void;
  clearToolCalls: () => void;
  
  // Actions - UI
  setSelectedAgentId: (id: string | null) => void;
  setEditorOpen: (open: boolean) => void;
  
  // Utility
  getAgentForInference: (flowIndex: string, conceptName?: string, sequenceType?: string) => string;
  reset: () => void;
}

// ============================================================================
// Default State
// ============================================================================

const defaultAgent: AgentConfig = {
  id: 'default',
  name: 'Default Agent',
  description: 'Default agent using configured LLM',
  tools: {
    llm: { model: 'demo' },
    paradigm: {},
    file_system: { enabled: true },
    python_interpreter: { enabled: true, timeout: 30 },
    user_input: { enabled: true, mode: 'blocking' },
  },
};

// ============================================================================
// Store Implementation
// ============================================================================

export const useAgentStore = create<AgentState>((set, get) => ({
  // Initial state
  agents: { default: defaultAgent },
  rules: [],
  explicitMappings: {},
  defaultAgent: 'default',
  toolCalls: [],
  maxToolCalls: 500,
  selectedAgentId: null,
  isEditorOpen: false,

  // Agent actions
  setAgents: (agents) => set({ agents }),
  
  addAgent: (config) => set((state) => ({
    agents: { ...state.agents, [config.id]: config }
  })),
  
  updateAgent: (id, updates) => set((state) => {
    const existing = state.agents[id];
    if (!existing) return state;
    return {
      agents: {
        ...state.agents,
        [id]: { ...existing, ...updates }
      }
    };
  }),
  
  updateAgentTools: (id, toolUpdates) => set((state) => {
    const existing = state.agents[id];
    if (!existing) return state;
    return {
      agents: {
        ...state.agents,
        [id]: {
          ...existing,
          tools: {
            ...existing.tools,
            ...toolUpdates,
          }
        }
      }
    };
  }),
  
  deleteAgent: (id) => set((state) => {
    if (id === 'default') return state;  // Can't delete default
    const { [id]: _, ...rest } = state.agents;
    
    // Also clean up mappings pointing to this agent
    const cleanedExplicit: Record<string, string> = {};
    for (const [flow, agent] of Object.entries(state.explicitMappings)) {
      if (agent !== id) {
        cleanedExplicit[flow] = agent;
      }
    }
    
    return {
      agents: rest,
      explicitMappings: cleanedExplicit,
      rules: state.rules.filter(r => r.agent_id !== id),
    };
  }),

  // Mapping actions
  setRules: (rules) => set({ rules }),
  
  addRule: (rule) => set((state) => ({
    rules: [...state.rules, rule].sort((a, b) => b.priority - a.priority)
  })),
  
  removeRule: (index) => set((state) => ({
    rules: state.rules.filter((_, i) => i !== index)
  })),
  
  clearRules: () => set({ rules: [] }),
  
  setExplicitMapping: (flowIndex, agentId) => set((state) => ({
    explicitMappings: { ...state.explicitMappings, [flowIndex]: agentId }
  })),
  
  clearExplicitMapping: (flowIndex) => set((state) => {
    const { [flowIndex]: _, ...rest } = state.explicitMappings;
    return { explicitMappings: rest };
  }),
  
  clearAllExplicitMappings: () => set({ explicitMappings: {} }),
  
  setDefaultAgent: (agentId) => set({ defaultAgent: agentId }),

  // Tool call actions
  addToolCall: (event) => set((state) => {
    const newCalls = [...state.toolCalls, event];
    // Trim to max size
    if (newCalls.length > state.maxToolCalls) {
      return { toolCalls: newCalls.slice(-state.maxToolCalls) };
    }
    return { toolCalls: newCalls };
  }),
  
  updateToolCall: (id, updates) => set((state) => ({
    toolCalls: state.toolCalls.map(call => 
      call.id === id ? { ...call, ...updates } : call
    )
  })),
  
  clearToolCalls: () => set({ toolCalls: [] }),

  // UI actions
  setSelectedAgentId: (id) => set({ selectedAgentId: id }),
  setEditorOpen: (open) => set({ isEditorOpen: open }),

  // Utility
  getAgentForInference: (flowIndex, conceptName, sequenceType) => {
    const state = get();
    
    // Check explicit first
    if (state.explicitMappings[flowIndex]) {
      return state.explicitMappings[flowIndex];
    }
    
    // Check rules
    for (const rule of state.rules) {
      let value = '';
      switch (rule.match_type) {
        case 'flow_index':
          value = flowIndex;
          break;
        case 'concept_name':
          value = conceptName || '';
          break;
        case 'sequence_type':
          value = sequenceType || '';
          break;
      }
      
      try {
        if (new RegExp(rule.pattern).test(value)) {
          return rule.agent_id;
        }
      } catch {
        // Invalid regex, skip
      }
    }
    
    return state.defaultAgent;
  },
  
  reset: () => set({
    agents: { default: defaultAgent },
    rules: [],
    explicitMappings: {},
    defaultAgent: 'default',
    toolCalls: [],
    selectedAgentId: null,
    isEditorOpen: false,
  }),
}));

