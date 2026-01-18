/**
 * Project-related type definitions
 */

export interface RepositoryPaths {
  concepts: string;
  inferences: string;
  inputs?: string;
}

export interface ExecutionSettings {
  max_cycles: number;
  db_path: string;
  agent_config?: string;  // Path to .agent.json file (agent tool configs)
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
  max_cycles?: number;
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

// =============================================================================
// Multi-Project (Tabs) Support
// =============================================================================

/**
 * Represents an open project instance (a tab).
 * Each open project has its own execution state.
 */
export interface OpenProjectInstance {
  id: string;  // Project ID (same as ProjectConfig.id)
  name: string;
  directory: string;
  config_file: string;
  config: ProjectConfig;
  is_loaded: boolean;  // Whether repositories are loaded
  repositories_exist: boolean;
  is_active: boolean;  // Whether this is the currently focused tab
  is_read_only: boolean;  // Read-only projects can be viewed and executed, but not modified
  
  // Remote project support
  is_remote?: boolean;  // Whether this is a remote project
  server_id?: string;  // Remote server ID (if is_remote)
  server_name?: string;  // Remote server name (if is_remote)
  server_url?: string;  // Remote server URL (if is_remote)
  plan_id?: string;  // Remote plan ID (if is_remote)
}

export interface OpenProjectsResponse {
  projects: OpenProjectInstance[];
  active_project_id: string | null;
}

export interface SwitchProjectRequest {
  project_id: string;
}

export interface CloseProjectRequest {
  project_id: string;
}

export interface OpenProjectInTabRequest {
  project_id?: string;  // Open by project ID
  project_path?: string;  // Or by path
  config_file?: string;  // Specific config file
  make_active?: boolean;  // Whether to switch to this tab
  is_read_only?: boolean;  // Read-only projects can be viewed and executed, but not modified
}

// =============================================================================
// Remote Project Tabs (for remote plans loaded from deployment servers)
// =============================================================================

/**
 * Represents a remote project tab (loaded from a deployment server).
 * These are view-only and managed client-side.
 */
export interface RemoteProjectTab {
  id: string;  // Format: "remote:{server_id}:{plan_id}" or "remote:{server_id}:{plan_id}:{run_id}"
  name: string;
  server_id: string;
  server_name: string;
  plan_id: string;
  plan_name: string;
  is_active: boolean;
  is_loaded: boolean;  // Always true for remote tabs once loaded
  node_count: number;
  edge_count: number;
  // Optional: bound to a running execution for live updates
  run_id?: string;
  is_bound?: boolean;  // true if receiving live updates via binding
  // Worker ID in the backend WorkerRegistry (for unified state management)
  worker_id?: string;
}