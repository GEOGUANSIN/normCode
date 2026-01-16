/**
 * Deployment state management with Zustand
 */
import { create } from 'zustand';
import type { 
  DeploymentServer, 
  ServerHealth, 
  RemotePlan, 
  DeployResult,
  RemoteRunStatus,
} from '../types/deployment';
import { deploymentApi } from '../services/api';
import { useNotificationStore } from './notificationStore';

interface DeploymentState {
  // Server management
  servers: DeploymentServer[];
  selectedServerId: string | null;
  
  // Server health
  serverHealth: Record<string, ServerHealth>;
  
  // Remote plans on selected server
  remotePlans: RemotePlan[];
  
  // Active remote runs
  activeRuns: RemoteRunStatus[];
  
  // UI state
  isLoading: boolean;
  isDeploying: boolean;
  isPanelOpen: boolean;
  activeTab: 'servers' | 'deploy' | 'runs';
  error: string | null;
  lastDeployResult: DeployResult | null;
  
  // Actions
  setServers: (servers: DeploymentServer[]) => void;
  setSelectedServerId: (id: string | null) => void;
  setServerHealth: (serverId: string, health: ServerHealth) => void;
  setRemotePlans: (plans: RemotePlan[]) => void;
  setPanelOpen: (open: boolean) => void;
  setActiveTab: (tab: 'servers' | 'deploy' | 'runs') => void;
  setError: (error: string | null) => void;
  
  // Async actions
  fetchServers: () => Promise<void>;
  addServer: (name: string, url: string, description?: string, isDefault?: boolean) => Promise<boolean>;
  removeServer: (serverId: string) => Promise<void>;
  updateServer: (serverId: string, updates: { name?: string; url?: string; description?: string; is_default?: boolean }) => Promise<boolean>;
  checkServerHealth: (serverId: string) => Promise<ServerHealth | null>;
  testConnection: (url: string) => Promise<ServerHealth | null>;
  deployCurrentProject: (serverId: string) => Promise<boolean>;
  fetchRemotePlans: (serverId: string) => Promise<void>;
  startRemoteRun: (serverId: string, planId: string, llmModel?: string) => Promise<RemoteRunStatus | null>;
  refreshRunStatus: (serverId: string, runId: string) => Promise<void>;
  
  // Reset
  reset: () => void;
}

export const useDeploymentStore = create<DeploymentState>((set, get) => ({
  // Initial state
  servers: [],
  selectedServerId: null,
  serverHealth: {},
  remotePlans: [],
  activeRuns: [],
  isLoading: false,
  isDeploying: false,
  isPanelOpen: false,
  activeTab: 'servers',
  error: null,
  lastDeployResult: null,
  
  // Simple setters
  setServers: (servers) => set({ servers }),
  setSelectedServerId: (id) => set({ selectedServerId: id }),
  setServerHealth: (serverId, health) => set((state) => ({
    serverHealth: { ...state.serverHealth, [serverId]: health }
  })),
  setRemotePlans: (plans) => set({ remotePlans: plans }),
  setPanelOpen: (open) => set({ isPanelOpen: open }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setError: (error) => set({ error }),
  
  // Fetch all servers
  fetchServers: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await deploymentApi.listServers();
      set({ servers: response.servers, isLoading: false });
      
      // Auto-select default server if none selected
      const { selectedServerId } = get();
      if (!selectedServerId && response.servers.length > 0) {
        const defaultServer = response.servers.find(s => s.is_default) || response.servers[0];
        set({ selectedServerId: defaultServer.id });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch servers';
      set({ error: message, isLoading: false });
    }
  },
  
  // Add a new server
  addServer: async (name, url, description, isDefault = false) => {
    set({ isLoading: true, error: null });
    try {
      const server = await deploymentApi.addServer({ name, url, description, is_default: isDefault });
      set((state) => ({
        servers: [...state.servers, server],
        selectedServerId: server.id,
        isLoading: false,
      }));
      
      useNotificationStore.getState().showSuccess(
        'Server Added',
        `${name} has been added to your deployment servers.`,
        3000
      );
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add server';
      set({ error: message, isLoading: false });
      useNotificationStore.getState().showError('Failed to Add Server', message);
      return false;
    }
  },
  
  // Remove a server
  removeServer: async (serverId) => {
    try {
      await deploymentApi.removeServer(serverId);
      set((state) => ({
        servers: state.servers.filter(s => s.id !== serverId),
        selectedServerId: state.selectedServerId === serverId ? null : state.selectedServerId,
      }));
    } catch (err) {
      console.error('Failed to remove server:', err);
    }
  },
  
  // Update a server
  updateServer: async (serverId, updates) => {
    try {
      const server = await deploymentApi.updateServer(serverId, updates);
      set((state) => ({
        servers: state.servers.map(s => s.id === serverId ? server : s),
      }));
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update server';
      set({ error: message });
      return false;
    }
  },
  
  // Check server health
  checkServerHealth: async (serverId) => {
    try {
      const health = await deploymentApi.checkHealth(serverId);
      set((state) => ({
        serverHealth: { ...state.serverHealth, [serverId]: health }
      }));
      return health;
    } catch (err) {
      console.error('Failed to check server health:', err);
      return null;
    }
  },
  
  // Test a connection URL before adding
  testConnection: async (url) => {
    set({ isLoading: true });
    try {
      const health = await deploymentApi.testConnection(url);
      set({ isLoading: false });
      return health;
    } catch (err) {
      set({ isLoading: false });
      return null;
    }
  },
  
  // Deploy current project to a server
  deployCurrentProject: async (serverId) => {
    set({ isDeploying: true, error: null, lastDeployResult: null });
    try {
      const result = await deploymentApi.deployProject({ server_id: serverId });
      set({ isDeploying: false, lastDeployResult: result });
      
      if (result.success) {
        useNotificationStore.getState().showSuccess(
          'Deployment Successful',
          `${result.plan_name} deployed to ${result.server_name}`,
          5000
        );
      } else {
        useNotificationStore.getState().showError(
          'Deployment Failed',
          result.message
        );
      }
      
      return result.success;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Deployment failed';
      set({ isDeploying: false, error: message });
      useNotificationStore.getState().showError('Deployment Failed', message);
      return false;
    }
  },
  
  // Fetch plans from a remote server
  fetchRemotePlans: async (serverId) => {
    set({ isLoading: true });
    try {
      const response = await deploymentApi.listRemotePlans(serverId);
      set({ remotePlans: response.plans, isLoading: false });
    } catch (err) {
      console.error('Failed to fetch remote plans:', err);
      set({ remotePlans: [], isLoading: false });
    }
  },
  
  // Start a run on a remote server
  startRemoteRun: async (serverId, planId, llmModel) => {
    try {
      const run = await deploymentApi.startRemoteRun({
        server_id: serverId,
        plan_id: planId,
        llm_model: llmModel,
      });
      set((state) => ({
        activeRuns: [...state.activeRuns, run],
      }));
      
      useNotificationStore.getState().showSuccess(
        'Run Started',
        `Started run ${run.run_id.substring(0, 8)}...`,
        3000
      );
      
      return run;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start run';
      useNotificationStore.getState().showError('Failed to Start Run', message);
      return null;
    }
  },
  
  // Refresh status of a remote run
  refreshRunStatus: async (serverId, runId) => {
    try {
      const status = await deploymentApi.getRemoteRunStatus(serverId, runId);
      set((state) => ({
        activeRuns: state.activeRuns.map(r => 
          r.run_id === runId ? status : r
        ),
      }));
    } catch (err) {
      console.error('Failed to refresh run status:', err);
    }
  },
  
  // Reset store
  reset: () => set({
    remotePlans: [],
    activeRuns: [],
    isLoading: false,
    isDeploying: false,
    error: null,
    lastDeployResult: null,
  }),
}));

