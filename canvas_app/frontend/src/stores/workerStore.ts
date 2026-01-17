/**
 * Worker Registry state management with Zustand
 * 
 * Mirrors the backend WorkerRegistry to show all running orchestrators/workers.
 */

import { create } from 'zustand';

// Worker visibility states
export type WorkerVisibility = 'visible' | 'hidden' | 'minimized';

// Worker categories
export type WorkerCategory = 'project' | 'assistant' | 'background' | 'ephemeral' | 'remote';

// Worker execution status
export type WorkerStatus = 'idle' | 'loading' | 'ready' | 'running' | 'paused' | 'stepping' | 'completed' | 'failed' | 'stopped';

// Panel types
export type PanelType = 'main' | 'chat' | 'secondary' | 'floating' | 'debug';

// Worker state from backend
export interface WorkerState {
  worker_id: string;
  category: WorkerCategory;
  status: WorkerStatus;
  visibility: WorkerVisibility;
  name: string;
  project_id: string | null;
  project_path: string | null;
  current_inference: string | null;
  completed_count: number;
  total_count: number;
  cycle_count: number;
  run_id: string | null;
  created_at: string | null;
  started_at: string | null;
  last_activity: string | null;
  metadata: Record<string, unknown>;
}

// Panel binding
export interface PanelBinding {
  panel_id: string;
  panel_type: PanelType;
  worker_id: string;
}

// Registered worker with bindings
export interface RegisteredWorker {
  state: WorkerState;
  bindings: string[];
}

interface WorkerStoreState {
  // All workers
  workers: Record<string, RegisteredWorker>;
  
  // Panel bindings
  panelBindings: Record<string, PanelBinding>;
  
  // Selected worker for details view
  selectedWorkerId: string | null;
  
  // Loading state
  isLoading: boolean;
  lastError: string | null;
  
  // Actions
  setWorkers: (workers: Record<string, RegisteredWorker>) => void;
  updateWorker: (workerId: string, worker: RegisteredWorker) => void;
  removeWorker: (workerId: string) => void;
  
  setPanelBindings: (bindings: Record<string, PanelBinding>) => void;
  updatePanelBinding: (panelId: string, binding: PanelBinding | null) => void;
  
  setSelectedWorkerId: (workerId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Fetch from backend
  fetchWorkers: () => Promise<void>;
  bindPanel: (panelId: string, panelType: PanelType, workerId: string) => Promise<boolean>;
  unbindPanel: (panelId: string) => Promise<boolean>;
  switchPanelWorker: (panelId: string, newWorkerId: string) => Promise<boolean>;
  fetchWorkerGraph: (workerId: string) => Promise<{ nodes: unknown[]; edges: unknown[] } | null>;
  fetchWorkerExecutionState: (workerId: string) => Promise<{
    status: string;
    current_inference: string | null;
    completed_count: number;
    total_count: number;
    cycle_count: number;
    node_statuses: Record<string, string>;
    breakpoints: string[];
  } | null>;
  fetchWorkerReference: (workerId: string, conceptName: string) => Promise<{
    concept_name: string;
    has_reference: boolean;
    data: unknown;
    axes: string[];
    shape: number[];
  } | null>;
  getMainPanelWorkerId: () => string | null;
  getChatPanelWorkerId: () => string | null;
  getActiveWorkerId: () => string | null;
}

const API_BASE = '/api/execution';

export const useWorkerStore = create<WorkerStoreState>((set, get) => ({
  workers: {},
  panelBindings: {},
  selectedWorkerId: null,
  isLoading: false,
  lastError: null,
  
  setWorkers: (workers) => set({ workers }),
  
  updateWorker: (workerId, worker) => 
    set((state) => ({
      workers: { ...state.workers, [workerId]: worker },
    })),
  
  removeWorker: (workerId) =>
    set((state) => {
      const { [workerId]: _, ...rest } = state.workers;
      return { workers: rest };
    }),
  
  setPanelBindings: (bindings) => set({ panelBindings: bindings }),
  
  updatePanelBinding: (panelId, binding) =>
    set((state) => {
      if (binding === null) {
        const { [panelId]: _, ...rest } = state.panelBindings;
        return { panelBindings: rest };
      }
      return {
        panelBindings: { ...state.panelBindings, [panelId]: binding },
      };
    }),
  
  setSelectedWorkerId: (workerId) => set({ selectedWorkerId: workerId }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ lastError: error }),
  
  fetchWorkers: async () => {
    set({ isLoading: true, lastError: null });
    try {
      const res = await fetch(`${API_BASE}/workers`);
      if (!res.ok) throw new Error('Failed to fetch workers');
      
      const data = await res.json();
      
      // Parse response
      const workers: Record<string, RegisteredWorker> = {};
      for (const [workerId, workerData] of Object.entries(data.workers || {})) {
        const wd = workerData as { state: WorkerState; bindings: string[] };
        workers[workerId] = {
          state: wd.state,
          bindings: wd.bindings || [],
        };
      }
      
      const panelBindings: Record<string, PanelBinding> = {};
      for (const [panelId, bindingData] of Object.entries(data.panel_bindings || {})) {
        const bd = bindingData as { panel_type: PanelType; worker_id: string };
        panelBindings[panelId] = {
          panel_id: panelId,
          panel_type: bd.panel_type,
          worker_id: bd.worker_id,
        };
      }
      
      set({ workers, panelBindings, isLoading: false });
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Unknown error';
      set({ isLoading: false, lastError: error });
    }
  },
  
  bindPanel: async (panelId, panelType, workerId) => {
    try {
      const res = await fetch(`${API_BASE}/panels/bind`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          panel_id: panelId,
          panel_type: panelType,
          worker_id: workerId,
        }),
      });
      
      if (!res.ok) throw new Error('Failed to bind panel');
      
      const data = await res.json();
      
      // Update local state
      get().updatePanelBinding(panelId, {
        panel_id: panelId,
        panel_type: panelType,
        worker_id: data.worker_id,
      });
      
      // Refresh workers to get updated bindings
      await get().fetchWorkers();
      
      return true;
    } catch (e) {
      console.error('Failed to bind panel:', e);
      return false;
    }
  },
  
  unbindPanel: async (panelId) => {
    try {
      const res = await fetch(`${API_BASE}/panels/${panelId}/unbind`, {
        method: 'POST',
      });
      
      if (!res.ok) throw new Error('Failed to unbind panel');
      
      // Update local state
      get().updatePanelBinding(panelId, null);
      
      // Refresh workers to get updated bindings
      await get().fetchWorkers();
      
      return true;
    } catch (e) {
      console.error('Failed to unbind panel:', e);
      return false;
    }
  },
  
  switchPanelWorker: async (panelId, newWorkerId) => {
    try {
      const res = await fetch(`${API_BASE}/panels/${panelId}/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ worker_id: newWorkerId }),
      });
      
      if (!res.ok) throw new Error('Failed to switch panel worker');
      
      // Refresh to get updated state
      await get().fetchWorkers();
      
      return true;
    } catch (e) {
      console.error('Failed to switch panel worker:', e);
      return false;
    }
  },
  
  fetchWorkerGraph: async (workerId: string) => {
    try {
      const res = await fetch(`${API_BASE}/workers/${workerId}/graph`);
      if (!res.ok) {
        throw new Error(`Failed to fetch graph for worker ${workerId}`);
      }
      return await res.json();
    } catch (e) {
      console.error('Failed to fetch worker graph:', e);
      return null;
    }
  },
  
  fetchWorkerExecutionState: async (workerId: string) => {
    try {
      const res = await fetch(`${API_BASE}/workers/${workerId}/state`);
      if (!res.ok) {
        throw new Error(`Failed to fetch state for worker ${workerId}`);
      }
      return await res.json() as {
        status: string;
        current_inference: string | null;
        completed_count: number;
        total_count: number;
        cycle_count: number;
        node_statuses: Record<string, string>;
        breakpoints: string[];
      };
    } catch (e) {
      console.error('Failed to fetch worker execution state:', e);
      return null;
    }
  },
  
  fetchWorkerReference: async (workerId: string, conceptName: string) => {
    try {
      const res = await fetch(`${API_BASE}/workers/${workerId}/reference/${encodeURIComponent(conceptName)}`);
      if (!res.ok) {
        throw new Error(`Failed to fetch reference for ${conceptName} from worker ${workerId}`);
      }
      return await res.json();
    } catch (e) {
      console.error('Failed to fetch worker reference:', e);
      return null;
    }
  },
  
  // Get the worker ID bound to the main panel (if any)
  getMainPanelWorkerId: () => {
    const { panelBindings } = get();
    const mainBinding = panelBindings['main_panel'];
    return mainBinding?.worker_id || null;
  },
  
  // Get the worker ID bound to the chat panel (if any)
  getChatPanelWorkerId: () => {
    const { panelBindings } = get();
    const chatBinding = panelBindings['chat_panel'];
    return chatBinding?.worker_id || null;
  },
  
  // Get any active worker ID (checks main_panel first, then chat_panel)
  getActiveWorkerId: () => {
    const { panelBindings } = get();
    // Check main panel first
    const mainBinding = panelBindings['main_panel'];
    if (mainBinding?.worker_id) {
      return mainBinding.worker_id;
    }
    // Fall back to chat panel
    const chatBinding = panelBindings['chat_panel'];
    return chatBinding?.worker_id || null;
  },
}));

