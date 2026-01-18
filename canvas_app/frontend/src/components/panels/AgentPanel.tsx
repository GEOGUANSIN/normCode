import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  Bot, Plus, Settings, Trash2, Activity, Check, X, Loader2,
  ChevronRight, ChevronDown, Save, RotateCcw,
  Wrench, FileCode, Code, MessageSquare, Cpu, Workflow, Repeat, Zap,
  MessageCircle, LayoutGrid
} from 'lucide-react';
import { useAgentStore, AgentConfig, ToolCallEvent } from '../../stores/agentStore';
import { useLLMStore } from '../../stores/llmStore';
import { LLMSettingsPanel } from './LLMSettingsPanel';

// ============================================================================
// Capabilities Types
// ============================================================================

interface ToolInfo {
  name: string;
  enabled: boolean;
  methods: string[];
  description: string;
}

interface ParadigmInfo {
  name: string;
  description: string;
  vertical_inputs: Record<string, unknown> | string;
  horizontal_inputs: Record<string, unknown> | string;
  is_custom: boolean;
  source: string;
}

interface SequenceInfo {
  name: string;
  description: string;
  category: string;
}

interface AgentCapabilities {
  agent_id: string;
  tools: ToolInfo[];
  paradigms: ParadigmInfo[];
  sequences: SequenceInfo[];
  paradigm_dir: string | null;
  agent_frame_model: string;
}

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

async function fetchAgentCapabilities(agentId: string): Promise<AgentCapabilities> {
  const res = await fetch(`${API_BASE}/${agentId}/capabilities`);
  if (!res.ok) throw new Error('Failed to fetch capabilities');
  return res.json();
}

// ============================================================================
// Agent Capabilities Panel
// ============================================================================

interface CapabilitiesPanelProps {
  agentId: string | null;
}

function CapabilitiesPanel({ agentId }: CapabilitiesPanelProps) {
  const [capabilities, setCapabilities] = useState<AgentCapabilities | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [expandedParadigms, setExpandedParadigms] = useState<Set<string>>(new Set());
  const [showParadigms, setShowParadigms] = useState(false);
  const [showSequences, setShowSequences] = useState(true);  // Default expanded
  
  useEffect(() => {
    if (!agentId) {
      setCapabilities(null);
      return;
    }
    
    const load = async () => {
      setLoading(true);
      try {
        const caps = await fetchAgentCapabilities(agentId);
        setCapabilities(caps);
      } catch (e) {
        console.error('Failed to load capabilities:', e);
        setCapabilities(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [agentId]);
  
  if (!agentId) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm p-4 text-center">
        Select an agent to view its tools and paradigms
      </div>
    );
  }
  
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={20} className="animate-spin text-slate-400" />
      </div>
    );
  }
  
  if (!capabilities) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
        No capabilities data
      </div>
    );
  }
  
  const toggleTool = (name: string) => {
    const next = new Set(expandedTools);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setExpandedTools(next);
  };
  
  const toggleParadigm = (name: string) => {
    const next = new Set(expandedParadigms);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setExpandedParadigms(next);
  };
  
  const getToolIcon = (name: string) => {
    switch (name) {
      case 'llm': return <Cpu size={12} className="text-blue-500" />;
      case 'file_system': return <FileCode size={12} className="text-green-500" />;
      case 'python_interpreter': return <Code size={12} className="text-yellow-600" />;
      case 'user_input': return <MessageSquare size={12} className="text-purple-500" />;
      case 'paradigm_tool': return <Workflow size={12} className="text-indigo-500" />;
      case 'composition_tool': return <Repeat size={12} className="text-pink-500" />;
      case 'prompt_tool': return <FileCode size={12} className="text-teal-500" />;
      case 'formatter_tool': return <Zap size={12} className="text-amber-500" />;
      case 'perception_router': return <Workflow size={12} className="text-cyan-500" />;
      case 'chat': return <MessageCircle size={12} className="text-emerald-500" />;
      case 'canvas': return <LayoutGrid size={12} className="text-rose-500" />;
      default: return <Wrench size={12} className="text-slate-500" />;
    }
  };
  
  const enabledTools = capabilities.tools.filter(t => t.enabled);
  const disabledTools = capabilities.tools.filter(t => !t.enabled);
  
  return (
    <div className="h-full overflow-y-auto text-xs">
      {/* Tools Section */}
      <div className="p-2">
        <div className="font-semibold text-slate-600 mb-2 flex items-center gap-1">
          <Wrench size={12} />
          Tools ({enabledTools.length} enabled)
        </div>
        
        <div className="space-y-1">
          {enabledTools.map(tool => (
            <div key={tool.name} className="border rounded overflow-hidden bg-white">
              <div 
                className="flex items-center gap-2 p-1.5 cursor-pointer hover:bg-slate-50"
                onClick={() => toggleTool(tool.name)}
              >
                {expandedTools.has(tool.name) ? (
                  <ChevronDown size={10} className="text-slate-400" />
                ) : (
                  <ChevronRight size={10} className="text-slate-400" />
                )}
                {getToolIcon(tool.name)}
                <span className="font-mono font-medium">{tool.name}</span>
                <span className="text-slate-400 text-[10px] ml-auto">
                  {tool.methods.length} methods
                </span>
              </div>
              
              {expandedTools.has(tool.name) && (
                <div className="px-2 pb-2 pt-1 bg-slate-50 border-t">
                  <div className="text-slate-500 mb-1">{tool.description}</div>
                  <div className="flex flex-wrap gap-1">
                    {tool.methods.map(method => (
                      <span 
                        key={method}
                        className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded font-mono text-[10px]"
                      >
                        .{method}()
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {disabledTools.length > 0 && (
            <div className="mt-2 pt-2 border-t">
              <div className="text-slate-400 text-[10px] mb-1">Disabled:</div>
              <div className="flex flex-wrap gap-1">
                {disabledTools.map(tool => (
                  <span 
                    key={tool.name}
                    className="px-1.5 py-0.5 bg-slate-100 text-slate-400 rounded font-mono text-[10px] line-through"
                  >
                    {tool.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Sequences Section */}
      <div className="p-2 border-t">
        <div 
          className="font-semibold text-slate-600 mb-2 flex items-center gap-1 cursor-pointer hover:text-orange-600"
          onClick={() => setShowSequences(!showSequences)}
        >
          {showSequences ? (
            <ChevronDown size={12} />
          ) : (
            <ChevronRight size={12} />
          )}
          <Workflow size={12} />
          Sequences ({capabilities.sequences?.length || 0})
          <span className="text-[10px] bg-orange-100 text-orange-700 px-1 rounded font-normal">
            {capabilities.agent_frame_model || 'demo'}
          </span>
        </div>
        
        {showSequences && capabilities.sequences && (
          <div className="space-y-1">
            {/* Group sequences by category */}
            {(() => {
              const byCategory: Record<string, SequenceInfo[]> = {};
              for (const seq of capabilities.sequences) {
                const cat = seq.category || 'other';
                if (!byCategory[cat]) byCategory[cat] = [];
                byCategory[cat].push(seq);
              }
              
              const categoryLabels: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
                'core': { label: 'Core', color: 'bg-slate-100 text-slate-700', icon: <Zap size={10} /> },
                'llm': { label: 'LLM', color: 'bg-blue-100 text-blue-700', icon: <Cpu size={10} /> },
                'python': { label: 'Python', color: 'bg-yellow-100 text-yellow-700', icon: <Code size={10} /> },
                'composition': { label: 'Composition', color: 'bg-purple-100 text-purple-700', icon: <Workflow size={10} /> },
                'input': { label: 'Input', color: 'bg-green-100 text-green-700', icon: <MessageSquare size={10} /> },
              };
              
              const categoryOrder = ['core', 'llm', 'composition', 'python', 'input', 'other'];
              
              return categoryOrder.map(cat => {
                const seqs = byCategory[cat];
                if (!seqs || seqs.length === 0) return null;
                
                const info = categoryLabels[cat] || { label: cat, color: 'bg-slate-100 text-slate-600', icon: <Repeat size={10} /> };
                
                return (
                  <div key={cat} className="mb-2">
                    <div className="flex items-center gap-1 text-[10px] font-semibold text-slate-500 mb-1">
                      {info.icon}
                      {info.label}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {seqs.map(seq => (
                        <span
                          key={seq.name}
                          className={`px-1.5 py-0.5 rounded font-mono text-[10px] cursor-help ${info.color}`}
                          title={seq.description}
                        >
                          {seq.name}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        )}
      </div>
      
      {/* Paradigms Section */}
      <div className="p-2 border-t">
        {(() => {
          const customParadigms = capabilities.paradigms.filter(p => p.is_custom);
          const defaultParadigms = capabilities.paradigms.filter(p => !p.is_custom);
          
          return (
            <>
              <div 
                className="font-semibold text-slate-600 mb-2 flex items-center gap-1 cursor-pointer hover:text-purple-600"
                onClick={() => setShowParadigms(!showParadigms)}
              >
                {showParadigms ? (
                  <ChevronDown size={12} />
                ) : (
                  <ChevronRight size={12} />
                )}
                <FileCode size={12} />
                Paradigms
                {customParadigms.length > 0 && (
                  <span className="text-[10px] bg-green-100 text-green-700 px-1 rounded">
                    {customParadigms.length} custom
                  </span>
                )}
                <span className="text-[10px] text-slate-400">
                  +{defaultParadigms.length} default
                </span>
              </div>
              
              {showParadigms && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {/* Custom Paradigms */}
                  {customParadigms.length > 0 && (
                    <div>
                      <div className="text-[10px] text-green-600 font-semibold mb-1 flex items-center gap-1">
                        ★ Project Paradigms
                        {capabilities.paradigm_dir && (
                          <span className="text-slate-400 font-normal truncate max-w-[150px]" title={capabilities.paradigm_dir}>
                            ({capabilities.paradigm_dir.split('/').pop() || capabilities.paradigm_dir.split('\\').pop()})
                          </span>
                        )}
                      </div>
                      <div className="space-y-1">
                        {customParadigms.map(paradigm => (
                          <div key={paradigm.name} className="border border-green-200 rounded overflow-hidden bg-green-50">
                            <div 
                              className="flex items-start gap-1 p-1.5 cursor-pointer hover:bg-green-100"
                              onClick={() => toggleParadigm(paradigm.name)}
                            >
                              {expandedParadigms.has(paradigm.name) ? (
                                <ChevronDown size={10} className="text-green-500 mt-0.5 shrink-0" />
                              ) : (
                                <ChevronRight size={10} className="text-green-500 mt-0.5 shrink-0" />
                              )}
                              <span className="font-mono text-[10px] break-all leading-tight text-green-800">
                                {paradigm.name}
                              </span>
                            </div>
                            
                            {expandedParadigms.has(paradigm.name) && (
                              <div className="px-2 pb-2 pt-1 bg-white border-t border-green-200 text-[10px]">
                                {paradigm.description && (
                                  <div className="text-slate-600 mb-1">{paradigm.description}</div>
                                )}
                                {paradigm.vertical_inputs && (
                                  <div className="text-purple-700">
                                    <span className="font-semibold">Vertical:</span>{' '}
                                    {typeof paradigm.vertical_inputs === 'string' 
                                      ? paradigm.vertical_inputs 
                                      : Object.keys(paradigm.vertical_inputs).join(', ')}
                                  </div>
                                )}
                                {paradigm.horizontal_inputs && (
                                  <div className="text-blue-700">
                                    <span className="font-semibold">Horizontal:</span>{' '}
                                    {typeof paradigm.horizontal_inputs === 'string'
                                      ? paradigm.horizontal_inputs
                                      : Object.keys(paradigm.horizontal_inputs).join(', ')}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Default Paradigms */}
                  {defaultParadigms.length > 0 && (
                    <div>
                      <div className="text-[10px] text-slate-500 font-semibold mb-1">
                        Default Paradigms ({defaultParadigms.length})
                      </div>
                      <div className="space-y-1">
                        {defaultParadigms.map(paradigm => (
                          <div key={paradigm.name} className="border rounded overflow-hidden bg-white">
                            <div 
                              className="flex items-start gap-1 p-1.5 cursor-pointer hover:bg-slate-50"
                              onClick={() => toggleParadigm(paradigm.name)}
                            >
                              {expandedParadigms.has(paradigm.name) ? (
                                <ChevronDown size={10} className="text-slate-400 mt-0.5 shrink-0" />
                              ) : (
                                <ChevronRight size={10} className="text-slate-400 mt-0.5 shrink-0" />
                              )}
                              <span className="font-mono text-[10px] break-all leading-tight">
                                {paradigm.name}
                              </span>
                            </div>
                            
                            {expandedParadigms.has(paradigm.name) && (
                              <div className="px-2 pb-2 pt-1 bg-slate-50 border-t text-[10px]">
                                {paradigm.description && (
                                  <div className="text-slate-600 mb-1">{paradigm.description}</div>
                                )}
                                {paradigm.vertical_inputs && (
                                  <div className="text-purple-700">
                                    <span className="font-semibold">Vertical:</span>{' '}
                                    {typeof paradigm.vertical_inputs === 'string' 
                                      ? paradigm.vertical_inputs 
                                      : Object.keys(paradigm.vertical_inputs).join(', ')}
                                  </div>
                                )}
                                {paradigm.horizontal_inputs && (
                                  <div className="text-blue-700">
                                    <span className="font-semibold">Horizontal:</span>{' '}
                                    {typeof paradigm.horizontal_inputs === 'string'
                                      ? paradigm.horizontal_inputs
                                      : Object.keys(paradigm.horizontal_inputs).join(', ')}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          );
        })()}
      </div>
    </div>
  );
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
  
  // Get LLM providers from store
  const { providers, fetchProviders } = useLLMStore();
  
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
  const [showLLMSettings, setShowLLMSettings] = useState(false);
  
  const isNew = !existingAgent;
  const isDefault = agentId === 'default';
  
  // Fetch LLM providers on mount
  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);
  
  // Build list of available models from providers
  const availableModels = providers
    .filter(p => p.is_enabled)
    .map(p => ({ id: p.id, name: p.name, model: p.model }));
  
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
      <div className="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-semibold">
            {isNew ? 'New Agent' : `Edit Agent: ${config.name}`}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded">
            <X size={18} />
          </button>
        </div>
        
        {/* Form */}
        <div className="p-4 space-y-4">
          {error && (
            <div className="p-2 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
              {error}
            </div>
          )}
          
          {/* Basic Info */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">ID</label>
              <input
                type="text"
                value={config.id}
                onChange={(e) => setConfig({ ...config, id: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
                disabled={!isNew || isDefault}
                className="w-full px-3 py-2 border rounded text-sm disabled:bg-slate-100"
                placeholder="e.g., analyst, coder"
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
          
          {/* LLM Config */}
          <details className="border rounded" open>
            <summary className="px-3 py-2 bg-slate-50 cursor-pointer font-medium text-sm flex items-center gap-2">
              <ChevronRight size={16} className="details-chevron" />
              LLM Configuration
            </summary>
            <div className="p-3 space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium">Model</label>
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); setShowLLMSettings(true); }}
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                  >
                    <Bot size={12} />
                    Configure
                    <ChevronRight size={12} />
                  </button>
                </div>
                <select
                  value={config.tools.llm.model}
                  onChange={(e) => setConfig({
                    ...config,
                    tools: {
                      ...config.tools,
                      llm: { ...config.tools.llm, model: e.target.value }
                    }
                  })}
                  className="w-full px-3 py-2 border rounded text-sm"
                >
                  {availableModels.length > 0 ? (
                    availableModels.map(m => (
                      <option key={m.id} value={m.name}>
                        {m.name} ({m.model})
                      </option>
                    ))
                  ) : (
                    // Fallback options if no providers configured
                    <>
                      <option value="demo">demo (mock)</option>
                      <option value="qwen-plus">qwen-plus</option>
                      <option value="gpt-4o">gpt-4o</option>
                    </>
                  )}
                </select>
              </div>
            </div>
          </details>

          {/* LLM Settings Panel */}
          <LLMSettingsPanel
            isOpen={showLLMSettings}
            onClose={() => {
              setShowLLMSettings(false);
              fetchProviders();  // Refresh providers after closing
            }}
          />
          
          {/* Tools Config */}
          <details className="border rounded">
            <summary className="px-3 py-2 bg-slate-50 cursor-pointer font-medium text-sm flex items-center gap-2">
              <ChevronRight size={16} className="details-chevron" />
              Tools
            </summary>
            <div className="p-3 space-y-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.tools.file_system.enabled}
                  onChange={(e) => setConfig({
                    ...config,
                    tools: {
                      ...config.tools,
                      file_system: { ...config.tools.file_system, enabled: e.target.checked }
                    }
                  })}
                  className="rounded"
                />
                <span className="text-sm">File System</span>
              </label>
              
              {config.tools.file_system.enabled && (
                <div className="ml-6">
                  <label className="block text-xs text-slate-500 mb-1">Base Directory (optional)</label>
                  <input
                    type="text"
                    value={config.tools.file_system.base_dir || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      tools: {
                        ...config.tools,
                        file_system: { ...config.tools.file_system, base_dir: e.target.value || undefined }
                      }
                    })}
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="Use project default"
                  />
                </div>
              )}
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.tools.python_interpreter.enabled}
                  onChange={(e) => setConfig({
                    ...config,
                    tools: {
                      ...config.tools,
                      python_interpreter: { ...config.tools.python_interpreter, enabled: e.target.checked }
                    }
                  })}
                  className="rounded"
                />
                <span className="text-sm">Python Interpreter</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.tools.user_input.enabled}
                  onChange={(e) => setConfig({
                    ...config,
                    tools: {
                      ...config.tools,
                      user_input: { ...config.tools.user_input, enabled: e.target.checked }
                    }
                  })}
                  className="rounded"
                />
                <span className="text-sm">User Input (Human-in-the-Loop)</span>
              </label>
            </div>
          </details>
          
          {/* Paradigm Config */}
          <details className="border rounded">
            <summary className="px-3 py-2 bg-slate-50 cursor-pointer font-medium text-sm flex items-center gap-2">
              <ChevronRight size={16} className="details-chevron" />
              Paradigm
            </summary>
            <div className="p-3">
              <label className="block text-sm font-medium mb-1">Custom Paradigm Directory</label>
              <input
                type="text"
                value={config.tools.paradigm.dir || ''}
                onChange={(e) => setConfig({
                  ...config,
                  tools: {
                    ...config.tools,
                    paradigm: { ...config.tools.paradigm, dir: e.target.value || undefined }
                  }
                })}
                className="w-full px-3 py-2 border rounded text-sm"
                placeholder="e.g., provision/paradigm"
              />
              <p className="text-xs text-slate-500 mt-1">
                Leave empty to use default paradigms
              </p>
            </div>
          </details>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t flex justify-end gap-2">
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
  const [capabilitiesCollapsed, setCapabilitiesCollapsed] = useState(false);
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
      
      {/* Capabilities Section - Collapsible */}
      <div className={`border-t overflow-hidden flex flex-col ${capabilitiesCollapsed ? '' : 'flex-1'} min-h-0`}>
        <div 
          className="p-2 border-b flex items-center justify-between bg-white cursor-pointer hover:bg-slate-50"
          onClick={() => setCapabilitiesCollapsed(!capabilitiesCollapsed)}
        >
          <h3 className="font-semibold text-sm flex items-center gap-2">
            {capabilitiesCollapsed ? (
              <ChevronRight size={14} className="text-slate-400" />
            ) : (
              <ChevronDown size={14} className="text-slate-400" />
            )}
            <Wrench size={14} className="text-green-500" />
            Capabilities
            {selectedAgentId && (
              <span className="text-xs text-slate-400 font-normal">
                ({selectedAgentId})
              </span>
            )}
          </h3>
        </div>
        
        {!capabilitiesCollapsed && (
          <div className="flex-1 overflow-hidden">
            <CapabilitiesPanel agentId={selectedAgentId} />
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

