import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  Bot, Plus, Settings, Trash2, Activity, Check, X, Loader2,
  ChevronRight, ChevronDown, Save, RotateCcw, Layers, Wrench, Workflow, FileCode
} from 'lucide-react';
import { useAgentStore, AgentConfig, ToolCallEvent } from '../../stores/agentStore';

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = '/api/agents';

async function fetchAgents(): Promise<AgentConfig[]> {
  const res = await fetch(API_BASE);
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

async function saveAgent(config: AgentConfig): Promise<AgentConfig> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to save agent');
  return res.json();
}

async function deleteAgentApi(agentId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/${agentId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete agent');
}


// ============================================================================
// Agent List Item
// ============================================================================

interface AgentListItemProps {
  agent: AgentConfig;
  isSelected: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function AgentListItem({ agent, isSelected, onSelect, onEdit, onDelete }: AgentListItemProps) {
  const isDefault = agent.id === 'default';
  
  return (
    <div 
      className={`
        p-2 rounded cursor-pointer transition-colors
        ${isSelected ? 'bg-purple-100 border border-purple-300' : 'hover:bg-slate-100'}
      `}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isSelected ? 'bg-purple-500' : 'bg-slate-300'}`} />
          <span className="font-medium text-sm">{agent.name}</span>
        </div>
        <div className="flex items-center gap-1">
          <button 
            onClick={(e) => { e.stopPropagation(); onEdit(); }}
            className="p-1 hover:bg-slate-200 rounded"
            title="Edit agent"
          >
            <Settings size={14} className="text-slate-500" />
          </button>
          {!isDefault && (
            <button 
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="p-1 hover:bg-red-100 rounded"
              title="Delete agent"
            >
              <Trash2 size={14} className="text-red-400" />
            </button>
          )}
        </div>
      </div>
      <div className="text-xs text-slate-500 ml-4">{agent.tools?.llm?.model || 'demo'}</div>
    </div>
  );
}

// ============================================================================
// Shared Tool Config Component
// ============================================================================

import { EmbeddedToolConfig } from './ToolConfigCards';

// ============================================================================
// Runtime Capabilities Summary (for AgentEditor)
// ============================================================================

interface AgentCapabilities {
  agent_id: string;
  tools: Array<{ name: string; enabled: boolean; methods: string[]; description: string }>;
  paradigms: Array<{ name: string; is_custom: boolean }>;
  sequences: Array<{ name: string; category: string }>;
  paradigm_dir: string | null;
  agent_frame_model: string;
}

interface RuntimeCapabilitiesSummaryProps {
  agentId: string | null;
}

function RuntimeCapabilitiesSummary({ agentId }: RuntimeCapabilitiesSummaryProps) {
  const [capabilities, setCapabilities] = useState<AgentCapabilities | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  
  useEffect(() => {
    if (!agentId) {
      setCapabilities(null);
      return;
    }
    
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/agents/${agentId}/capabilities`);
        if (res.ok) {
          setCapabilities(await res.json());
        }
      } catch (e) {
        console.error('Failed to load capabilities:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [agentId]);
  
  if (!agentId) return null;
  
  if (loading) {
    return (
      <div className="border rounded-lg p-3 flex items-center justify-center">
        <Loader2 size={16} className="animate-spin text-slate-400" />
      </div>
    );
  }
  
  if (!capabilities) return null;
  
  const enabledTools = capabilities.tools.filter(t => t.enabled);
  const customParadigms = capabilities.paradigms.filter(p => p.is_custom);
  
  return (
    <div className="border rounded-lg overflow-hidden bg-slate-50">
      <div 
        className="px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-slate-100"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Layers size={14} className="text-green-500" />
          <span>Runtime Capabilities</span>
          <span className="text-[10px] text-slate-400 font-normal bg-slate-200 px-1 rounded">read-only</span>
        </div>
        <div className="text-xs text-slate-500">
          {enabledTools.length} tools • {capabilities.sequences?.length || 0} seq
        </div>
      </div>
      
      {expanded && (
        <div className="p-3 border-t bg-white space-y-3 text-xs">
          {/* Tools */}
          <div>
            <div className="font-semibold text-slate-600 mb-1 flex items-center gap-1">
              <Wrench size={10} />
              Tools ({enabledTools.length} enabled)
            </div>
            <div className="flex flex-wrap gap-1">
              {enabledTools.map(tool => (
                <span 
                  key={tool.name}
                  className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded font-mono"
                  title={`${tool.methods.length} methods: ${tool.methods.join(', ')}`}
                >
                  {tool.name}
                </span>
              ))}
            </div>
          </div>
          
          {/* Sequences */}
          <div>
            <div className="font-semibold text-slate-600 mb-1 flex items-center gap-1">
              <Workflow size={10} />
              Sequences ({capabilities.sequences?.length || 0})
              <span className="text-[10px] bg-orange-100 text-orange-700 px-1 rounded font-normal">
                {capabilities.agent_frame_model || 'demo'}
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {capabilities.sequences?.slice(0, 8).map(seq => (
                <span 
                  key={seq.name}
                  className="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded font-mono"
                >
                  {seq.name}
                </span>
              ))}
              {(capabilities.sequences?.length || 0) > 8 && (
                <span className="text-slate-400">+{capabilities.sequences.length - 8} more</span>
              )}
            </div>
          </div>
          
          {/* Paradigms */}
          <div>
            <div className="font-semibold text-slate-600 mb-1 flex items-center gap-1">
              <FileCode size={10} />
              Paradigms ({capabilities.paradigms.length})
              {customParadigms.length > 0 && (
                <span className="text-green-600 bg-green-100 px-1 rounded">
                  {customParadigms.length} custom
                </span>
              )}
              {capabilities.paradigm_dir && (
                <span className="ml-2 font-mono text-indigo-600 text-[10px] bg-indigo-50 px-1 rounded">
                  {capabilities.paradigm_dir}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1 mt-1">
              {capabilities.paradigms.slice(0, 12).map(paradigm => (
                <span 
                  key={paradigm.name}
                  className={`px-1.5 py-0.5 rounded font-mono ${
                    paradigm.is_custom 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-indigo-100 text-indigo-700'
                  }`}
                  title={paradigm.is_custom ? 'Custom paradigm' : 'Built-in paradigm'}
                >
                  {paradigm.name}
                </span>
              ))}
              {capabilities.paradigms.length > 12 && (
                <span className="text-slate-400 px-1">+{capabilities.paradigms.length - 12} more</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Agent Editor Modal
// ============================================================================

interface AgentEditorProps {
  agentId: string | null;  // null = creating new agent
  onClose: () => void;
  onSave: (config: AgentConfig) => void;
}

function AgentEditor({ agentId, onClose, onSave }: AgentEditorProps) {
  const agents = useAgentStore(s => s.agents);
  const existingAgent = agentId ? agents[agentId] : null;
  
  const [config, setConfig] = useState<AgentConfig>(() => existingAgent || {
    id: '',
    name: '',
    description: '',
    tools: {
      llm: { model: 'demo' },
      paradigm: {},
      file_system: { enabled: true },
      python_interpreter: { enabled: true, timeout: 30 },
      user_input: { enabled: true, mode: 'blocking' },
    },
  });
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const isNew = !existingAgent;
  const isDefault = agentId === 'default';
  
  const handleSave = async () => {
    if (!config.id.trim()) {
      setError('Agent ID is required');
      return;
    }
    if (!config.name.trim()) {
      setError('Agent name is required');
      return;
    }
    
    setSaving(true);
    setError(null);
    
    try {
      const saved = await saveAgent(config);
      onSave(saved);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };
  
  // Use portal to render at body level, avoiding z-index stacking context issues
  return createPortal(
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]">
      <div className="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between shrink-0">
          <h3 className="font-semibold flex items-center gap-2">
            <Bot size={18} className="text-purple-500" />
            {isNew ? 'New Agent' : `Edit Agent: ${config.name}`}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded">
            <X size={18} />
          </button>
        </div>
        
        {/* Form - scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {error && (
            <div className="p-2 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
              {error}
            </div>
          )}
          
          {/* Basic Info */}
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">ID</label>
                <input
                  type="text"
                  value={config.id}
                  onChange={(e) => setConfig({ ...config, id: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
                  disabled={!isNew || isDefault}
                  className="w-full px-3 py-2 border rounded text-sm disabled:bg-slate-100"
                  placeholder="e.g., analyst"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded text-sm"
                  placeholder="Display name"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <input
                type="text"
                value={config.description}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="Optional description"
              />
            </div>
          </div>
          
          {/* Divider */}
          <div className="border-t pt-4">
            <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3">
              Tool Configuration
            </div>
            
            {/* Embedded Tool Config */}
            <EmbeddedToolConfig 
              tools={config.tools}
              onChange={(tools) => setConfig({ ...config, tools })}
            />
          </div>
          
          {/* Runtime Capabilities Summary - only for existing agents */}
          {!isNew && agentId && (
            <div className="border-t pt-4">
              <RuntimeCapabilitiesSummary agentId={agentId} />
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t flex justify-end gap-2 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Save
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

// ============================================================================
// Tool Call Detail Modal
// ============================================================================

interface ToolCallDetailModalProps {
  call: ToolCallEvent;
  callId: string;  // Keep ID to fetch latest from store
  onClose: () => void;
}

// Helper to format values nicely - handles strings with newlines specially
function formatValue(value: unknown): string {
  if (typeof value === 'string') {
    // Return string as-is to preserve formatting
    return value;
  }
  return JSON.stringify(value, null, 2);
}

// Component for displaying a single input/output value
function ValueDisplay({ label, value }: { label: string; value: unknown }) {
  const [expanded, setExpanded] = useState(true);
  const formatted = formatValue(value);
  const isLong = formatted.length > 500;
  
  return (
    <div className="border rounded overflow-hidden">
      <div 
        className="flex items-center justify-between px-3 py-2 bg-slate-100 cursor-pointer hover:bg-slate-200"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="font-mono text-sm font-medium text-slate-700">{label}</span>
        <div className="flex items-center gap-2">
          {isLong && (
            <span className="text-xs text-slate-400">{formatted.length} chars</span>
          )}
          {expanded ? (
            <ChevronDown size={14} className="text-slate-400" />
          ) : (
            <ChevronRight size={14} className="text-slate-400" />
          )}
        </div>
      </div>
      {expanded && (
        <pre className="p-3 text-xs font-mono overflow-auto whitespace-pre-wrap max-h-96 bg-white">
          {formatted}
        </pre>
      )}
    </div>
  );
}

function ToolCallDetailModal({ call, callId, onClose }: ToolCallDetailModalProps) {
  // Get the latest call data from the store to ensure we're showing current state
  const toolCalls = useAgentStore(s => s.toolCalls);
  const latestCall = toolCalls.find(c => c.id === callId) || call;
  
  // If call was deleted from store, close modal
  useEffect(() => {
    if (!toolCalls.find(c => c.id === callId)) {
      onClose();
    }
  }, [toolCalls, callId, onClose]);
  
  return createPortal(
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-lg shadow-xl w-[800px] max-w-[90vw] max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between bg-slate-50 shrink-0">
          <div className="flex items-center gap-3">
            {latestCall.status === 'started' && (
              <Loader2 size={18} className="animate-spin text-blue-500" />
            )}
            {latestCall.status === 'completed' && (
              <Check size={18} className="text-green-500" />
            )}
            {latestCall.status === 'failed' && (
              <X size={18} className="text-red-500" />
            )}
            <div>
              <h3 className="font-semibold font-mono text-lg">
                {latestCall.tool_name}.{latestCall.method}
              </h3>
              <div className="text-sm text-slate-500 flex items-center gap-2 flex-wrap">
                <span>{latestCall.timestamp}</span>
                {latestCall.flow_index && (
                  <span className="font-mono text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded">
                    {latestCall.flow_index}
                  </span>
                )}
                <span>• {latestCall.agent_id}</span>
                {latestCall.duration_ms !== undefined && (
                  <span>• {latestCall.duration_ms.toFixed(0)}ms</span>
                )}
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded">
            <X size={20} />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Show message if still in progress */}
          {latestCall.status === 'started' && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="font-semibold text-blue-700 text-sm mb-1 flex items-center gap-2">
                <Loader2 size={16} className="animate-spin" />
                Tool call is still in progress...
              </div>
              <div className="text-blue-600 text-sm">
                This call is currently executing. The outputs will appear here when it completes.
              </div>
            </div>
          )}
          
          {/* Error */}
          {latestCall.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded">
              <div className="font-semibold text-red-700 text-sm mb-1">Error</div>
              <pre className="text-red-600 text-sm font-mono whitespace-pre-wrap">{latestCall.error}</pre>
            </div>
          )}
          
          {/* Inputs - show each key separately */}
          <div>
            <div className="font-semibold text-sm text-slate-700 mb-2 flex items-center gap-2">
              <span>Inputs</span>
              {latestCall.inputs && (
                <span className="text-xs text-slate-400 font-normal">
                  ({Object.keys(latestCall.inputs).length} {Object.keys(latestCall.inputs).length === 1 ? 'key' : 'keys'})
                </span>
              )}
            </div>
            <div className="space-y-2">
              {latestCall.inputs && Object.entries(latestCall.inputs).map(([key, value]) => (
                <ValueDisplay key={key} label={key} value={value} />
              ))}
              {(!latestCall.inputs || Object.keys(latestCall.inputs).length === 0) && (
                <div className="text-slate-400 text-sm italic">No inputs</div>
              )}
            </div>
          </div>
          
          {/* Outputs */}
          {latestCall.outputs !== undefined && latestCall.outputs !== null && (
            <div>
              <div className="font-semibold text-sm text-slate-700 mb-2">Outputs</div>
              <div className="space-y-2">
                {typeof latestCall.outputs === 'object' && !Array.isArray(latestCall.outputs) ? (
                  Object.entries(latestCall.outputs as Record<string, unknown>).map(([key, value]) => (
                    <ValueDisplay key={key} label={key} value={value} />
                  ))
                ) : (
                  <ValueDisplay label="result" value={latestCall.outputs} />
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-3 border-t bg-slate-50 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-slate-200 hover:bg-slate-300 rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

// ============================================================================
// Tool Call Feed
// ============================================================================

interface ToolCallFeedProps {
  calls: ToolCallEvent[];
}

function ToolCallFeed({ calls }: ToolCallFeedProps) {
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  
  if (calls.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
        No tool calls yet
      </div>
    );
  }
  
  // Show most recent first
  const sortedCalls = [...calls].reverse();
  
  return (
    <>
      <div className="h-full overflow-y-auto text-xs">
        {sortedCalls.map(call => {
          const isStarted = call.status === 'started';
          return (
            <div 
              key={call.id}
              className={`p-2 border-b transition-colors ${
                isStarted 
                  ? 'cursor-not-allowed opacity-75' 
                  : 'hover:bg-slate-100 cursor-pointer'
              }`}
              onClick={() => {
                // Prevent opening modal for calls that are still in progress
                if (!isStarted) {
                  setSelectedCallId(call.id);
                }
              }}
              title={isStarted ? 'Tool call is still in progress' : 'Click to view details'}
            >
            <div className="flex items-start gap-2">
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
                <div className="flex items-center gap-1 flex-wrap text-[10px]">
                  <span className="font-mono text-slate-400">
                    {call.timestamp.split('T')[1]?.slice(0, 8) || call.timestamp}
                  </span>
                  {call.flow_index && (
                    <span className="font-mono text-purple-600 bg-purple-50 px-1 rounded">
                      {call.flow_index}
                    </span>
                  )}
                </div>
                <div className="font-mono text-slate-800 truncate">
                  {call.tool_name}.{call.method}
                </div>
                {call.duration_ms !== undefined && call.status !== 'started' && (
                  <div className="text-slate-400 text-[10px]">
                    {call.duration_ms.toFixed(0)}ms
                  </div>
                )}
              </div>
            </div>
          </div>
          );
        })}
      </div>
      
      {/* Detail Modal */}
      {selectedCallId && (() => {
        const selectedCall = calls.find(c => c.id === selectedCallId);
        return selectedCall ? (
          <ToolCallDetailModal
            call={selectedCall}
            callId={selectedCallId}
            onClose={() => setSelectedCallId(null)}
          />
        ) : null;
      })()}
    </>
  );
}

// ============================================================================
// Main Agent Panel
// ============================================================================

export function AgentPanel() {
  const { 
    agents, toolCalls, 
    addAgent, deleteAgent, 
    setSelectedAgentId, selectedAgentId,
    clearToolCalls
  } = useAgentStore();
  
  const [isEditing, setIsEditing] = useState(false);
  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [agentsCollapsed, setAgentsCollapsed] = useState(false);
  const [toolCallsCollapsed, setToolCallsCollapsed] = useState(false);
  
  // Load agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      setLoading(true);
      try {
        const agentList = await fetchAgents();
        const agentMap: Record<string, AgentConfig> = {};
        for (const agent of agentList) {
          agentMap[agent.id] = agent;
        }
        useAgentStore.setState({ agents: agentMap });
      } catch (e) {
        console.error('Failed to load agents:', e);
      } finally {
        setLoading(false);
      }
    };
    loadAgents();
  }, []);
  
  const handleNewAgent = () => {
    setEditingAgentId(null);
    setIsEditing(true);
  };
  
  const handleEditAgent = (agentId: string) => {
    setEditingAgentId(agentId);
    setIsEditing(true);
  };
  
  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm(`Delete agent "${agentId}"?`)) return;
    
    try {
      await deleteAgentApi(agentId);
      deleteAgent(agentId);
    } catch (e) {
      console.error('Failed to delete agent:', e);
    }
  };
  
  const handleSaveAgent = (config: AgentConfig) => {
    addAgent(config);
  };
  
  return (
    <div className="h-full flex flex-col bg-slate-50 border-r w-72">
      {/* Agent List Section - Collapsible */}
      <div className={`overflow-hidden flex flex-col ${agentsCollapsed ? '' : 'shrink-0'} min-h-0`}>
        <div 
          className="p-2 border-b flex items-center justify-between bg-white cursor-pointer hover:bg-slate-50"
          onClick={() => setAgentsCollapsed(!agentsCollapsed)}
        >
          <h3 className="font-semibold text-sm flex items-center gap-2">
            {agentsCollapsed ? (
              <ChevronRight size={14} className="text-slate-400" />
            ) : (
              <ChevronDown size={14} className="text-slate-400" />
            )}
            <Bot size={14} className="text-purple-500" />
            Agents
            <span className="text-xs text-slate-400">({Object.keys(agents).length})</span>
          </h3>
          <button 
            onClick={(e) => { e.stopPropagation(); handleNewAgent(); }}
            className="p-1 hover:bg-purple-100 rounded text-purple-600"
            title="New Agent"
          >
            <Plus size={14} />
          </button>
        </div>
        
        {!agentsCollapsed && (
          <div className="max-h-32 overflow-y-auto p-1.5 space-y-1">
            {loading ? (
              <div className="flex items-center justify-center p-2">
                <Loader2 size={16} className="animate-spin text-slate-400" />
              </div>
            ) : (
              Object.values(agents).map(agent => (
                <AgentListItem
                  key={agent.id}
                  agent={agent}
                  isSelected={selectedAgentId === agent.id}
                  onSelect={() => setSelectedAgentId(agent.id)}
                  onEdit={() => handleEditAgent(agent.id)}
                  onDelete={() => handleDeleteAgent(agent.id)}
                />
              ))
            )}
          </div>
        )}
      </div>
      
      {/* Tool Call Monitor Section - Collapsible */}
      <div className={`border-t overflow-hidden flex flex-col ${toolCallsCollapsed ? '' : 'flex-1'} min-h-0`}>
        <div 
          className="p-2 border-b flex items-center justify-between bg-white cursor-pointer hover:bg-slate-50"
          onClick={() => setToolCallsCollapsed(!toolCallsCollapsed)}
        >
          <h3 className="font-semibold text-sm flex items-center gap-2">
            {toolCallsCollapsed ? (
              <ChevronRight size={14} className="text-slate-400" />
            ) : (
              <ChevronDown size={14} className="text-slate-400" />
            )}
            <Activity size={14} className="text-blue-500" />
            Tool Calls
            {toolCalls.length > 0 && (
              <span className="text-xs text-slate-400">({toolCalls.length})</span>
            )}
          </h3>
          <button 
            onClick={(e) => { e.stopPropagation(); clearToolCalls(); }}
            className="p-1 hover:bg-slate-200 rounded"
            title="Clear history"
          >
            <RotateCcw size={12} className="text-slate-400" />
          </button>
        </div>
        
        {!toolCallsCollapsed && (
          <div className="flex-1 overflow-hidden">
            <ToolCallFeed calls={toolCalls} />
          </div>
        )}
      </div>
      
      {/* Agent Editor Modal */}
      {isEditing && (
        <AgentEditor
          agentId={editingAgentId}
          onClose={() => setIsEditing(false)}
          onSave={handleSaveAgent}
        />
      )}
    </div>
  );
}

