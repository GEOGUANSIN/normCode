/**
 * Configuration store for execution settings
 */

import { create } from 'zustand';

interface ConfigState {
  // Current configuration values
  llmModel: string;
  maxCycles: number;
  dbPath: string;
  baseDir: string;
  paradigmDir: string;
  
  // Available options (fetched from API)
  availableModels: string[];
  defaultMaxCycles: number;
  defaultDbPath: string;
  
  // Loading state
  isLoaded: boolean;
  
  // Actions
  setLlmModel: (model: string) => void;
  setMaxCycles: (cycles: number) => void;
  setDbPath: (path: string) => void;
  setBaseDir: (dir: string) => void;
  setParadigmDir: (dir: string) => void;
  setAvailableModels: (models: string[]) => void;
  setDefaults: (defaults: { defaultMaxCycles: number; defaultDbPath: string }) => void;
  setLoaded: (loaded: boolean) => void;
  reset: () => void;
}

const DEFAULT_STATE = {
  llmModel: 'demo',
  maxCycles: 50,
  dbPath: 'orchestration.db',
  baseDir: '',
  paradigmDir: '',
  availableModels: ['demo'],
  defaultMaxCycles: 50,
  defaultDbPath: 'orchestration.db',
  isLoaded: false,
};

export const useConfigStore = create<ConfigState>((set) => ({
  ...DEFAULT_STATE,
  
  setLlmModel: (model) => set({ llmModel: model }),
  setMaxCycles: (cycles) => set({ maxCycles: cycles }),
  setDbPath: (path) => set({ dbPath: path }),
  setBaseDir: (dir) => set({ baseDir: dir }),
  setParadigmDir: (dir) => set({ paradigmDir: dir }),
  setAvailableModels: (models) => set({ availableModels: models }),
  setDefaults: (defaults) => set({ 
    defaultMaxCycles: defaults.defaultMaxCycles,
    defaultDbPath: defaults.defaultDbPath,
  }),
  setLoaded: (loaded) => set({ isLoaded: loaded }),
  reset: () => set(DEFAULT_STATE),
}));
