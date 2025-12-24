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
  id: string;  // Unique project ID
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  repositories: RepositoryPaths;
  execution: ExecutionSettings;
  breakpoints: string[];
  ui_preferences: Record<string, unknown>;
}

/**
 * A registered project in the app's project registry.
 * Tracks all known projects (not just recent ones).
 */
export interface RegisteredProject {
  id: string;  // Unique project ID
  name: string;
  directory: string;  // Absolute path to project directory
  config_file: string;  // Filename of the config
  description?: string;
  created_at: string;
  last_opened?: string;
}

// Legacy type for backwards compatibility
export interface RecentProject {
  path: string;
  name: string;
  last_opened: string;
}

export interface ProjectResponse {
  id: string;  // Project ID
  path: string;  // Directory path
  config_file: string;  // Config filename
  config: ProjectConfig;
  is_loaded: boolean;
  repositories_exist: boolean;
}

export interface ProjectListResponse {
  projects: RegisteredProject[];
}

export interface DirectoryProjectsResponse {
  directory: string;
  projects: RegisteredProject[];
}

export interface RecentProjectsResponse {
  projects: RegisteredProject[];
}

export interface OpenProjectRequest {
  project_id?: string;  // Open by project ID
  project_path?: string;  // Path to directory
  config_file?: string;  // Specific config file
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

export interface ScanDirectoryRequest {
  directory: string;
  register?: boolean;
}

export interface DiscoverPathsRequest {
  directory: string;
}

export interface DiscoveredPathsResponse {
  directory: string;
  concepts: string | null;
  inferences: string | null;
  inputs: string | null;
  paradigm_dir: string | null;
  concepts_exists: boolean;
  inferences_exists: boolean;
  inputs_exists: boolean;
  paradigm_dir_exists: boolean;
}
