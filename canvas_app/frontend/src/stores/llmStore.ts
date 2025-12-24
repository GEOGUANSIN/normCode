/**
 * LLM Settings store for managing LLM provider configurations
 */

import { create } from 'zustand';
import type {
  LLMProviderConfig,
  LLMProviderPreset,
  CreateProviderRequest,
  UpdateProviderRequest,
  TestProviderResponse,
} from '../types/llm';

interface LLMState {
  // Data
  providers: LLMProviderConfig[];
  presets: Record<string, LLMProviderPreset>;
  defaultProviderId: string | null;
  
  // UI state
  isLoading: boolean;
  isTestingConnection: boolean;
  error: string | null;
  selectedProviderId: string | null;
  
  // Actions
  fetchProviders: () => Promise<void>;
  fetchPresets: () => Promise<void>;
  createProvider: (request: CreateProviderRequest) => Promise<LLMProviderConfig>;
  updateProvider: (id: string, request: UpdateProviderRequest) => Promise<LLMProviderConfig>;
  deleteProvider: (id: string) => Promise<void>;
  setDefaultProvider: (id: string) => Promise<void>;
  testProvider: (id: string) => Promise<TestProviderResponse>;
  testNewProvider: (config: Partial<CreateProviderRequest>) => Promise<TestProviderResponse>;
  importFromYaml: () => Promise<number>;
  
  // UI actions
  setSelectedProvider: (id: string | null) => void;
  clearError: () => void;
}

const API_BASE = '/api/llm';

export const useLLMStore = create<LLMState>((set, get) => ({
  // Initial state
  providers: [],
  presets: {},
  defaultProviderId: null,
  isLoading: false,
  isTestingConnection: false,
  error: null,
  selectedProviderId: null,
  
  fetchProviders: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers`);
      if (!response.ok) throw new Error('Failed to fetch providers');
      const data = await response.json();
      set({
        providers: data.providers,
        defaultProviderId: data.default_provider_id,
        isLoading: false,
      });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },
  
  fetchPresets: async () => {
    try {
      const response = await fetch(`${API_BASE}/presets`);
      if (!response.ok) throw new Error('Failed to fetch presets');
      const data = await response.json();
      set({ presets: data.presets });
    } catch (err) {
      console.error('Failed to fetch presets:', err);
    }
  },
  
  createProvider: async (request: CreateProviderRequest) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create provider');
      }
      const provider = await response.json();
      
      // Refresh providers list
      await get().fetchProviders();
      
      return provider;
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
      throw err;
    }
  },
  
  updateProvider: async (id: string, request: UpdateProviderRequest) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update provider');
      }
      const provider = await response.json();
      
      // Update in local state
      set(state => ({
        providers: state.providers.map(p => p.id === id ? provider : p),
        isLoading: false,
      }));
      
      return provider;
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
      throw err;
    }
  },
  
  deleteProvider: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete provider');
      }
      
      // Remove from local state
      set(state => ({
        providers: state.providers.filter(p => p.id !== id),
        selectedProviderId: state.selectedProviderId === id ? null : state.selectedProviderId,
        isLoading: false,
      }));
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
      throw err;
    }
  },
  
  setDefaultProvider: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers/${id}/set-default`, {
        method: 'POST',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to set default provider');
      }
      
      // Update local state
      set(state => ({
        defaultProviderId: id,
        providers: state.providers.map(p => ({
          ...p,
          is_default: p.id === id,
        })),
        isLoading: false,
      }));
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
      throw err;
    }
  },
  
  testProvider: async (id: string) => {
    set({ isTestingConnection: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: id }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to test provider');
      }
      const result = await response.json();
      set({ isTestingConnection: false });
      return result;
    } catch (err) {
      set({ error: (err as Error).message, isTestingConnection: false });
      throw err;
    }
  },
  
  testNewProvider: async (config: Partial<CreateProviderRequest>) => {
    set({ isTestingConnection: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/providers/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to test provider');
      }
      const result = await response.json();
      set({ isTestingConnection: false });
      return result;
    } catch (err) {
      set({ error: (err as Error).message, isTestingConnection: false });
      throw err;
    }
  },
  
  importFromYaml: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/import-yaml`, {
        method: 'POST',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to import from YAML');
      }
      const result = await response.json();
      
      // Refresh providers list
      await get().fetchProviders();
      
      return result.imported_count;
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
      throw err;
    }
  },
  
  setSelectedProvider: (id: string | null) => {
    set({ selectedProviderId: id });
  },
  
  clearError: () => {
    set({ error: null });
  },
}));
