/**
 * Configuration store for project execution settings
 * 
 * Note: LLM model, base_dir, and paradigm_dir are now configured per-agent
 * in the Agent Panel. This store only holds project-level execution settings.
 */

import { create } from 'zustand';

interface ConfigState {
  // Project execution settings
  maxCycles: number;
  dbPath: string;
  agentConfig: string;  // Path to .agent.json file
  
  // Defaults (fetched from API)
  defaultMaxCycles: number;
  defaultDbPath: string;
  
  // Loading state
  isLoaded: boolean;
  
  // Actions
  setMaxCycles: (cycles: number) => void;
  setDbPath: (path: string) => void;
  setAgentConfig: (config: string) => void;
  setDefaults: (defaults: { defaultMaxCycles: number; defaultDbPath: string }) => void;
  setLoaded: (loaded: boolean) => void;
  reset: () => void;
}

const DEFAULT_STATE = {
  maxCycles: 50,
  dbPath: 'orchestration.db',
  agentConfig: '',  // Path to .agent.json file
  defaultMaxCycles: 50,
  defaultDbPath: 'orchestration.db',
  isLoaded: false,
};

export const useConfigStore = create<ConfigState>((set) => ({
  ...DEFAULT_STATE,
  
  setMaxCycles: (cycles) => set({ maxCycles: cycles }),
  setDbPath: (path) => set({ dbPath: path }),
  setAgentConfig: (config) => set({ agentConfig: config }),
  setDefaults: (defaults) => set({ 
    defaultMaxCycles: defaults.defaultMaxCycles,
    defaultDbPath: defaults.defaultDbPath,
  }),
  setLoaded: (loaded) => set({ isLoaded: loaded }),
  reset: () => set(DEFAULT_STATE),
}));
