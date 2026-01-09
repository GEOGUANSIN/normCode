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
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface AgentDefinition {
  id: string;
  name: string;
  description: string | null;
  llm_model: string | null;
  file_system_enabled: boolean;
  file_system_base_dir: string | null;
  python_interpreter_enabled: boolean;
  python_interpreter_timeout: number;
  user_input_enabled: boolean;
  user_input_mode: string;
  paradigm_dir: string | null;
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
  agent: AgentDefinition;
  isDefault: boolean;
}

function AgentCard({ agent, isDefault }: AgentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className={`border rounded-lg overflow-hidden ${isDefault ? 'border-emerald-300 bg-emerald-50/30' : 'border-slate-200 bg-white'}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-start gap-3 text-left hover:bg-slate-50/50 transition-colors"
      >
        <div className="mt-0.5 text-slate-400">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
        
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
          isDefault ? 'bg-emerald-500' : 'bg-slate-700'
        }`}>
          <Bot size={20} className="text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800">{agent.name}</span>
            {isDefault && (
              <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded text-[10px] font-medium">
                DEFAULT
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <code className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{agent.id}</code>
            {agent.llm_model && (
              <span className="text-xs text-purple-600 flex items-center gap-1">
                <Sparkles size={10} />
                {agent.llm_model}
              </span>
            )}
          </div>
          {agent.description && (
            <p className="text-xs text-slate-500 mt-1 line-clamp-1">{agent.description}</p>
          )}
        </div>
        
        {/* Capability indicators */}
        <div className="flex items-center gap-1 shrink-0">
          {agent.file_system_enabled && (
            <div className="w-6 h-6 rounded bg-blue-100 flex items-center justify-center" title="File System Access">
              <FolderOpen size={12} className="text-blue-600" />
            </div>
          )}
          {agent.python_interpreter_enabled && (
            <div className="w-6 h-6 rounded bg-amber-100 flex items-center justify-center" title="Python Interpreter">
              <Terminal size={12} className="text-amber-600" />
            </div>
          )}
          {agent.user_input_enabled && (
            <div className="w-6 h-6 rounded bg-green-100 flex items-center justify-center" title="User Input">
              <MessageSquare size={12} className="text-green-600" />
            </div>
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3">
          {agent.description && (
            <p className="text-sm text-slate-600">{agent.description}</p>
          )}
          
          {/* Capabilities Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-2 p-2 bg-slate-50 rounded">
              <FolderOpen size={14} className={agent.file_system_enabled ? 'text-blue-600' : 'text-slate-300'} />
              <span className="text-slate-600">File System</span>
              {agent.file_system_enabled ? (
                <Check size={12} className="text-green-500 ml-auto" />
              ) : (
                <XCircle size={12} className="text-slate-300 ml-auto" />
              )}
            </div>
            
            <div className="flex items-center gap-2 p-2 bg-slate-50 rounded">
              <Terminal size={14} className={agent.python_interpreter_enabled ? 'text-amber-600' : 'text-slate-300'} />
              <span className="text-slate-600">Python</span>
              {agent.python_interpreter_enabled ? (
                <Check size={12} className="text-green-500 ml-auto" />
              ) : (
                <XCircle size={12} className="text-slate-300 ml-auto" />
              )}
            </div>
            
            <div className="flex items-center gap-2 p-2 bg-slate-50 rounded">
              <MessageSquare size={14} className={agent.user_input_enabled ? 'text-green-600' : 'text-slate-300'} />
              <span className="text-slate-600">User Input</span>
              {agent.user_input_enabled ? (
                <span className="text-green-600 ml-auto font-medium">{agent.user_input_mode}</span>
              ) : (
                <XCircle size={12} className="text-slate-300 ml-auto" />
              )}
            </div>
            
            {agent.python_interpreter_enabled && (
              <div className="flex items-center gap-2 p-2 bg-slate-50 rounded">
                <Clock size={14} className="text-slate-400" />
                <span className="text-slate-600">Timeout</span>
                <span className="text-slate-700 ml-auto font-medium">{agent.python_interpreter_timeout}s</span>
              </div>
            )}
          </div>
          
          {/* Additional paths */}
          {(agent.file_system_base_dir || agent.paradigm_dir) && (
            <div className="space-y-1 text-xs">
              {agent.file_system_base_dir && (
                <div className="flex items-center gap-2">
                  <FolderOpen size={12} className="text-slate-400" />
                  <span className="text-slate-500">Base Dir:</span>
                  <code className="text-slate-700 truncate">{agent.file_system_base_dir}</code>
                </div>
              )}
              {agent.paradigm_dir && (
                <div className="flex items-center gap-2">
                  <Cpu size={12} className="text-slate-400" />
                  <span className="text-slate-500">Paradigms:</span>
                  <code className="text-slate-700 truncate">{agent.paradigm_dir}</code>
                </div>
              )}
            </div>
          )}
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

export function AgentConfigPreview({ filePath, onClose }: AgentConfigPreviewProps) {
  const [data, setData] = useState<AgentPreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount or path change
  useEffect(() => {
    loadPreview();
  }, [filePath]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAgentPreview(filePath);
      setData(result);
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
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
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
                agent={agent} 
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
    </div>
  );
}

export default AgentConfigPreview;

