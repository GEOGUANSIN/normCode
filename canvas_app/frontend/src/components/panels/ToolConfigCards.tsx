/**
 * Shared Tool Configuration Cards
 * 
 * Reusable tool configuration UI components used by both:
 * - AgentEditor (modal)
 * - ToolConfigSection (sidebar)
 */

import { useState, useEffect } from 'react';
import { 
  Cpu, FileCode, Code, MessageSquare, Workflow,
  ChevronRight, ChevronDown, Settings, Plus, Trash2, Wrench
} from 'lucide-react';
import { 
  AgentToolsConfig, 
  CustomToolConfig,
} from '../../stores/agentStore';
import { useLLMStore } from '../../stores/llmStore';
import { LLMSettingsPanel } from './LLMSettingsPanel';

// ============================================================================
// Embedded Tool Config - Shared UI for tool configuration
// ============================================================================

interface EmbeddedToolConfigProps {
  tools: AgentToolsConfig;
  onChange: (tools: AgentToolsConfig) => void;
  compact?: boolean;  // For sidebar vs modal sizing
}

export function EmbeddedToolConfig({ tools, onChange, compact = false }: EmbeddedToolConfigProps) {
  const { providers, fetchProviders } = useLLMStore();
  const [showLLMSettings, setShowLLMSettings] = useState(false);
  const [expandedTool, setExpandedTool] = useState<string | null>(compact ? null : 'llm');
  
  useEffect(() => {
    if (!compact) {
      fetchProviders();
    }
  }, [fetchProviders, compact]);
  
  const availableModels = providers
    .filter(p => p.is_enabled)
    .map(p => ({ id: p.id, name: p.name, model: p.model }));
  
  const updateTool = <K extends keyof AgentToolsConfig>(key: K, value: AgentToolsConfig[K]) => {
    onChange({ ...tools, [key]: value });
  };
  
  const py = compact ? 'py-1.5' : 'py-2';
  
  return (
    <div className="space-y-2">
      {/* LLM - Compact mode just shows model name, full mode has dropdown */}
      {compact ? (
        // Compact: Simple display only
        <div className="border rounded-lg overflow-hidden bg-blue-50/50 border-blue-200">
          <div className="flex items-center gap-2 px-3 py-1.5">
            <Cpu size={14} className="text-blue-500" />
            <span className="font-medium text-sm">LLM</span>
            <span className="text-xs text-blue-700 font-mono ml-auto truncate max-w-[120px]">
              {tools.llm.model}
            </span>
          </div>
        </div>
      ) : (
        // Full: Expandable with dropdown and settings
        <div className="border rounded-lg overflow-hidden bg-blue-50/50 border-blue-200">
          <div 
            className={`flex items-center gap-2 px-3 ${py} cursor-pointer hover:bg-white/50`}
            onClick={() => setExpandedTool(expandedTool === 'llm' ? null : 'llm')}
          >
            {expandedTool === 'llm' ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
            <Cpu size={14} className="text-blue-500" />
            <span className="font-medium text-sm flex-1">LLM</span>
            <span className="text-xs text-slate-500 font-mono truncate max-w-[80px]">{tools.llm.model}</span>
          </div>
          {expandedTool === 'llm' && (
            <div className="px-3 pb-3 pt-1 border-t bg-white/80 space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-500">Model</label>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setShowLLMSettings(true); }}
                  className="flex items-center gap-1 text-[10px] text-blue-600 hover:text-blue-700"
                >
                  <Settings size={10} />
                  Manage Providers
                </button>
              </div>
              <select
                value={tools.llm.model}
                onChange={(e) => updateTool('llm', { ...tools.llm, model: e.target.value })}
                className="w-full px-2 py-1.5 border rounded text-sm"
              >
                {availableModels.length > 0 ? (
                  availableModels.map(m => (
                    <option key={m.id} value={m.name}>{m.name} ({m.model})</option>
                  ))
                ) : (
                  <>
                    <option value="demo">demo (mock)</option>
                    <option value="qwen-plus">qwen-plus</option>
                  </>
                )}
              </select>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Temperature</label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={tools.llm.temperature ?? 0}
                    onChange={(e) => updateTool('llm', { ...tools.llm, temperature: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">Max Tokens</label>
                  <input
                    type="number"
                    min="1"
                    value={tools.llm.max_tokens ?? ''}
                    onChange={(e) => updateTool('llm', { ...tools.llm, max_tokens: e.target.value ? parseInt(e.target.value) : undefined })}
                    placeholder="Default"
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* File System */}
      <div className={`border rounded-lg overflow-hidden ${tools.file_system.enabled ? 'bg-green-50/50 border-green-200' : 'bg-slate-50 border-slate-200 opacity-60'}`}>
        <div className={`flex items-center gap-2 px-3 ${py}`}>
          <div className="cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'file_system' ? null : 'file_system')}>
            {expandedTool === 'file_system' ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
          </div>
          <FileCode size={14} className="text-green-500" />
          <span className="font-medium text-sm flex-1 cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'file_system' ? null : 'file_system')}>File System</span>
          <label className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={tools.file_system.enabled}
              onChange={(e) => updateTool('file_system', { ...tools.file_system, enabled: e.target.checked })}
              className="rounded text-green-500"
            />
            <span className="text-xs text-slate-500">{tools.file_system.enabled ? 'On' : 'Off'}</span>
          </label>
        </div>
        {expandedTool === 'file_system' && tools.file_system.enabled && (
          <div className="px-3 pb-3 pt-1 border-t bg-white/80">
            <label className="text-xs text-slate-500 block mb-1">Base Directory</label>
            <input
              type="text"
              value={tools.file_system.base_dir || ''}
              onChange={(e) => updateTool('file_system', { ...tools.file_system, base_dir: e.target.value || undefined })}
              placeholder="Use project root"
              className="w-full px-2 py-1 border rounded text-sm"
            />
          </div>
        )}
      </div>
      
      {/* Python Interpreter */}
      <div className={`border rounded-lg overflow-hidden ${tools.python_interpreter.enabled ? 'bg-yellow-50/50 border-yellow-200' : 'bg-slate-50 border-slate-200 opacity-60'}`}>
        <div className={`flex items-center gap-2 px-3 ${py}`}>
          <div className="cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'python' ? null : 'python')}>
            {expandedTool === 'python' ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
          </div>
          <Code size={14} className="text-yellow-600" />
          <span className="font-medium text-sm flex-1 cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'python' ? null : 'python')}>Python</span>
          <label className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={tools.python_interpreter.enabled}
              onChange={(e) => updateTool('python_interpreter', { ...tools.python_interpreter, enabled: e.target.checked })}
              className="rounded text-yellow-500"
            />
            <span className="text-xs text-slate-500">{tools.python_interpreter.enabled ? 'On' : 'Off'}</span>
          </label>
        </div>
        {expandedTool === 'python' && tools.python_interpreter.enabled && (
          <div className="px-3 pb-3 pt-1 border-t bg-white/80">
            <label className="text-xs text-slate-500 block mb-1">Timeout (sec)</label>
            <input
              type="number"
              min="1"
              max="300"
              value={tools.python_interpreter.timeout}
              onChange={(e) => updateTool('python_interpreter', { ...tools.python_interpreter, timeout: parseInt(e.target.value) || 30 })}
              className="w-full px-2 py-1 border rounded text-sm"
            />
          </div>
        )}
      </div>
      
      {/* User Input */}
      <div className={`border rounded-lg overflow-hidden ${tools.user_input.enabled ? 'bg-purple-50/50 border-purple-200' : 'bg-slate-50 border-slate-200 opacity-60'}`}>
        <div className={`flex items-center gap-2 px-3 ${py}`}>
          <div className="cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'user_input' ? null : 'user_input')}>
            {expandedTool === 'user_input' ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
          </div>
          <MessageSquare size={14} className="text-purple-500" />
          <span className="font-medium text-sm flex-1 cursor-pointer" onClick={() => setExpandedTool(expandedTool === 'user_input' ? null : 'user_input')}>User Input</span>
          <label className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={tools.user_input.enabled}
              onChange={(e) => updateTool('user_input', { ...tools.user_input, enabled: e.target.checked })}
              className="rounded text-purple-500"
            />
            <span className="text-xs text-slate-500">{tools.user_input.enabled ? 'On' : 'Off'}</span>
          </label>
        </div>
        {expandedTool === 'user_input' && tools.user_input.enabled && (
          <div className="px-3 pb-3 pt-1 border-t bg-white/80">
            <label className="text-xs text-slate-500 block mb-1">Mode</label>
            <select
              value={tools.user_input.mode}
              onChange={(e) => updateTool('user_input', { ...tools.user_input, mode: e.target.value as 'blocking' | 'async' | 'disabled' })}
              className="w-full px-2 py-1 border rounded text-sm"
            >
              <option value="blocking">Blocking</option>
              <option value="async">Async</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
        )}
      </div>
      
      {/* Paradigm */}
      <div className="border rounded-lg overflow-hidden bg-indigo-50/50 border-indigo-200">
        <div 
          className={`flex items-center gap-2 px-3 ${py} cursor-pointer hover:bg-white/50`}
          onClick={() => setExpandedTool(expandedTool === 'paradigm' ? null : 'paradigm')}
        >
          {expandedTool === 'paradigm' ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
          <Workflow size={14} className="text-indigo-500" />
          <span className="font-medium text-sm flex-1">Paradigm</span>
          {tools.paradigm.dir && <span className="text-xs text-slate-500 font-mono truncate max-w-[60px]">{tools.paradigm.dir}</span>}
        </div>
        {expandedTool === 'paradigm' && (
          <div className="px-3 pb-3 pt-1 border-t bg-white/80">
            <label className="text-xs text-slate-500 block mb-1">Custom Directory</label>
            <input
              type="text"
              value={tools.paradigm.dir || ''}
              onChange={(e) => updateTool('paradigm', { ...tools.paradigm, dir: e.target.value || undefined })}
              placeholder="e.g., provisions/paradigms"
              className="w-full px-2 py-1 border rounded text-sm"
            />
            <p className="text-[10px] text-slate-400 mt-1">Leave empty for defaults</p>
          </div>
        )}
      </div>
      
      {/* Custom Tools */}
      {!compact && (
        <CustomToolsSection 
          tools={tools.custom} 
          onChange={(custom) => updateTool('custom', custom)} 
        />
      )}
      
      {/* LLM Settings Panel */}
      <LLMSettingsPanel
        isOpen={showLLMSettings}
        onClose={() => {
          setShowLLMSettings(false);
          fetchProviders();
        }}
      />
    </div>
  );
}

// ============================================================================
// Custom Tools Section
// ============================================================================

interface CustomToolsSectionProps {
  tools: Record<string, CustomToolConfig> | undefined;
  onChange: (tools: Record<string, CustomToolConfig>) => void;
}

function CustomToolsSection({ tools, onChange }: CustomToolsSectionProps) {
  const [newToolName, setNewToolName] = useState('');
  const [newToolTypeId, setNewToolTypeId] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  
  const handleAddTool = () => {
    if (!newToolName.trim() || !newToolTypeId.trim()) return;
    
    const updated = {
      ...(tools || {}),
      [newToolName]: {
        type_id: newToolTypeId,
        enabled: true,
        settings: {},
      },
    };
    onChange(updated);
    setNewToolName('');
    setNewToolTypeId('');
    setIsAdding(false);
  };
  
  const handleRemoveTool = (name: string) => {
    if (!tools) return;
    const { [name]: _, ...rest } = tools;
    onChange(rest);
  };
  
  const handleToggleTool = (name: string, enabled: boolean) => {
    if (!tools || !tools[name]) return;
    onChange({
      ...tools,
      [name]: { ...tools[name], enabled },
    });
  };
  
  const toolEntries = Object.entries(tools || {});
  
  return (
    <div className="mt-3 pt-3 border-t">
      <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2 flex items-center gap-1">
        <Wrench size={10} />
        Custom Tools
      </div>
      
      <div className="space-y-2">
        {toolEntries.length === 0 && !isAdding && (
          <div className="text-xs text-slate-400 italic py-2">
            No custom tools
          </div>
        )}
        
        {toolEntries.map(([name, tool]) => (
          <div 
            key={name}
            className="flex items-center gap-2 p-2 bg-slate-50 rounded border text-sm"
          >
            <Wrench size={12} className="text-slate-400" />
            <div className="flex-1 min-w-0">
              <div className="font-mono text-sm truncate">{name}</div>
              <div className="text-[10px] text-slate-400">type: {tool.type_id}</div>
            </div>
            <input
              type="checkbox"
              checked={tool.enabled}
              onChange={(e) => handleToggleTool(name, e.target.checked)}
              className="rounded"
            />
            <button
              onClick={() => handleRemoveTool(name)}
              className="p-1 hover:bg-red-100 rounded text-red-400"
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
        
        {isAdding ? (
          <div className="p-2 border rounded bg-blue-50 space-y-2">
            <input
              type="text"
              value={newToolName}
              onChange={(e) => setNewToolName(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
              placeholder="Tool name"
              className="w-full px-2 py-1 border rounded text-sm"
            />
            <input
              type="text"
              value={newToolTypeId}
              onChange={(e) => setNewToolTypeId(e.target.value)}
              placeholder="Implementation type_id"
              className="w-full px-2 py-1 border rounded text-sm"
            />
            <div className="flex gap-2">
              <button
                onClick={handleAddTool}
                disabled={!newToolName.trim() || !newToolTypeId.trim()}
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded disabled:opacity-50"
              >
                Add
              </button>
              <button
                onClick={() => setIsAdding(false)}
                className="px-2 py-1 text-xs bg-slate-200 rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
          >
            <Plus size={12} />
            Add Custom Tool
          </button>
        )}
      </div>
    </div>
  );
}

