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
  RemoteRunResult,
  BuildServerResponse,
  // Remote graph & inspection types
  RemotePlanGraph,
  RemoteCanvasGraph,
  RemoteRunDbOverview,
  RemoteRunExecutions,
  RemoteRunStatistics,
  RemoteRunCheckpoints,
  RemoteCheckpointState,
  RemoteBlackboardSummary,
  RemoteCompletedConcepts,
  RemoteResumeResult,
  BoundRemoteRun,
} from '../types/deployment';
import { deploymentApi, workerApi } from '../services/api';
import { useNotificationStore } from './notificationStore';
import { useGraphStore } from './graphStore';
import { useProjectStore } from './projectStore';
import type { GraphData, GraphNode, GraphEdge } from '../types/graph';

interface DeploymentState {
  // Server management
  servers: DeploymentServer[];
  selectedServerId: string | null;
  
  // Server health
  serverHealth: Record<string, ServerHealth>;
  
  // Remote plans on selected server
  remotePlans: RemotePlan[];
  
  // Active remote runs (including historical)
  activeRuns: RemoteRunStatus[];
  
  // Run results cache (run_id -> result)
  runResults: Record<string, RemoteRunResult>;
  
  // Remote graph cache (plan_id -> graph data)
  remotePlanGraphs: Record<string, RemotePlanGraph>;
  
  // Remote canvas graphs cache (tab_id -> canvas-ready graph data)
  remoteCanvasGraphs: Record<string, RemoteCanvasGraph>;
  
  // Currently loaded remote graph on canvas
  loadedRemoteGraph: RemoteCanvasGraph | null;
  
  // Bound remote runs (mirrored to local canvas)
  boundRemoteRuns: BoundRemoteRun[];
  activeBoundRunId: string | null;
  
  // Selected remote run for inspection
  selectedRemoteRunId: string | null;
  
  // Remote run inspection data
  remoteRunDbOverview: RemoteRunDbOverview | null;
  remoteRunExecutions: RemoteRunExecutions | null;
  remoteRunStatistics: RemoteRunStatistics | null;
  remoteRunCheckpoints: RemoteRunCheckpoints | null;
  remoteCheckpointState: RemoteCheckpointState | null;
  remoteBlackboard: RemoteBlackboardSummary | null;
  remoteCompletedConcepts: RemoteCompletedConcepts | null;
  
  // Polling interval ID
  _pollingIntervalId: ReturnType<typeof setInterval> | null;
  
  // UI state
  isLoading: boolean;
  isDeploying: boolean;
  isBuilding: boolean;
  isPanelOpen: boolean;
  activeTab: 'servers' | 'deploy' | 'runs' | 'build' | 'inspect';
  error: string | null;
  lastDeployResult: DeployResult | null;
  lastBuildResult: BuildServerResponse | null;
  
  // Actions
  setServers: (servers: DeploymentServer[]) => void;
  setSelectedServerId: (id: string | null) => void;
  setServerHealth: (serverId: string, health: ServerHealth) => void;
  setRemotePlans: (plans: RemotePlan[]) => void;
  setPanelOpen: (open: boolean) => void;
  setActiveTab: (tab: 'servers' | 'deploy' | 'runs' | 'build' | 'inspect') => void;
  setError: (error: string | null) => void;
  setSelectedRemoteRunId: (runId: string | null) => void;
  
  // Async actions - Server management
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
  refreshAllActiveRuns: () => Promise<void>;
  fetchRunResult: (serverId: string, runId: string) => Promise<RemoteRunResult | null>;
  startPolling: () => void;
  stopPolling: () => void;
  buildServer: (options?: { outputDir?: string; includeTestPlans?: boolean; createZip?: boolean }) => Promise<BuildServerResponse | null>;
  
  // Async actions - Remote graph loading
  fetchRemotePlanGraph: (serverId: string, planId: string) => Promise<RemotePlanGraph | null>;
  loadRemotePlanOnCanvas: (serverId: string, planId: string, llmModel?: string) => Promise<boolean>;
  loadRemoteRunOnCanvas: (serverId: string, runId: string, planId: string, planName: string, runStatus?: string) => Promise<boolean>;  // Load graph + bind run for live updates
  loadCachedRemoteGraph: (tabId: string) => boolean;  // Load from cache when switching tabs
  clearLoadedRemoteGraph: () => void;
  
  // Async actions - Remote runs listing (includes historical)
  fetchRemoteRuns: (serverId: string, includeHistorical?: boolean) => Promise<void>;
  
  // Async actions - Remote run inspection
  fetchRemoteRunDbOverview: (serverId: string, runId: string) => Promise<RemoteRunDbOverview | null>;
  fetchRemoteRunExecutions: (serverId: string, runId: string, options?: { includeLogs?: boolean; limit?: number; offset?: number }) => Promise<RemoteRunExecutions | null>;
  fetchRemoteRunStatistics: (serverId: string, runId: string) => Promise<RemoteRunStatistics | null>;
  fetchRemoteRunCheckpoints: (serverId: string, runId: string) => Promise<RemoteRunCheckpoints | null>;
  fetchRemoteCheckpointState: (serverId: string, runId: string, cycle: number, inferenceCount?: number) => Promise<RemoteCheckpointState | null>;
  fetchRemoteBlackboard: (serverId: string, runId: string, cycle?: number) => Promise<RemoteBlackboardSummary | null>;
  fetchRemoteCompletedConcepts: (serverId: string, runId: string, cycle?: number) => Promise<RemoteCompletedConcepts | null>;
  resumeRemoteRun: (serverId: string, runId: string, options?: { cycle?: number; inferenceCount?: number; llmModel?: string; fork?: boolean }) => Promise<RemoteResumeResult | null>;
  
  // Remote run binding (mirror to local canvas)
  bindRemoteRun: (serverId: string, runId: string, planId: string, planName: string) => Promise<boolean>;
  unbindRemoteRun: (serverId: string, runId: string) => Promise<boolean>;
  fetchBoundRuns: () => Promise<void>;
  
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
  runResults: {},
  remotePlanGraphs: {},
  remoteCanvasGraphs: {},
  loadedRemoteGraph: null,
  boundRemoteRuns: [],
  activeBoundRunId: null,
  selectedRemoteRunId: null,
  remoteRunDbOverview: null,
  remoteRunExecutions: null,
  remoteRunStatistics: null,
  remoteRunCheckpoints: null,
  remoteCheckpointState: null,
  remoteBlackboard: null,
  remoteCompletedConcepts: null,
  _pollingIntervalId: null,
  isLoading: false,
  isDeploying: false,
  isBuilding: false,
  isPanelOpen: false,
  activeTab: 'servers',
  error: null,
  lastDeployResult: null,
  lastBuildResult: null,
  
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
  setSelectedRemoteRunId: (runId) => set({ 
    selectedRemoteRunId: runId,
    // Clear inspection data when changing run
    remoteRunDbOverview: null,
    remoteRunExecutions: null,
    remoteRunStatistics: null,
    remoteRunCheckpoints: null,
    remoteCheckpointState: null,
    remoteBlackboard: null,
    remoteCompletedConcepts: null,
  }),
  
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
    const { remotePlans } = get();
    const plan = remotePlans.find(p => p.id === planId);
    const planName = plan?.name || planId;
    
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
      
      // Check if this plan is currently loaded on canvas - if so, auto-bind the run
      const { activeRemoteTabId, remoteProjectTabs } = useProjectStore.getState();
      const activeRemoteTab = activeRemoteTabId 
        ? remoteProjectTabs.find(t => t.id === activeRemoteTabId)
        : null;
      
      if (activeRemoteTab && activeRemoteTab.server_id === serverId && activeRemoteTab.plan_id === planId) {
        // This run is for the currently active remote tab - bind it automatically
        console.log(`[deploymentStore] Auto-binding run ${run.run_id} to active remote tab`);
        get().bindRemoteRun(serverId, run.run_id, planId, planName);
      }
      
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
      
      // If completed, fetch result
      if (status.status === 'completed') {
        get().fetchRunResult(serverId, runId);
      }
    } catch (err) {
      console.error('Failed to refresh run status:', err);
    }
  },
  
  // Refresh all active runs
  refreshAllActiveRuns: async () => {
    const { activeRuns } = get();
    const runningRuns = activeRuns.filter(r => r.status === 'running' || r.status === 'pending');
    
    for (const run of runningRuns) {
      await get().refreshRunStatus(run.server_id, run.run_id);
    }
  },
  
  // Fetch result of a completed run
  fetchRunResult: async (serverId, runId) => {
    try {
      const result = await deploymentApi.getRemoteRunResult(serverId, runId) as RemoteRunResult;
      set((state) => ({
        runResults: { ...state.runResults, [runId]: result },
      }));
      return result;
    } catch (err) {
      console.error('Failed to fetch run result:', err);
      return null;
    }
  },
  
  // Start polling for run status updates
  startPolling: () => {
    const { _pollingIntervalId } = get();
    if (_pollingIntervalId) return; // Already polling
    
    const intervalId = setInterval(() => {
      get().refreshAllActiveRuns();
    }, 3000); // Poll every 3 seconds
    
    set({ _pollingIntervalId: intervalId });
  },
  
  // Stop polling
  stopPolling: () => {
    const { _pollingIntervalId } = get();
    if (_pollingIntervalId) {
      clearInterval(_pollingIntervalId);
      set({ _pollingIntervalId: null });
    }
  },
  
  // Build a deployment server
  buildServer: async (options = {}) => {
    set({ isBuilding: true, error: null, lastBuildResult: null });
    try {
      const result = await deploymentApi.buildServer({
        output_dir: options.outputDir,
        include_test_plans: options.includeTestPlans,
        create_zip: options.createZip,
      });
      set({ isBuilding: false, lastBuildResult: result });
      
      if (result.success) {
        useNotificationStore.getState().showSuccess(
          'Server Built',
          `Deployment server created at ${result.output_dir}`,
          5000
        );
      } else {
        useNotificationStore.getState().showError(
          'Build Failed',
          result.message
        );
      }
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Build failed';
      set({ isBuilding: false, error: message });
      useNotificationStore.getState().showError('Build Failed', message);
      return null;
    }
  },
  
  // =========================================================================
  // Remote Graph Loading
  // =========================================================================
  
  fetchRemotePlanGraph: async (serverId, planId) => {
    set({ isLoading: true, error: null });
    try {
      const graph = await deploymentApi.getRemotePlanGraph(serverId, planId);
      set((state) => ({
        remotePlanGraphs: { ...state.remotePlanGraphs, [planId]: graph },
        isLoading: false,
      }));
      return graph;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch plan graph';
      set({ error: message, isLoading: false });
      console.error('Failed to fetch remote plan graph:', err);
      return null;
    }
  },
  
  loadRemotePlanOnCanvas: async (serverId, planId, llmModel) => {
    /**
     * Load a remote plan on canvas WITHOUT starting a run.
     * 
     * This opens the remote plan as a project tab and displays the graph,
     * but does NOT start execution. The user can then click "Start" in the
     * ControlPanel when ready.
     * 
     * Flow:
     * 1. Open remote project as a tab (with LLM model configuration)
     * 2. Fetch and display the graph
     * 3. Store remote project metadata (server_url, plan_id, llm_model) for later execution
     * 
     * When the user clicks "Start" in ControlPanel, the unified execution
     * system will detect it's a remote project and handle accordingly,
     * using the configured LLM model.
     */
    const { addNotification } = useNotificationStore.getState();
    const { setGraphData } = useGraphStore.getState();
    const { servers } = get();
    set({ isLoading: true, error: null });
    
    try {
      const server = servers.find(s => s.id === serverId);
      if (!server) {
        throw new Error(`Server not found: ${serverId}`);
      }
      
      // STEP 1: Open the remote project as a regular tab (unified with local projects)
      console.log(`[Remote] Opening remote project: ${planId} on ${server.name} with LLM: ${llmModel || 'default'}`);
      const { projectApi } = await import('../services/api');
      
      const remoteProject = await projectApi.openRemote({
        server_id: serverId,
        plan_id: planId,
        make_active: true,
        llm_model: llmModel,  // Pass the LLM model for remote execution
      });
      
      console.log(`[Remote] Opened remote project as tab: ${remoteProject.name} (id: ${remoteProject.id})`);
      
      // STEP 2: Sync tabs from backend to get the updated tab list
      await useProjectStore.getState().fetchOpenTabs();
      
      // STEP 3: Fetch canvas-ready graph (nodes + edges) from remote server
      // This is just for display - no run is started yet
      const canvasGraph = await deploymentApi.getRemoteCanvasGraph(serverId, planId);
      
      // Convert remote graph format to GraphData format for the canvas
      const graphData: GraphData = {
        nodes: canvasGraph.nodes.map(n => ({
          ...n,
          category: n.category as GraphNode['category'],
          node_type: n.node_type as GraphNode['node_type'],
        })) as GraphNode[],
        edges: canvasGraph.edges.map(e => ({
          ...e,
          edge_type: e.edge_type as GraphEdge['edge_type'],
        })) as GraphEdge[],
      };
      
      // Set the graph in graphStore for canvas rendering
      setGraphData(graphData);
      
      // STEP 4: Store the remote project info for later use
      // When user clicks "Start", the execution system will use this info
      // to start a run and activate the remote proxy
      const cacheKey = `remote:${serverId}:${planId}`;
      set((state) => ({ 
        loadedRemoteGraph: canvasGraph, 
        remoteCanvasGraphs: { ...state.remoteCanvasGraphs, [cacheKey]: canvasGraph },
        // Don't set activeBoundRunId - no run is started yet
        isLoading: false,
      }));
      
      addNotification({
        type: 'success',
        title: 'Remote Project Loaded',
        message: `Opened "${canvasGraph.plan_name}" from ${server.name}. Click Start to run.`,
        duration: 4000,
      });
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load remote plan';
      set({ error: message, isLoading: false });
      console.error('Failed to load remote plan on canvas:', err);
      
      addNotification({
        type: 'error',
        title: 'Failed to Load',
        message,
        duration: 6000,
      });
      
      return false;
    }
  },
  
  loadRemoteRunOnCanvas: async (serverId, runId, planId, planName, runStatus) => {
    const { addNotification } = useNotificationStore.getState();
    const { setGraphData } = useGraphStore.getState();
    const { servers, activeRuns } = get();
    set({ isLoading: true, error: null });
    
    // Check if run is active (can be bound for live updates)
    const isActiveRun = runStatus === 'running' || runStatus === 'paused' || runStatus === 'pending';
    
    try {
      const server = servers.find(s => s.id === serverId);
      if (!server) {
        throw new Error(`Server not found: ${serverId}`);
      }
      
      // 1. Fetch canvas-ready graph (nodes + edges) from remote server
      const canvasGraph = await deploymentApi.getRemoteCanvasGraph(serverId, planId);
      
      // Convert remote graph format to GraphData format for the canvas
      const graphData: GraphData = {
        nodes: canvasGraph.nodes.map(n => ({
          ...n,
          category: n.category as GraphNode['category'],
          node_type: n.node_type as GraphNode['node_type'],
        })) as GraphNode[],
        edges: canvasGraph.edges.map(e => ({
          ...e,
          edge_type: e.edge_type as GraphEdge['edge_type'],
        })) as GraphEdge[],
      };
      
      // Set the graph in graphStore for canvas rendering
      setGraphData(graphData);
      
      // 2. UNIFIED APPROACH: Register remote worker via WorkerRegistry
      // This creates a RemoteExecutionController that handles all remote communication
      // The worker will show up in WorkersPanel and ControlPanel works automatically
      let workerId: string | null = null;
      let bindSuccess = false;
      
      if (isActiveRun) {
        try {
          // Register the remote worker with the backend's WorkerRegistry
          const result = await workerApi.connectRemote({
            server_url: server.url,
            run_id: runId,
            panel_id: 'main',  // Bind to main panel
            panel_type: 'main',
          });
          
          workerId = result.worker_id;
          bindSuccess = result.success;
          
          console.log(`[Remote] Registered worker: ${workerId}`);
        } catch (err) {
          console.warn('[Remote] Failed to register remote worker:', err);
          bindSuccess = false;
        }
      }
      
      // 3. Store the loaded remote graph metadata and cache it
      const cacheKey = `remote:${serverId}:${planId}:${runId}`;
      
      set((state) => ({ 
        loadedRemoteGraph: canvasGraph, 
        remoteCanvasGraphs: { ...state.remoteCanvasGraphs, [cacheKey]: canvasGraph },
        activeBoundRunId: runId,
        isLoading: false,
      }));
      
      // 4. Notify success - NO SPECIAL REMOTE TAB NEEDED
      // The remote proxy worker shows in WorkersPanel, ControlPanel uses worker API
      if (isActiveRun && bindSuccess && workerId) {
        addNotification({
          type: 'success',
          title: 'Remote Run Connected',
          message: `Connected to "${planName}" on ${server.name} - live control via remote proxy worker`,
          duration: 4000,
        });
      } else if (!isActiveRun) {
        // For completed/failed runs, sync from activeRuns list to executionStore
        const { useExecutionStore } = await import('./executionStore');
        const execStore = useExecutionStore.getState();
        
        const run = activeRuns.find(r => r.run_id === runId);
        if (run) {
          const statusMap: Record<string, string> = {
            'running': 'running',
            'paused': 'paused',
            'pending': 'idle',
            'completed': 'completed',
            'failed': 'failed',
            'stopped': 'idle',
          };
          const execStatus = statusMap[run.status] || 'completed';
          execStore.setStatus(execStatus as any);
          execStore.setProgress(
            run.progress?.completed_count || 0,
            run.progress?.total_count || 0,
            run.progress?.cycle_count || 0
          );
        } else if (runStatus) {
          const statusMap: Record<string, string> = {
            'running': 'running',
            'paused': 'paused',
            'pending': 'idle',
            'completed': 'completed',
            'failed': 'failed',
            'stopped': 'idle',
          };
          execStore.setStatus((statusMap[runStatus] || 'completed') as any);
        }
        
        addNotification({
          type: 'success',
          title: 'Remote Run Loaded',
          message: `Loaded "${planName}" (${runStatus || 'completed'}) from ${server?.name || 'remote server'}`,
          duration: 4000,
        });
      }
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load remote run';
      set({ error: message, isLoading: false });
      console.error('Failed to load remote run on canvas:', err);
      
      addNotification({
        type: 'error',
        title: 'Failed to Load',
        message,
        duration: 6000,
      });
      
      return false;
    }
  },
  
  loadCachedRemoteGraph: (tabId) => {
    const { remoteCanvasGraphs } = get();
    const cachedGraph = remoteCanvasGraphs[tabId];
    
    if (!cachedGraph) {
      console.warn(`No cached graph found for tab: ${tabId}`);
      return false;
    }
    
    // Convert cached graph to GraphData and set in graphStore
    const { setGraphData } = useGraphStore.getState();
    const graphData: GraphData = {
      nodes: cachedGraph.nodes.map(n => ({
        ...n,
        category: n.category as GraphNode['category'],
        node_type: n.node_type as GraphNode['node_type'],
      })) as GraphNode[],
      edges: cachedGraph.edges.map(e => ({
        ...e,
        edge_type: e.edge_type as GraphEdge['edge_type'],
      })) as GraphEdge[],
    };
    
    setGraphData(graphData);
    set({ loadedRemoteGraph: cachedGraph });
    return true;
  },
  
  clearLoadedRemoteGraph: () => {
    const { loadedRemoteGraph } = get();
    if (!loadedRemoteGraph) return;
    
    const projectStore = useProjectStore.getState();
    const tabId = `remote:${loadedRemoteGraph.server_id}:${loadedRemoteGraph.plan_id}`;
    projectStore.closeRemoteTab(tabId);
    set({ loadedRemoteGraph: null });
  },
  
  // =========================================================================
  // Remote Runs (includes historical)
  // =========================================================================
  
  fetchRemoteRuns: async (serverId, includeHistorical = true) => {
    set({ isLoading: true });
    try {
      const runs = await deploymentApi.listRemoteRuns(serverId, includeHistorical);
      // Add server_id to each run if not present
      const runsWithServer = runs.map(r => ({ ...r, server_id: r.server_id || serverId }));
      set({ activeRuns: runsWithServer, isLoading: false });
    } catch (err) {
      console.error('Failed to fetch remote runs:', err);
      set({ activeRuns: [], isLoading: false });
    }
  },
  
  // =========================================================================
  // Remote Run Database Inspection
  // =========================================================================
  
  fetchRemoteRunDbOverview: async (serverId, runId) => {
    set({ isLoading: true });
    try {
      const overview = await deploymentApi.getRemoteRunDbOverview(serverId, runId);
      set({ remoteRunDbOverview: overview, isLoading: false });
      return overview;
    } catch (err) {
      console.error('Failed to fetch run DB overview:', err);
      set({ remoteRunDbOverview: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteRunExecutions: async (serverId, runId, options = {}) => {
    set({ isLoading: true });
    try {
      const executions = await deploymentApi.getRemoteRunExecutions(serverId, runId, options);
      set({ remoteRunExecutions: executions, isLoading: false });
      return executions;
    } catch (err) {
      console.error('Failed to fetch run executions:', err);
      set({ remoteRunExecutions: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteRunStatistics: async (serverId, runId) => {
    set({ isLoading: true });
    try {
      const statistics = await deploymentApi.getRemoteRunStatistics(serverId, runId);
      set({ remoteRunStatistics: statistics, isLoading: false });
      return statistics;
    } catch (err) {
      console.error('Failed to fetch run statistics:', err);
      set({ remoteRunStatistics: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteRunCheckpoints: async (serverId, runId) => {
    set({ isLoading: true });
    try {
      const checkpoints = await deploymentApi.listRemoteRunCheckpoints(serverId, runId);
      set({ remoteRunCheckpoints: checkpoints, isLoading: false });
      return checkpoints;
    } catch (err) {
      console.error('Failed to fetch run checkpoints:', err);
      set({ remoteRunCheckpoints: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteCheckpointState: async (serverId, runId, cycle, inferenceCount) => {
    set({ isLoading: true });
    try {
      const state = await deploymentApi.getRemoteCheckpointState(serverId, runId, cycle, inferenceCount);
      set({ remoteCheckpointState: state, isLoading: false });
      return state;
    } catch (err) {
      console.error('Failed to fetch checkpoint state:', err);
      set({ remoteCheckpointState: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteBlackboard: async (serverId, runId, cycle) => {
    set({ isLoading: true });
    try {
      const blackboard = await deploymentApi.getRemoteBlackboardSummary(serverId, runId, cycle);
      set({ remoteBlackboard: blackboard, isLoading: false });
      return blackboard;
    } catch (err) {
      console.error('Failed to fetch blackboard:', err);
      set({ remoteBlackboard: null, isLoading: false });
      return null;
    }
  },
  
  fetchRemoteCompletedConcepts: async (serverId, runId, cycle) => {
    set({ isLoading: true });
    try {
      const concepts = await deploymentApi.getRemoteCompletedConcepts(serverId, runId, cycle);
      set({ remoteCompletedConcepts: concepts, isLoading: false });
      return concepts;
    } catch (err) {
      console.error('Failed to fetch completed concepts:', err);
      set({ remoteCompletedConcepts: null, isLoading: false });
      return null;
    }
  },
  
  resumeRemoteRun: async (serverId, runId, options = {}) => {
    set({ isLoading: true });
    try {
      const result = await deploymentApi.resumeRemoteRun(serverId, runId, options);
      
      useNotificationStore.getState().showSuccess(
        options.fork ? 'Run Forked' : 'Run Resumed',
        `${options.fork ? 'Forked' : 'Resumed'} run ${result.run_id.substring(0, 8)}... from cycle ${result.resumed_from.cycle}`,
        5000
      );
      
      // Refresh runs list
      get().fetchRemoteRuns(serverId);
      
      set({ isLoading: false });
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resume run';
      useNotificationStore.getState().showError('Resume Failed', message);
      set({ isLoading: false });
      return null;
    }
  },
  
  // =========================================================================
  // Remote Run Binding (Mirror to Local Canvas)
  // =========================================================================
  
  bindRemoteRun: async (serverId, runId, planId, planName) => {
    const { addNotification } = useNotificationStore.getState();
    
    try {
      await deploymentApi.bindRemoteRun(serverId, runId, planId, planName);
      
      addNotification({
        type: 'success',
        title: 'Remote Run Bound',
        message: `Now mirroring execution from ${planName || runId}`,
        duration: 4000,
      });
      
      // Refresh bound runs
      get().fetchBoundRuns();
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to bind remote run';
      addNotification({
        type: 'error',
        title: 'Bind Failed',
        message,
        duration: 6000,
      });
      return false;
    }
  },
  
  unbindRemoteRun: async (serverId, runId) => {
    const { addNotification } = useNotificationStore.getState();
    
    try {
      await deploymentApi.unbindRemoteRun(serverId, runId);
      
      addNotification({
        type: 'info',
        title: 'Remote Run Unbound',
        message: 'Stopped mirroring remote execution',
        duration: 3000,
      });
      
      // Refresh bound runs
      get().fetchBoundRuns();
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to unbind remote run';
      addNotification({
        type: 'error',
        title: 'Unbind Failed',
        message,
        duration: 6000,
      });
      return false;
    }
  },
  
  fetchBoundRuns: async () => {
    try {
      const result = await deploymentApi.listBoundRuns();
      set({ 
        boundRemoteRuns: result.bound_runs,
        activeBoundRunId: result.bound_runs.find(r => r.is_active)?.run_id || null,
      });
    } catch (err) {
      console.error('Failed to fetch bound runs:', err);
    }
  },
  
  // Reset store
  reset: () => {
    get().stopPolling();
    set({
      remotePlans: [],
      activeRuns: [],
      runResults: {},
      remotePlanGraphs: {},
      remoteCanvasGraphs: {},
      loadedRemoteGraph: null,
      boundRemoteRuns: [],
      activeBoundRunId: null,
      selectedRemoteRunId: null,
      remoteRunDbOverview: null,
      remoteRunExecutions: null,
      remoteRunStatistics: null,
      remoteRunCheckpoints: null,
      remoteCheckpointState: null,
      remoteBlackboard: null,
      remoteCompletedConcepts: null,
      isLoading: false,
      isDeploying: false,
      isBuilding: false,
      error: null,
      lastDeployResult: null,
      lastBuildResult: null,
    });
  },
}));

