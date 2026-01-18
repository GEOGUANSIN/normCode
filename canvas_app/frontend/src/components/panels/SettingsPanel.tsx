/**
 * Settings Panel for project execution configuration
 * 
 * Includes:
 * - Agent Summary (selected agent info)
 * - Runtime Capabilities (read-only introspection)
 * - Execution Settings (max cycles, db path)
 */

import { useState, useEffect } from 'react';
import { 
  Settings, RefreshCw, Save, X, Bot, ChevronRight, ChevronDown,
  Cpu, Wrench, FileCode, Workflow, Layers, Loader2
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { executionApi, projectApi } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useProjectStore } from '../../stores/projectStore';
import { useAgentStore } from '../../stores/agentStore';

// ============================================================================
// Agent Summary Card
// ============================================================================

interface AgentSummaryCardProps {
  onOpenAgentPanel?: () => void;
}

function AgentSummaryCard({ onOpenAgentPanel }: AgentSummaryCardProps) {
  const agents = useAgentStore(s => s.agents);
  const selectedAgentId = useAgentStore(s => s.selectedAgentId);
  const defaultAgentId = useAgentStore(s => s.defaultAgent);
  
  const agentId = selectedAgentId || defaultAgentId;
  const agent = agentId ? agents[agentId] : null;
  
  if (!agent) {
    return (
      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-500">
        No agent selected
      </div>
    );
  }
  
  return (
    <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-purple-600" />
          <span className="font-semibold text-sm text-purple-800">{agent.name}</span>
        </div>
        <button
          onClick={onOpenAgentPanel}
          className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 font-medium"
        >
          Edit
          <ChevronRight size={12} />
        </button>
      </div>
      
      {/* Tool Summary */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-slate-600">
          <Cpu size={12} className="text-blue-500" />
          <span className="font-mono">{agent.tools.llm.model}</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-600">
          <FileCode size={12} className={agent.tools.file_system.enabled ? 'text-green-500' : 'text-slate-300'} />
          <span>File System {agent.tools.file_system.enabled ? '✓' : '✗'}</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-600">
          <Wrench size={12} className={agent.tools.python_interpreter.enabled ? 'text-yellow-500' : 'text-slate-300'} />
          <span>Python {agent.tools.python_interpreter.enabled ? '✓' : '✗'}</span>
        </div>
        {agent.tools.paradigm.dir && (
          <div className="flex items-center gap-1.5 text-slate-600 col-span-2">
            <Workflow size={12} className="text-indigo-500" />
            <span className="font-mono truncate">{agent.tools.paradigm.dir}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Runtime Capabilities Card
// ============================================================================

interface AgentCapabilities {
  agent_id: string;
  tools: Array<{ name: string; enabled: boolean; methods: string[]; description: string }>;
  paradigms: Array<{ name: string; is_custom: boolean }>;
  sequences: Array<{ name: string; category: string }>;
  paradigm_dir: string | null;
  agent_frame_model: string;
}

function RuntimeCapabilitiesCard() {
  const selectedAgentId = useAgentStore(s => s.selectedAgentId);
  const defaultAgentId = useAgentStore(s => s.defaultAgent);
  const agentId = selectedAgentId || defaultAgentId;
  
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
  
  if (loading) {
    return (
      <div className="p-3 border rounded-lg flex items-center justify-center">
        <Loader2 size={16} className="animate-spin text-slate-400" />
      </div>
    );
  }
  
  if (!capabilities) {
    return null;
  }
  
  const enabledTools = capabilities.tools.filter(t => t.enabled);
  const customParadigms = capabilities.paradigms.filter(p => p.is_custom);
  
  return (
    <div className="border rounded-lg overflow-hidden">
      <div 
        className="px-3 py-2 bg-slate-50 flex items-center justify-between cursor-pointer hover:bg-slate-100"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Layers size={14} className="text-green-500" />
          <span>Runtime Capabilities</span>
          <span className="text-[10px] text-slate-400 font-normal bg-slate-200 px-1 rounded">read-only</span>
        </div>
        <div className="text-xs text-slate-500">
          {enabledTools.length} tools • {capabilities.sequences?.length || 0} sequences
        </div>
      </div>
      
      {expanded && (
        <div className="p-3 space-y-3 text-xs">
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
                  title={tool.description}
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
            </div>
            <div className="flex flex-wrap gap-1">
              {capabilities.sequences?.slice(0, 10).map(seq => (
                <span 
                  key={seq.name}
                  className="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded font-mono"
                >
                  {seq.name}
                </span>
              ))}
              {(capabilities.sequences?.length || 0) > 10 && (
                <span className="text-slate-400">+{capabilities.sequences.length - 10} more</span>
              )}
            </div>
          </div>
          
          {/* Paradigms */}
          <div>
            <div className="font-semibold text-slate-600 mb-1 flex items-center gap-1">
              <FileCode size={10} />
              Paradigms
              {customParadigms.length > 0 && (
                <span className="text-green-600 bg-green-100 px-1 rounded">
                  {customParadigms.length} custom
                </span>
              )}
            </div>
            <div className="text-slate-500">
              {capabilities.paradigms.length} total
              {capabilities.paradigm_dir && (
                <span className="ml-2 font-mono text-indigo-600">
                  ({capabilities.paradigm_dir})
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Settings Panel Props
// ============================================================================

interface SettingsPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  onOpenAgentPanel?: () => void;  // Callback to open agent panel
}

export function SettingsPanel({ isOpen, onToggle, onOpenAgentPanel }: SettingsPanelProps) {
  const {
    maxCycles,
    dbPath,
    agentConfig,
    defaultMaxCycles,
    defaultDbPath,
    setMaxCycles,
    setDbPath,
    setDefaults,
    setLoaded,
  } = useConfigStore();

  const { currentProject, setCurrentProject, projectPath, projectConfigFile, openTabs, activeTabId } = useProjectStore();
  
  // Check if current project is read-only (e.g., compiler project)
  const isReadOnly = openTabs.find(t => t.id === activeTabId)?.is_read_only ?? false;

  // Fetch config options from API
  const { data: configData, isLoading } = useQuery({
    queryKey: ['execution-config'],
    queryFn: executionApi.getConfig,
    staleTime: 60000, // Cache for 1 minute
  });

  // Update store when config is fetched
  useEffect(() => {
    if (configData) {
      setDefaults({
        defaultMaxCycles: configData.default_max_cycles,
        defaultDbPath: configData.default_db_path,
      });
      // Set initial values from defaults if not already set
      if (dbPath === 'orchestration.db') {
        setDbPath(configData.default_db_path);
      }
      if (maxCycles === 50) {
        setMaxCycles(configData.default_max_cycles);
      }
      setLoaded(true);
    }
  }, [configData, dbPath, maxCycles, setDefaults, setDbPath, setMaxCycles, setLoaded]);

  const handleReset = () => {
    setMaxCycles(defaultMaxCycles);
    setDbPath(defaultDbPath);
  };

  // Save settings to project
  const handleSaveToProject = async () => {
    if (!currentProject) return;
    
    try {
      const response = await projectApi.save({
        execution: {
          max_cycles: maxCycles,
          db_path: dbPath,
        },
      });
      // Update project in store
      setCurrentProject(response.config, projectPath, projectConfigFile);
    } catch (err) {
      console.error('Failed to save settings to project:', err);
    }
  };

  // Check if settings differ from project
  const hasUnsavedChanges = currentProject && (
    maxCycles !== currentProject.execution.max_cycles ||
    dbPath !== currentProject.execution.db_path
  );

  // Don't render anything when closed - header button handles toggle
  if (!isOpen) {
    return null;
  }

  return (
    <div className="border-b border-slate-200 bg-white relative z-20">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Settings size={14} />
          <span>Execution Settings</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Save button - hidden for read-only projects */}
          {!isReadOnly && currentProject && hasUnsavedChanges && (
            <button
              onClick={handleSaveToProject}
              className="px-2 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors flex items-center gap-1"
              title="Save settings to project"
            >
              <Save size={12} />
              Save
            </button>
          )}
          <button
            onClick={handleReset}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Reset to defaults"
          >
            <RefreshCw size={14} />
          </button>
          <button
            onClick={onToggle}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Close settings"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Settings Form */}
      <div className="p-4 space-y-4 overflow-visible">
        {isLoading ? (
          <div className="text-sm text-slate-500">Loading configuration...</div>
        ) : (
          <>
            {/* Agent Summary */}
            <AgentSummaryCard onOpenAgentPanel={onOpenAgentPanel} />

            {/* Runtime Capabilities */}
            <RuntimeCapabilitiesCard />

            {/* Execution Settings */}
            <div className="border-t pt-4">
              <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3">
                Execution Settings
              </div>
              
              {/* Max Cycles */}
              <div className="mb-3">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Max Cycles
                </label>
                <input
                  type="number"
                  value={maxCycles}
                  onChange={(e) => setMaxCycles(Math.max(1, Math.min(1000, parseInt(e.target.value) || 1)))}
                  min={1}
                  max={1000}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Maximum cycles before stopping (1-1000)
                </p>
              </div>

              {/* Database Path */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Database Path
                </label>
                <input
                  type="text"
                  value={dbPath}
                  onChange={(e) => setDbPath(e.target.value)}
                  placeholder="orchestration.db"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                />
                <p className="mt-1 text-xs text-slate-500">
                  SQLite database for checkpointing
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
