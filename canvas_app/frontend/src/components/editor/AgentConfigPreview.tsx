/**
 * AgentConfigPreview - A clean viewer for .agent.json configuration files.
 * 
 * Displays agent definitions, routing mappings, and LLM provider configurations
 * in an organized, easy-to-read format.
 */

import { useState, useEffect } from 'react';
import { 
  Bot,
  Users,
  GitBranch,
  Cpu,
  RefreshCw,
  X,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  FolderOpen,
  Terminal,
  MessageSquare,
  Clock,
  Sparkles,
  Shield,
  Hash,
  Zap,
  Settings,
  Check,
  XCircle,
  Code,
  FileText,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

// Tool configuration types for tool-centric agent design
interface LLMToolConfigDef {
  model: string;
  temperature?: number;
  max_tokens?: number;
}

interface ParadigmToolConfigDef {
  dir?: string;
}

interface FileSystemToolConfigDef {
  enabled: boolean;
  base_dir?: string;
}

interface PythonInterpreterToolConfigDef {
  enabled: boolean;
  timeout: number;
}

interface UserInputToolConfigDef {
  enabled: boolean;
  mode: string;
}

interface AgentToolsConfigDef {
  llm: LLMToolConfigDef;
  paradigm: ParadigmToolConfigDef;
  file_system: FileSystemToolConfigDef;
  python_interpreter: PythonInterpreterToolConfigDef;
  user_input: UserInputToolConfigDef;
}

interface AgentDefinition {
  id: string;
  name: string;
  description: string | null;
  // New tool-centric format (from API)
  tools?: AgentToolsConfigDef | null;
  // Legacy fields for backward compatibility (reading old config files)
  llm_model?: string | null;
  file_system_enabled?: boolean;
  file_system_base_dir?: string | null;
  python_interpreter_enabled?: boolean;
  python_interpreter_timeout?: number;
  user_input_enabled?: boolean;
  user_input_mode?: string;
  paradigm_dir?: string | null;
}

// Normalized agent with guaranteed tools structure
interface NormalizedAgent {
  id: string;
  name: string;
  description: string | null;
  tools: AgentToolsConfigDef;
}

// Helper to normalize agent (support both new and legacy format from API)
function normalizeAgent(agent: AgentDefinition): NormalizedAgent {
  if (agent.tools) {
    // New format from API - ensure all nested objects exist with defaults
    return {
      id: agent.id,
      name: agent.name,
      description: agent.description,
      tools: {
        llm: {
          model: agent.tools.llm?.model || 'demo',
          temperature: agent.tools.llm?.temperature,
          max_tokens: agent.tools.llm?.max_tokens,
        },
        paradigm: {
          dir: agent.tools.paradigm?.dir,
        },
        file_system: {
          enabled: agent.tools.file_system?.enabled ?? true,
          base_dir: agent.tools.file_system?.base_dir,
        },
        python_interpreter: {
          enabled: agent.tools.python_interpreter?.enabled ?? true,
          timeout: agent.tools.python_interpreter?.timeout ?? 30,
        },
        user_input: {
          enabled: agent.tools.user_input?.enabled ?? true,
          mode: agent.tools.user_input?.mode || 'blocking',
        },
      },
    };
  }
  // Convert legacy format to tool-centric
  return {
    id: agent.id,
    name: agent.name,
    description: agent.description,
    tools: {
      llm: { model: agent.llm_model || 'demo' },
      paradigm: { dir: agent.paradigm_dir || undefined },
      file_system: { enabled: agent.file_system_enabled ?? true, base_dir: agent.file_system_base_dir || undefined },
      python_interpreter: { enabled: agent.python_interpreter_enabled ?? true, timeout: agent.python_interpreter_timeout ?? 30 },
      user_input: { enabled: agent.user_input_enabled ?? true, mode: agent.user_input_mode || 'blocking' },
    },
  };
}

interface AgentMapping {
  match_type: string;
  pattern: string;
  agent_id: string;
  priority: number;
}

interface LLMProvider {
  provider_name: string;
  provider_type: string;
  model: string;
  api_key: string | null;
}

interface AgentConfigData {
  description: string | null;
  default_agent: string | null;
  agents: AgentDefinition[];
  mappings: AgentMapping[];
  llm_providers: LLMProvider[];
  created_at: string | null;
  updated_at: string | null;
}

interface AgentPreviewData {
  success: boolean;
  file_path: string;
  config: AgentConfigData | null;
  error?: string;
}

interface AgentConfigPreviewProps {
  filePath: string;
  onClose?: () => void;
}

// =============================================================================
// API
// =============================================================================

async function fetchAgentPreview(filePath: string): Promise<AgentPreviewData> {
  const response = await fetch('/api/repositories/preview-agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to load preview' }));
    throw new Error(error.detail || 'Failed to load preview');
  }
  
  return response.json();
}

async function fetchRawFile(filePath: string): Promise<string> {
  const response = await fetch(`/api/editor/file?path=${encodeURIComponent(filePath)}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to load file' }));
    throw new Error(error.detail || 'Failed to load file');
  }
  
  const data = await response.json();
  return data.content || '';
}

// =============================================================================
// Section Components
// =============================================================================

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  badge?: string | number;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

function Section({ title, icon, badge, children, defaultExpanded = true }: SectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center gap-3 hover:bg-slate-50 transition-colors"
      >
        <div className="text-slate-400">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
        <div className="flex items-center gap-2 text-slate-600">
          {icon}
          <span className="font-semibold">{title}</span>
        </div>
        {badge !== undefined && (
          <span className="ml-auto px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-xs font-medium">
            {badge}
          </span>
        )}
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-slate-100">
          {children}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Agent Card Component
// =============================================================================

interface AgentCardProps {
  agent: NormalizedAgent;
  isDefault: boolean;
}

function AgentCard({ agent, isDefault }: AgentCardProps) {
  // Default agent starts expanded
  const [isExpanded, setIsExpanded] = useState(isDefault);
  
  const { tools } = agent;
  
  // Count enabled tools
  const enabledToolsCount = [
    tools.file_system.enabled,
    tools.python_interpreter.enabled,
    tools.user_input.enabled,
  ].filter(Boolean).length;
  
  return (
    <div className={`border rounded-lg overflow-hidden ${isDefault ? 'border-emerald-300 bg-emerald-50/30' : 'border-slate-200 bg-white'}`}>
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-start gap-3 text-left hover:bg-slate-50/50 transition-colors"
      >
        <div className="mt-1 text-slate-400">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
        
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
          isDefault ? 'bg-gradient-to-br from-emerald-500 to-teal-600' : 'bg-gradient-to-br from-slate-600 to-slate-800'
        }`}>
          <Bot size={24} className="text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-slate-800 text-lg">{agent.name}</span>
            {isDefault && (
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-[10px] font-bold uppercase tracking-wide">
                Default
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <code className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-mono">{agent.id}</code>
            
            {/* LLM Model Badge */}
            <div className="flex items-center gap-1 px-2 py-0.5 bg-purple-100 rounded-full">
              <Sparkles size={10} className="text-purple-600" />
              <span className="text-xs text-purple-700 font-medium">{tools.llm.model || 'demo'}</span>
            </div>
            
            {/* Tools Count */}
            <span className="text-xs text-slate-400">
              {enabledToolsCount} tool{enabledToolsCount !== 1 ? 's' : ''} enabled
            </span>
          </div>
          {agent.description && (
            <p className="text-sm text-slate-500 mt-2">{agent.description}</p>
          )}
        </div>
        
        {/* Quick capability icons */}
        <div className="flex items-center gap-1.5 shrink-0">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${tools.file_system.enabled ? 'bg-blue-100' : 'bg-slate-100'}`} title="File System">
            <FolderOpen size={14} className={tools.file_system.enabled ? 'text-blue-600' : 'text-slate-300'} />
          </div>
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${tools.python_interpreter.enabled ? 'bg-amber-100' : 'bg-slate-100'}`} title="Python">
            <Terminal size={14} className={tools.python_interpreter.enabled ? 'text-amber-600' : 'text-slate-300'} />
          </div>
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${tools.user_input.enabled ? 'bg-green-100' : 'bg-slate-100'}`} title="User Input">
            <MessageSquare size={14} className={tools.user_input.enabled ? 'text-green-600' : 'text-slate-300'} />
          </div>
        </div>
      </button>
      
      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-slate-100 space-y-4">
          {/* LLM Configuration Card */}
          <div className="mt-3 p-3 bg-gradient-to-r from-purple-50 to-violet-50 rounded-lg border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={14} className="text-purple-600" />
              <span className="text-sm font-semibold text-purple-800">Language Model</span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-purple-400 block mb-0.5">Model</span>
                <span className="text-purple-800 font-mono font-medium">{tools.llm.model || 'demo'}</span>
              </div>
              <div>
                <span className="text-purple-400 block mb-0.5">Temperature</span>
                <span className="text-purple-800 font-medium">{tools.llm.temperature ?? 'default'}</span>
              </div>
              <div>
                <span className="text-purple-400 block mb-0.5">Max Tokens</span>
                <span className="text-purple-800 font-medium">{tools.llm.max_tokens ?? 'default'}</span>
              </div>
            </div>
          </div>
          
          {/* Paradigm Configuration */}
          {tools.paradigm.dir && (
            <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-100">
              <div className="flex items-center gap-2">
                <Cpu size={14} className="text-indigo-600" />
                <span className="text-sm font-semibold text-indigo-800">Custom Paradigms</span>
              </div>
              <code className="text-xs text-indigo-700 font-mono mt-1 block">{tools.paradigm.dir}</code>
            </div>
          )}
          
          {/* Tools Grid */}
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Tools & Capabilities</div>
            <div className="grid grid-cols-3 gap-2">
              {/* File System */}
              <div className={`p-3 rounded-lg border ${tools.file_system.enabled ? 'bg-blue-50 border-blue-200' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <FolderOpen size={14} className={tools.file_system.enabled ? 'text-blue-600' : 'text-slate-400'} />
                  <span className={`text-sm font-medium ${tools.file_system.enabled ? 'text-blue-800' : 'text-slate-500'}`}>File System</span>
                </div>
                {tools.file_system.enabled ? (
                  <div className="flex items-center gap-1">
                    <Check size={10} className="text-green-500" />
                    <span className="text-[10px] text-green-600">Enabled</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <XCircle size={10} className="text-slate-400" />
                    <span className="text-[10px] text-slate-400">Disabled</span>
                  </div>
                )}
                {tools.file_system.enabled && tools.file_system.base_dir && (
                  <div className="mt-1 text-[10px] text-blue-600 font-mono truncate" title={tools.file_system.base_dir}>
                    {tools.file_system.base_dir}
                  </div>
                )}
              </div>
              
              {/* Python Interpreter */}
              <div className={`p-3 rounded-lg border ${tools.python_interpreter.enabled ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <Terminal size={14} className={tools.python_interpreter.enabled ? 'text-amber-600' : 'text-slate-400'} />
                  <span className={`text-sm font-medium ${tools.python_interpreter.enabled ? 'text-amber-800' : 'text-slate-500'}`}>Python</span>
                </div>
                {tools.python_interpreter.enabled ? (
                  <>
                    <div className="flex items-center gap-1">
                      <Check size={10} className="text-green-500" />
                      <span className="text-[10px] text-green-600">Enabled</span>
                    </div>
                    <div className="mt-1 flex items-center gap-1">
                      <Clock size={10} className="text-amber-500" />
                      <span className="text-[10px] text-amber-600">{tools.python_interpreter.timeout}s timeout</span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-1">
                    <XCircle size={10} className="text-slate-400" />
                    <span className="text-[10px] text-slate-400">Disabled</span>
                  </div>
                )}
              </div>
              
              {/* User Input */}
              <div className={`p-3 rounded-lg border ${tools.user_input.enabled ? 'bg-green-50 border-green-200' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <MessageSquare size={14} className={tools.user_input.enabled ? 'text-green-600' : 'text-slate-400'} />
                  <span className={`text-sm font-medium ${tools.user_input.enabled ? 'text-green-800' : 'text-slate-500'}`}>User Input</span>
                </div>
                {tools.user_input.enabled ? (
                  <>
                    <div className="flex items-center gap-1">
                      <Check size={10} className="text-green-500" />
                      <span className="text-[10px] text-green-600">Enabled</span>
                    </div>
                    <div className="mt-1">
                      <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                        {tools.user_input.mode}
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-1">
                    <XCircle size={10} className="text-slate-400" />
                    <span className="text-[10px] text-slate-400">Disabled</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Mapping Row Component
// =============================================================================

interface MappingRowProps {
  mapping: AgentMapping;
  agents: AgentDefinition[];
}

function MappingRow({ mapping, agents }: MappingRowProps) {
  const targetAgent = agents.find(a => a.id === mapping.agent_id);
  
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
      <div className="w-8 h-8 rounded bg-slate-200 flex items-center justify-center shrink-0">
        <Hash size={14} className="text-slate-600" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{mapping.match_type}:</span>
          <code className="text-sm font-mono text-slate-800 bg-white px-2 py-0.5 rounded border">
            {mapping.pattern}
          </code>
        </div>
      </div>
      
      <div className="text-slate-400">→</div>
      
      <div className="flex items-center gap-2 shrink-0">
        <div className="w-6 h-6 rounded bg-slate-700 flex items-center justify-center">
          <Bot size={12} className="text-white" />
        </div>
        <span className="text-sm font-medium text-slate-700">
          {targetAgent?.name || mapping.agent_id}
        </span>
      </div>
      
      <div className="text-xs text-slate-400 shrink-0">
        priority: {mapping.priority}
      </div>
    </div>
  );
}

// =============================================================================
// Provider Card Component
// =============================================================================

interface ProviderCardProps {
  provider: LLMProvider;
}

function ProviderCard({ provider }: ProviderCardProps) {
  const hasApiKey = provider.api_key && provider.api_key.length > 0;
  const isEnvVar = provider.api_key?.startsWith('${');
  
  return (
    <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-purple-50 to-violet-50 rounded-lg border border-purple-100">
      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center shrink-0">
        <Sparkles size={18} className="text-white" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-800">{provider.provider_name}</span>
          <span className="text-xs text-purple-600 bg-purple-100 px-1.5 py-0.5 rounded">
            {provider.provider_type}
          </span>
        </div>
        <div className="text-xs text-slate-500 mt-0.5">
          Model: <code className="text-purple-700">{provider.model}</code>
        </div>
      </div>
      
      <div className="flex items-center gap-2 shrink-0">
        {hasApiKey ? (
          isEnvVar ? (
            <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              <Shield size={12} />
              <span>ENV: {provider.api_key?.slice(2, -1)}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
              <Check size={12} />
              <span>API Key Set</span>
            </div>
          )
        ) : (
          <div className="flex items-center gap-1 text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded">
            <XCircle size={12} />
            <span>No API Key</span>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Main AgentConfigPreview Component
// =============================================================================

type ViewMode = 'formatted' | 'raw';

export function AgentConfigPreview({ filePath, onClose }: AgentConfigPreviewProps) {
  const [data, setData] = useState<AgentPreviewData | null>(null);
  const [rawJson, setRawJson] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('formatted');

  // Load data on mount or path change
  useEffect(() => {
    loadPreview();
  }, [filePath]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const [result, rawContent] = await Promise.all([
        fetchAgentPreview(filePath),
        fetchRawFile(filePath),
      ]);
      setData(result);
      setRawJson(rawContent);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load preview');
    } finally {
      setLoading(false);
    }
  };

  // Format date string
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="flex items-center gap-3 text-slate-500">
          <RefreshCw size={20} className="animate-spin" />
          <span>Loading agent config...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle size={32} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-slate-700 mb-2">Failed to Load</h3>
          <p className="text-slate-500 mb-4">{error}</p>
          <button
            onClick={loadPreview}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.config) return null;

  const config = data.config;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-purple-50 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Users size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">Agent Configuration</h2>
              {config.description && (
                <p className="text-sm text-slate-500 mt-1 max-w-xl">{config.description}</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('formatted')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'formatted'
                    ? 'bg-white text-slate-800 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
                title="Formatted View"
              >
                <FileText size={14} />
                <span>Formatted</span>
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'raw'
                    ? 'bg-white text-slate-800 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
                title="Raw JSON View"
              >
                <Code size={14} />
                <span>JSON</span>
              </button>
            </div>
            
            <div className="w-px h-6 bg-slate-200" />
            
            <button
              onClick={loadPreview}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw size={18} />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                title="Close"
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
        
        {/* Quick info badges */}
        <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Bot size={12} />
            <span>{config.agents.length} agent{config.agents.length !== 1 ? 's' : ''}</span>
          </div>
          {config.default_agent && (
            <div className="flex items-center gap-1.5">
              <Zap size={12} />
              <span>Default: <code className="text-emerald-600">{config.default_agent}</code></span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <GitBranch size={12} />
            <span>{config.mappings.length} mapping{config.mappings.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles size={12} />
            <span>{config.llm_providers.length} provider{config.llm_providers.length !== 1 ? 's' : ''}</span>
          </div>
          {config.updated_at && (
            <div className="flex items-center gap-1.5 ml-auto">
              <Clock size={12} />
              <span>Updated {formatDate(config.updated_at)}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {viewMode === 'raw' ? (
          /* Raw JSON View */
          <div className="h-full p-4">
            <div className="h-full bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                <div className="flex items-center gap-2">
                  <Code size={14} className="text-slate-400" />
                  <span className="text-sm font-medium text-slate-300">Raw JSON</span>
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(rawJson);
                  }}
                  className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded hover:bg-slate-700 transition-colors"
                >
                  Copy
                </button>
              </div>
              <pre className="p-4 text-sm font-mono text-slate-100 overflow-auto h-[calc(100%-40px)] leading-relaxed">
                <code>{rawJson || 'Loading...'}</code>
              </pre>
            </div>
          </div>
        ) : (
          /* Formatted View */
          <div className="p-6 space-y-4">
            {/* Agents Section */}
            <Section 
              title="Agents" 
              icon={<Bot size={18} />}
              badge={config.agents.length}
            >
              <div className="pt-3 space-y-3">
                {config.agents.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={normalizeAgent(agent)} 
                    isDefault={agent.id === config.default_agent}
                  />
                ))}
              </div>
            </Section>
            
            {/* Mappings Section */}
            {config.mappings.length > 0 && (
              <Section 
                title="Agent Mappings" 
                icon={<GitBranch size={18} />}
                badge={config.mappings.length}
              >
                <div className="pt-3 space-y-2">
                  {config.mappings.map((mapping, idx) => (
                    <MappingRow key={idx} mapping={mapping} agents={config.agents} />
                  ))}
                </div>
              </Section>
            )}
            
            {/* LLM Providers Section */}
            {config.llm_providers.length > 0 && (
              <Section 
                title="LLM Providers" 
                icon={<Sparkles size={18} />}
                badge={config.llm_providers.length}
              >
                <div className="pt-3 space-y-2">
                  {config.llm_providers.map((provider, idx) => (
                    <ProviderCard key={idx} provider={provider} />
                  ))}
                </div>
              </Section>
            )}
            
            {/* Metadata Section */}
            <Section 
              title="Metadata" 
              icon={<Settings size={18} />}
              defaultExpanded={false}
            >
              <div className="pt-3 space-y-2 text-sm">
                {config.created_at && (
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="text-slate-400" />
                    <span className="text-slate-500">Created:</span>
                    <span className="text-slate-700">{formatDate(config.created_at)}</span>
                  </div>
                )}
                {config.updated_at && (
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="text-slate-400" />
                    <span className="text-slate-500">Updated:</span>
                    <span className="text-slate-700">{formatDate(config.updated_at)}</span>
                  </div>
                )}
              </div>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentConfigPreview;

