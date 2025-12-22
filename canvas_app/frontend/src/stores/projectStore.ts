/**
 * Project state management with Zustand
 */
import { create } from 'zustand';
import type { ProjectConfig, RegisteredProject } from '../types/project';
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
    projectConfigFile: null,
    isLoaded: false,
    repositoriesExist: false,
    directoryProjects: [],
    isLoading: false,
    error: null,
  }),
}));
