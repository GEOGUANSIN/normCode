/**
 * Settings Panel for execution configuration
 */

import { useEffect, useState } from 'react';
import { Settings, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { executionApi } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';

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

  // Fetch config options from API
  const { data: configData, isLoading, refetch } = useQuery({
    queryKey: ['execution-config'],
    queryFn: executionApi.getConfig,
    staleTime: 60000, // Cache for 1 minute
  });

  // Update store when config is fetched
  useEffect(() => {
    if (configData) {
      setAvailableModels(configData.available_models);
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
  }, [configData, dbPath, maxCycles, setAvailableModels, setDefaults, setDbPath, setMaxCycles, setLoaded]);

  const handleReset = () => {
    setLlmModel('demo');
    setMaxCycles(defaultMaxCycles);
    setDbPath(defaultDbPath);
    setBaseDir('');
    setParadigmDir('');
  };

  if (!isOpen) {
    return (
      <div className="border-b border-slate-200 bg-white">
        <button
          onClick={onToggle}
          className="w-full px-4 py-2 flex items-center justify-between text-sm text-slate-600 hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <Settings size={14} />
            <span>Settings</span>
          </div>
          <ChevronDown size={14} />
        </button>
      </div>
    );
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
            title="Collapse"
          >
            <ChevronUp size={14} />
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
              <label className="block text-sm font-medium text-slate-700 mb-1">
                LLM Model
              </label>
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
    </div>
  );
}
