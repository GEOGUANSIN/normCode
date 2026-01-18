/**
 * Settings Panel for project execution configuration
 * 
 * Note: LLM model, base_dir, and paradigm_dir are now configured per-agent
 * in the Agent Panel. This panel only shows project-level execution settings.
 */

import { useEffect } from 'react';
import { Settings, RefreshCw, Save, X, Bot, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { executionApi, projectApi } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useProjectStore } from '../../stores/projectStore';

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
            {/* Agent Tools Notice */}
            <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-purple-700">
                  <Bot size={16} />
                  <span className="font-medium">LLM, paradigm & tools</span>
                </div>
                <button
                  onClick={onOpenAgentPanel}
                  className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 font-medium"
                >
                  Configure in Agent Panel
                  <ChevronRight size={12} />
                </button>
              </div>
              <p className="mt-1 text-xs text-purple-600">
                LLM model, paradigm directory, and file system settings are now configured per-agent in the Agent Panel.
              </p>
              {agentConfig && (
                <p className="mt-1 text-xs text-purple-500 font-mono">
                  Config: {agentConfig}
                </p>
              )}
            </div>

            {/* Max Cycles */}
            <div>
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
                Maximum execution cycles before stopping (1-1000)
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
                SQLite database for checkpointing (relative to project directory)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
