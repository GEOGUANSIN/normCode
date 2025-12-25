/**
 * Project state management with Zustand
 */
import { create } from 'zustand';
import type { ProjectConfig, RegisteredProject, OpenProjectInstance } from '../types/project';
import { projectApi, graphApi, executionApi } from '../services/api';
import { useGraphStore } from './graphStore';
import { useExecutionStore } from './executionStore';
import { useConfigStore } from './configStore';

interface ProjectState {
  // Current project state
  currentProject: ProjectConfig | null;
  projectPath: string | null;
  projectConfigFile: string | null;  // The config filename
  isLoaded: boolean;  // Whether repositories are loaded
  repositoriesExist: boolean;
  
  // Multi-project (tabs) state
  openTabs: OpenProjectInstance[];  // All open project tabs
  activeTabId: string | null;  // Currently active tab
  
  // All registered projects and recent projects
  allProjects: RegisteredProject[];
  recentProjects: RegisteredProject[];
  directoryProjects: RegisteredProject[];  // Projects in current directory
  
  // UI state
  isProjectPanelOpen: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentProject: (project: ProjectConfig | null, path: string | null, configFile: string | null) => void;
  setIsLoaded: (loaded: boolean) => void;
  setRepositoriesExist: (exist: boolean) => void;
  setAllProjects: (projects: RegisteredProject[]) => void;
  setRecentProjects: (projects: RegisteredProject[]) => void;
  setDirectoryProjects: (projects: RegisteredProject[]) => void;
  setProjectPanelOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Multi-project tab actions
  setOpenTabs: (tabs: OpenProjectInstance[]) => void;
  setActiveTabId: (tabId: string | null) => void;
  
  // Async actions
  fetchCurrentProject: () => Promise<void>;
  fetchAllProjects: () => Promise<void>;
  fetchRecentProjects: () => Promise<void>;
  fetchDirectoryProjects: (directory: string) => Promise<void>;
  scanDirectory: (directory: string, register?: boolean) => Promise<RegisteredProject[]>;
  openProject: (projectPath?: string, configFile?: string, projectId?: string) => Promise<boolean>;
  createProject: (
    projectPath: string,
    name: string,
    options?: {
      description?: string;
      conceptsPath?: string;
      inferencesPath?: string;
      inputsPath?: string;
      llmModel?: string;
      maxCycles?: number;
      paradigmDir?: string;
    }
  ) => Promise<boolean>;
  saveProject: () => Promise<boolean>;
  closeProject: () => Promise<void>;
  loadProjectRepositories: () => Promise<boolean>;
  removeProjectFromRegistry: (projectId: string) => Promise<void>;
  updateRepositories: (paths: { concepts?: string; inferences?: string; inputs?: string }) => Promise<boolean>;
  
  // Multi-project tab async actions
  fetchOpenTabs: () => Promise<void>;
  openProjectAsTab: (projectPath?: string, configFile?: string, projectId?: string, makeActive?: boolean, isReadOnly?: boolean) => Promise<boolean>;
  switchTab: (projectId: string) => Promise<boolean>;
  closeTab: (projectId: string) => Promise<void>;
  closeAllTabs: () => Promise<void>;
  
  // Reset
  reset: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // Initial state
  currentProject: null,
  projectPath: null,
  projectConfigFile: null,
  isLoaded: false,
  repositoriesExist: false,
  
  // Multi-project tabs initial state
  openTabs: [],
  activeTabId: null,
  
  allProjects: [],
  recentProjects: [],
  directoryProjects: [],
  isProjectPanelOpen: false,
  isLoading: false,
  error: null,
  
  // Simple setters
  setCurrentProject: (project, path, configFile) => set({ 
    currentProject: project, 
    projectPath: path,
    projectConfigFile: configFile,
  }),
  setIsLoaded: (loaded) => set({ isLoaded: loaded }),
  setRepositoriesExist: (exist) => set({ repositoriesExist: exist }),
  setAllProjects: (projects) => set({ allProjects: projects }),
  setRecentProjects: (projects) => set({ recentProjects: projects }),
  setDirectoryProjects: (projects) => set({ directoryProjects: projects }),
  setProjectPanelOpen: (open) => set({ isProjectPanelOpen: open }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  // Multi-project tab setters
  setOpenTabs: (tabs) => set({ openTabs: tabs }),
  setActiveTabId: (tabId) => set({ activeTabId: tabId }),
  
  // Fetch current project from backend
  fetchCurrentProject: async () => {
    try {
      const response = await projectApi.getCurrent();
      if (response) {
        set({
          currentProject: response.config,
          projectPath: response.path,
          projectConfigFile: response.config_file,
          isLoaded: response.is_loaded,
          repositoriesExist: response.repositories_exist,
        });
        // Sync execution settings to configStore
        const configStore = useConfigStore.getState();
        const exec = response.config.execution;
        configStore.setLlmModel(exec.llm_model);
        configStore.setMaxCycles(exec.max_cycles);
        configStore.setDbPath(exec.db_path);
        configStore.setBaseDir(exec.base_dir || '');
        configStore.setParadigmDir(exec.paradigm_dir || '');
      } else {
        set({
          currentProject: null,
          projectPath: null,
          projectConfigFile: null,
          isLoaded: false,
          repositoriesExist: false,
        });
      }
    } catch (err) {
      console.error('Failed to fetch current project:', err);
    }
  },
  
  // Fetch all registered projects
  fetchAllProjects: async () => {
    try {
      const response = await projectApi.getAll();
      set({ allProjects: response.projects });
    } catch (err) {
      console.error('Failed to fetch all projects:', err);
    }
  },
  
  // Fetch recent projects
  fetchRecentProjects: async () => {
    try {
      const response = await projectApi.getRecent();
      set({ recentProjects: response.projects });
    } catch (err) {
      console.error('Failed to fetch recent projects:', err);
    }
  },
  
  // Fetch projects in a specific directory
  fetchDirectoryProjects: async (directory: string) => {
    try {
      const response = await projectApi.getProjectsInDirectory(directory);
      set({ directoryProjects: response.projects });
    } catch (err) {
      console.error('Failed to fetch directory projects:', err);
      set({ directoryProjects: [] });
    }
  },
  
  // Scan directory for project configs
  scanDirectory: async (directory: string, register: boolean = true) => {
    try {
      const response = await projectApi.scanDirectory({ directory, register });
      // Also update directoryProjects
      set({ directoryProjects: response.projects });
      // Refresh all projects if we registered
      if (register) {
        get().fetchAllProjects();
      }
      return response.projects;
    } catch (err) {
      console.error('Failed to scan directory:', err);
      return [];
    }
  },
  
  // Open an existing project (by path, by path+config, or by ID)
  openProject: async (projectPath?: string, configFile?: string, projectId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectApi.open({ 
        project_path: projectPath,
        config_file: configFile,
        project_id: projectId,
      });
      set({
        currentProject: response.config,
        projectPath: response.path,
        projectConfigFile: response.config_file,
        isLoaded: response.is_loaded,
        repositoriesExist: response.repositories_exist,
        isLoading: false,
        isProjectPanelOpen: false,
      });
      // Sync execution settings to configStore
      const configStore = useConfigStore.getState();
      const exec = response.config.execution;
      configStore.setLlmModel(exec.llm_model);
      configStore.setMaxCycles(exec.max_cycles);
      configStore.setDbPath(exec.db_path);
      configStore.setBaseDir(exec.base_dir || '');
      configStore.setParadigmDir(exec.paradigm_dir || '');
      // Refresh recent projects
      get().fetchRecentProjects();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to open project';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Create a new project
  createProject: async (projectPath, name, options = {}) => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectApi.create({
        project_path: projectPath,
        name,
        description: options.description,
        concepts_path: options.conceptsPath,
        inferences_path: options.inferencesPath,
        inputs_path: options.inputsPath,
        llm_model: options.llmModel,
        max_cycles: options.maxCycles,
        paradigm_dir: options.paradigmDir,
      });
      set({
        currentProject: response.config,
        projectPath: response.path,
        projectConfigFile: response.config_file,
        isLoaded: response.is_loaded,
        repositoriesExist: response.repositories_exist,
        isLoading: false,
        isProjectPanelOpen: false,
      });
      // Sync execution settings to configStore
      const configStore = useConfigStore.getState();
      const exec = response.config.execution;
      configStore.setLlmModel(exec.llm_model);
      configStore.setMaxCycles(exec.max_cycles);
      configStore.setDbPath(exec.db_path);
      configStore.setBaseDir(exec.base_dir || '');
      configStore.setParadigmDir(exec.paradigm_dir || '');
      // Refresh projects lists
      get().fetchRecentProjects();
      get().fetchAllProjects();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create project';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Save current project
  saveProject: async () => {
    const { currentProject } = get();
    if (!currentProject) return false;
    
    set({ isLoading: true, error: null });
    try {
      const response = await projectApi.save({
        execution: currentProject.execution,
        breakpoints: currentProject.breakpoints,
        ui_preferences: currentProject.ui_preferences,
      });
      set({
        currentProject: response.config,
        isLoading: false,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save project';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Close current project
  closeProject: async () => {
    try {
      await projectApi.close();
      set({
        currentProject: null,
        projectPath: null,
        projectConfigFile: null,
        isLoaded: false,
        repositoriesExist: false,
      });
    } catch (err) {
      console.error('Failed to close project:', err);
    }
  },
  
  // Remove a project from the registry
  removeProjectFromRegistry: async (projectId: string) => {
    try {
      await projectApi.removeFromRegistry(projectId);
      // Refresh project lists
      get().fetchAllProjects();
      get().fetchRecentProjects();
    } catch (err) {
      console.error('Failed to remove project from registry:', err);
    }
  },
  
  // Update repository paths
  updateRepositories: async (paths: { concepts?: string; inferences?: string; inputs?: string }) => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectApi.updateRepositories(paths);
      set({
        currentProject: response.config,
        repositoriesExist: response.repositories_exist,
        isLoading: false,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update repository paths';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Load repositories for current project (also serves as reload)
  loadProjectRepositories: async () => {
    set({ isLoading: true, error: null });
    try {
      // Reset execution state before loading (clean slate for reload)
      const executionStore = useExecutionStore.getState();
      executionStore.reset();
      
      const result = await projectApi.loadRepositories();
      
      // Fetch graph data after loading repositories
      const graphData = await graphApi.get();
      
      // Update graph store
      useGraphStore.getState().setGraphData(graphData);
      
      // Update execution store with initial counts
      executionStore.setProgress(0, graphData.nodes.filter(n => n.flow_index).length);
      
      // Fetch and sync breakpoints from backend
      try {
        const breakpointsResponse = await executionApi.getBreakpoints();
        // Clear existing breakpoints first, then add new ones
        const currentBreakpoints = executionStore.breakpoints;
        currentBreakpoints.forEach(bp => executionStore.removeBreakpoint(bp));
        breakpointsResponse.breakpoints.forEach(bp => executionStore.addBreakpoint(bp));
        console.log(`Synced ${breakpointsResponse.breakpoints.length} breakpoints from backend`);
      } catch (bpErr) {
        console.warn('Failed to fetch breakpoints:', bpErr);
      }
      
      set({ isLoaded: true, isLoading: false });
      
      // Update the loaded state in the open tabs if using tabs
      const { activeTabId, openTabs } = get();
      if (activeTabId) {
        const updatedTabs = openTabs.map(tab => 
          tab.id === activeTabId ? { ...tab, is_loaded: true } : tab
        );
        set({ openTabs: updatedTabs });
      }
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load repositories';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // ==========================================================================
  // Multi-project tab async actions
  // ==========================================================================
  
  // Fetch all open tabs from backend
  fetchOpenTabs: async () => {
    try {
      const response = await projectApi.getOpenTabs();
      set({
        openTabs: response.projects,
        activeTabId: response.active_project_id,
      });
      
      // If there's an active tab, sync its config to current project state
      const activeTab = response.projects.find(t => t.id === response.active_project_id);
      if (activeTab) {
        set({
          currentProject: activeTab.config,
          projectPath: activeTab.directory,
          projectConfigFile: activeTab.config_file,
          isLoaded: activeTab.is_loaded,
          repositoriesExist: activeTab.repositories_exist,
        });
        // Sync execution settings
        const configStore = useConfigStore.getState();
        const exec = activeTab.config.execution;
        configStore.setLlmModel(exec.llm_model);
        configStore.setMaxCycles(exec.max_cycles);
        configStore.setDbPath(exec.db_path);
        configStore.setBaseDir(exec.base_dir || '');
        configStore.setParadigmDir(exec.paradigm_dir || '');
      }
    } catch (err) {
      console.error('Failed to fetch open tabs:', err);
    }
  },
  
  // Open a project as a new tab
  openProjectAsTab: async (projectPath?: string, configFile?: string, projectId?: string, makeActive: boolean = true, isReadOnly: boolean = false) => {
    set({ isLoading: true, error: null });
    try {
      const instance = await projectApi.openAsTab({
        project_path: projectPath,
        config_file: configFile,
        project_id: projectId,
        make_active: makeActive,
        is_read_only: isReadOnly,
      });
      
      // IMPORTANT: Fetch the full tabs list from backend instead of locally managing it.
      // This ensures we get ALL tabs including any that were retroactively added
      // (e.g., when the first project was opened via openProject, not openProjectAsTab).
      const tabsResponse = await projectApi.getOpenTabs();
      
      set({
        openTabs: tabsResponse.projects,
        activeTabId: tabsResponse.active_project_id,
        isLoading: false,
        isProjectPanelOpen: false,
      });
      
      // If making active, update current project state
      if (makeActive) {
        set({
          currentProject: instance.config,
          projectPath: instance.directory,
          projectConfigFile: instance.config_file,
          isLoaded: instance.is_loaded,
          repositoriesExist: instance.repositories_exist,
        });
        // Sync execution settings
        const configStore = useConfigStore.getState();
        const exec = instance.config.execution;
        configStore.setLlmModel(exec.llm_model);
        configStore.setMaxCycles(exec.max_cycles);
        configStore.setDbPath(exec.db_path);
        configStore.setBaseDir(exec.base_dir || '');
        configStore.setParadigmDir(exec.paradigm_dir || '');
      }
      
      // Refresh recent projects
      get().fetchRecentProjects();
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to open project as tab';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Switch to a different tab
  switchTab: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const instance = await projectApi.switchTab({ project_id: projectId });
      
      // Update tabs state
      const { openTabs } = get();
      const updatedTabs = openTabs.map(t => ({
        ...t,
        is_active: t.id === projectId,
      }));
      
      set({
        openTabs: updatedTabs,
        activeTabId: projectId,
        currentProject: instance.config,
        projectPath: instance.directory,
        projectConfigFile: instance.config_file,
        isLoaded: instance.is_loaded,
        repositoriesExist: instance.repositories_exist,
        isLoading: false,
      });
      
      // Sync execution settings
      const configStore = useConfigStore.getState();
      const exec = instance.config.execution;
      configStore.setLlmModel(exec.llm_model);
      configStore.setMaxCycles(exec.max_cycles);
      configStore.setDbPath(exec.db_path);
      configStore.setBaseDir(exec.base_dir || '');
      configStore.setParadigmDir(exec.paradigm_dir || '');
      
      // If the project was loaded, we need to reload the graph and sync execution state
      // Each project has its own ExecutionController on the backend, so we just need
      // to reload the graph (graph_service is shared) and sync the execution state
      if (instance.is_loaded) {
        // Reset execution state first
        const executionStore = useExecutionStore.getState();
        executionStore.reset();
        
        try {
          // Reload graph from the current project's files
          const graphData = await graphApi.reload();
          useGraphStore.getState().setGraphData(graphData);
          
          // Update execution store with initial counts
          executionStore.setProgress(0, graphData.nodes.filter(n => n.flow_index).length);
          
          // Fetch and sync breakpoints from backend (from the project's controller)
          try {
            const breakpointsResponse = await executionApi.getBreakpoints();
            breakpointsResponse.breakpoints.forEach(bp => executionStore.addBreakpoint(bp));
            console.log(`Tab switch: synced ${breakpointsResponse.breakpoints.length} breakpoints`);
          } catch (bpErr) {
            console.warn('Failed to fetch breakpoints for switched tab:', bpErr);
          }
          
          // Sync execution state from the project's controller
          try {
            const execState = await executionApi.getState();
            executionStore.setStatus(execState.status);
            if (execState.node_statuses) {
              executionStore.setNodeStatuses(execState.node_statuses);
            }
          } catch (stateErr) {
            console.warn('Failed to sync execution state for switched tab:', stateErr);
          }
        } catch (graphErr) {
          console.warn('Failed to reload graph for switched tab:', graphErr);
        }
      } else {
        // Clear graph if not loaded
        useGraphStore.getState().reset();
        useExecutionStore.getState().reset();
      }
      
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to switch tab';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Close a tab
  closeTab: async (projectId: string) => {
    try {
      const response = await projectApi.closeTab({ project_id: projectId });
      
      set({
        openTabs: response.projects,
        activeTabId: response.active_project_id,
      });
      
      // If there's still an active project, update current state
      const activeTab = response.projects.find(t => t.id === response.active_project_id);
      if (activeTab) {
        set({
          currentProject: activeTab.config,
          projectPath: activeTab.directory,
          projectConfigFile: activeTab.config_file,
          isLoaded: activeTab.is_loaded,
          repositoriesExist: activeTab.repositories_exist,
        });
        
        // Sync execution settings
        const configStore = useConfigStore.getState();
        const exec = activeTab.config.execution;
        configStore.setLlmModel(exec.llm_model);
        configStore.setMaxCycles(exec.max_cycles);
        configStore.setDbPath(exec.db_path);
        configStore.setBaseDir(exec.base_dir || '');
        configStore.setParadigmDir(exec.paradigm_dir || '');
        
        // If the new active tab was loaded, reload graph and execution state
        if (activeTab.is_loaded) {
          // Reset execution state first
          const executionStore = useExecutionStore.getState();
          executionStore.reset();
          
          try {
            // Reload graph from the new active project's files
            const graphData = await graphApi.reload();
            useGraphStore.getState().setGraphData(graphData);
            
            // Update execution store with initial counts
            executionStore.setProgress(0, graphData.nodes.filter(n => n.flow_index).length);
            
            // Fetch and sync breakpoints from backend
            try {
              const breakpointsResponse = await executionApi.getBreakpoints();
              breakpointsResponse.breakpoints.forEach(bp => executionStore.addBreakpoint(bp));
              console.log(`Tab close: synced ${breakpointsResponse.breakpoints.length} breakpoints`);
            } catch (bpErr) {
              console.warn('Failed to fetch breakpoints for new active tab:', bpErr);
            }
            
            // Sync execution state from the project's controller
            try {
              const execState = await executionApi.getState();
              executionStore.setStatus(execState.status);
              if (execState.node_statuses) {
                executionStore.setNodeStatuses(execState.node_statuses);
              }
            } catch (stateErr) {
              console.warn('Failed to sync execution state for new active tab:', stateErr);
            }
          } catch (graphErr) {
            console.warn('Failed to reload graph for new active tab:', graphErr);
          }
        } else {
          // New active tab is not loaded, clear state
          useGraphStore.getState().reset();
          useExecutionStore.getState().reset();
        }
      } else {
        // No more tabs - reset state
        set({
          currentProject: null,
          projectPath: null,
          projectConfigFile: null,
          isLoaded: false,
          repositoriesExist: false,
        });
        useGraphStore.getState().reset();
        useExecutionStore.getState().reset();
      }
    } catch (err) {
      console.error('Failed to close tab:', err);
    }
  },
  
  // Close all tabs
  closeAllTabs: async () => {
    try {
      await projectApi.closeAllTabs();
      set({
        openTabs: [],
        activeTabId: null,
        currentProject: null,
        projectPath: null,
        projectConfigFile: null,
        isLoaded: false,
        repositoriesExist: false,
      });
      useGraphStore.getState().reset();
      useExecutionStore.getState().reset();
    } catch (err) {
      console.error('Failed to close all tabs:', err);
    }
  },
  
  // Reset store
  reset: () => set({
    currentProject: null,
    projectPath: null,
    projectConfigFile: null,
    isLoaded: false,
    repositoriesExist: false,
    openTabs: [],
    activeTabId: null,
    directoryProjects: [],
    isLoading: false,
    error: null,
  }),
}));
