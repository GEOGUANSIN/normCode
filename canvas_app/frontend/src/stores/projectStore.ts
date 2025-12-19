/**
 * Project state management with Zustand
 */
import { create } from 'zustand';
import type { ProjectConfig, RecentProject } from '../types/project';
import { projectApi, graphApi, executionApi } from '../services/api';
import { useGraphStore } from './graphStore';
import { useExecutionStore } from './executionStore';
import { useConfigStore } from './configStore';

interface ProjectState {
  // Current project state
  currentProject: ProjectConfig | null;
  projectPath: string | null;
  isLoaded: boolean;  // Whether repositories are loaded
  repositoriesExist: boolean;
  
  // Recent projects
  recentProjects: RecentProject[];
  
  // UI state
  isProjectPanelOpen: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentProject: (project: ProjectConfig | null, path: string | null) => void;
  setIsLoaded: (loaded: boolean) => void;
  setRepositoriesExist: (exist: boolean) => void;
  setRecentProjects: (projects: RecentProject[]) => void;
  setProjectPanelOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Async actions
  fetchCurrentProject: () => Promise<void>;
  fetchRecentProjects: () => Promise<void>;
  openProject: (projectPath: string) => Promise<boolean>;
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
  
  // Reset
  reset: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // Initial state
  currentProject: null,
  projectPath: null,
  isLoaded: false,
  repositoriesExist: false,
  recentProjects: [],
  isProjectPanelOpen: false,
  isLoading: false,
  error: null,
  
  // Simple setters
  setCurrentProject: (project, path) => set({ currentProject: project, projectPath: path }),
  setIsLoaded: (loaded) => set({ isLoaded: loaded }),
  setRepositoriesExist: (exist) => set({ repositoriesExist: exist }),
  setRecentProjects: (projects) => set({ recentProjects: projects }),
  setProjectPanelOpen: (open) => set({ isProjectPanelOpen: open }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  // Fetch current project from backend
  fetchCurrentProject: async () => {
    try {
      const response = await projectApi.getCurrent();
      if (response) {
        set({
          currentProject: response.config,
          projectPath: response.path,
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
          isLoaded: false,
          repositoriesExist: false,
        });
      }
    } catch (err) {
      console.error('Failed to fetch current project:', err);
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
  
  // Open an existing project
  openProject: async (projectPath: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectApi.open({ project_path: projectPath });
      set({
        currentProject: response.config,
        projectPath: response.path,
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
        isLoaded: false,
        repositoriesExist: false,
      });
    } catch (err) {
      console.error('Failed to close project:', err);
    }
  },
  
  // Load repositories for current project
  loadProjectRepositories: async () => {
    set({ isLoading: true, error: null });
    try {
      const result = await projectApi.loadRepositories();
      
      // Fetch graph data after loading repositories
      const graphData = await graphApi.get();
      
      // Update graph store
      useGraphStore.getState().setGraphData(graphData);
      
      // Update execution store with initial counts
      const executionStore = useExecutionStore.getState();
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
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load repositories';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Reset store
  reset: () => set({
    currentProject: null,
    projectPath: null,
    isLoaded: false,
    repositoriesExist: false,
    isLoading: false,
    error: null,
  }),
}));
