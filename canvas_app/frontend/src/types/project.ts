/**
 * Project-related type definitions
 */

export interface RepositoryPaths {
  concepts: string;
  inferences: string;
  inputs?: string;
}

export interface ExecutionSettings {
  llm_model: string;
  max_cycles: number;
  db_path: string;
  base_dir?: string;
  paradigm_dir?: string;
}

export interface ProjectConfig {
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  repositories: RepositoryPaths;
  execution: ExecutionSettings;
  breakpoints: string[];
  ui_preferences: Record<string, unknown>;
}

export interface RecentProject {
  path: string;
  name: string;
  last_opened: string;
}

export interface ProjectResponse {
  path: string;
  config: ProjectConfig;
  is_loaded: boolean;
  repositories_exist: boolean;
}

export interface RecentProjectsResponse {
  projects: RecentProject[];
}

export interface OpenProjectRequest {
  project_path: string;
}

export interface CreateProjectRequest {
  project_path: string;
  name: string;
  description?: string;
  concepts_path?: string;
  inferences_path?: string;
  inputs_path?: string;
  llm_model?: string;
  max_cycles?: number;
  paradigm_dir?: string;
}

export interface SaveProjectRequest {
  execution?: ExecutionSettings;
  breakpoints?: string[];
  ui_preferences?: Record<string, unknown>;
}
