/**
 * Settings Panel for execution configuration
 */

import { useEffect, useState } from 'react';
import { Settings, RefreshCw, Save, X, Bot, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { executionApi, projectApi } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useProjectStore } from '../../stores/projectStore';
import { useLLMStore } from '../../stores/llmStore';
import { LLMSettingsPanel } from './LLMSettingsPanel';

interface SettingsPanelProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function SettingsPanel({ isOpen, onToggle }: SettingsPanelProps) {
  const {
    llmModel,
    maxCycles,
    dbPath,
    baseDir,
    paradigmDir,
    availableModels,
    defaultMaxCycles,
    defaultDbPath,
    setLlmModel,
    setMaxCycles,
    setDbPath,
    setBaseDir,
    setParadigmDir,
    setAvailableModels,
    setDefaults,
    setLoaded,
  } = useConfigStore();

  const { currentProject, setCurrentProject, projectPath, openTabs, activeTabId } = useProjectStore();
  
  // Check if current project is read-only (e.g., compiler project)
  const isReadOnly = openTabs.find(t => t.id === activeTabId)?.is_read_only ?? false;
  
  // LLM settings state
  const [showLLMSettings, setShowLLMSettings] = useState(false);
  const { providers, fetchProviders, defaultProviderId } = useLLMStore();

  // Fetch config options from API
  const { data: configData, isLoading, refetch } = useQuery({
    queryKey: ['execution-config'],
    queryFn: executionApi.getConfig,
    staleTime: 60000, // Cache for 1 minute
  });

  // Fetch LLM providers on mount
  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  // Update store when config is fetched
  useEffect(() => {
    if (configData) {
      // Merge available models from API with LLM providers
      const apiModels = configData.available_models || [];
      const providerNames = providers
        .filter(p => p.is_enabled)
        .map(p => p.name);
      const allModels = [...new Set(['demo', ...apiModels, ...providerNames])];
      
      setAvailableModels(allModels);
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
  }, [configData, dbPath, maxCycles, providers, setAvailableModels, setDefaults, setDbPath, setMaxCycles, setLoaded]);

  const handleReset = () => {
    setLlmModel('demo');
    setMaxCycles(defaultMaxCycles);
    setDbPath(defaultDbPath);
    setBaseDir('');
    setParadigmDir('');
  };

  // Save settings to project
  const handleSaveToProject = async () => {
    if (!currentProject) return;
    
    try {
      const response = await projectApi.save({
        execution: {
          llm_model: llmModel,
          max_cycles: maxCycles,
          db_path: dbPath,
          base_dir: baseDir || undefined,
          paradigm_dir: paradigmDir || undefined,
        },
      });
      // Update project in store
      setCurrentProject(response.config, projectPath);
    } catch (err) {
      console.error('Failed to save settings to project:', err);
    }
  };

  // Check if settings differ from project
  const hasUnsavedChanges = currentProject && (
    llmModel !== currentProject.execution.llm_model ||
    maxCycles !== currentProject.execution.max_cycles ||
    dbPath !== currentProject.execution.db_path ||
    baseDir !== (currentProject.execution.base_dir || '') ||
    paradigmDir !== (currentProject.execution.paradigm_dir || '')
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
            {/* LLM Model */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-slate-700">
                  LLM Model
                </label>
                <button
                  onClick={() => setShowLLMSettings(true)}
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                >
                  <Bot size={12} />
                  Configure
                  <ChevronRight size={12} />
                </button>
              </div>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {model === 'demo' ? 'Demo (No LLM)' : model}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-500">
                Select the language model for semantic operations
              </p>
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
                SQLite database for checkpointing (relative to base directory)
              </p>
            </div>

            {/* Base Directory Override */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Base Directory (optional)
              </label>
              <input
                type="text"
                value={baseDir}
                onChange={(e) => setBaseDir(e.target.value)}
                placeholder="Auto-detect from repository path"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
              />
              <p className="mt-1 text-xs text-slate-500">
                Override base directory for file operations (leave empty to auto-detect)
              </p>
            </div>

            {/* Paradigm Directory */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Paradigm Directory (optional)
              </label>
              <input
                type="text"
                value={paradigmDir}
                onChange={(e) => setParadigmDir(e.target.value)}
                placeholder="e.g., provision/paradigm"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
              />
              <p className="mt-1 text-xs text-slate-500">
                Custom paradigm directory for project-specific paradigms (relative to base directory)
              </p>
            </div>
          </>
        )}
      </div>

      {/* LLM Settings Panel Modal */}
      <LLMSettingsPanel
        isOpen={showLLMSettings}
        onClose={() => {
          setShowLLMSettings(false);
          // Refresh providers after closing
          fetchProviders();
        }}
      />
    </div>
  );
}
