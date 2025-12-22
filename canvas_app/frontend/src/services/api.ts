/**
 * REST API client for NormCode Canvas backend
 */

import type { GraphData, GraphNode, GraphStats } from '../types/graph';
import type { 
  ExecutionState, 
  LoadRepositoryRequest, 
  LoadResponse, 
  CommandResponse,
  RepositoryExample,
  ExecutionConfig,
  RunInfo,
  CheckpointInfo,
  ResumeRequest,
  ForkRequest,
  CheckpointLoadResult,
} from '../types/execution';
import type {
  ProjectResponse,
  ProjectListResponse,
  DirectoryProjectsResponse,
  RecentProjectsResponse,
  OpenProjectRequest,
  CreateProjectRequest,
  SaveProjectRequest,
  ScanDirectoryRequest,
  ExecutionSettings,
} from '../types/project';

const API_BASE = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }
  
  return response.json();
}

// Repository endpoints
export const repositoryApi = {
  load: (request: LoadRepositoryRequest): Promise<LoadResponse> =>
    fetchJson(`${API_BASE}/repositories/load`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  getExamples: (): Promise<{ examples: RepositoryExample[] }> =>
    fetchJson(`${API_BASE}/repositories/examples`),
};

// Graph endpoints
export const graphApi = {
  get: (): Promise<GraphData> =>
    fetchJson(`${API_BASE}/graph`),
  
  getNode: (nodeId: string): Promise<GraphNode> =>
    fetchJson(`${API_BASE}/graph/node/${encodeURIComponent(nodeId)}`),
  
  getNodeData: (nodeId: string): Promise<{ node: GraphNode; concept: unknown }> =>
    fetchJson(`${API_BASE}/graph/node/${encodeURIComponent(nodeId)}/data`),
  
  getStats: (): Promise<GraphStats> =>
    fetchJson(`${API_BASE}/graph/stats`),
};

// Execution endpoints
export const executionApi = {
  getState: (): Promise<ExecutionState> =>
    fetchJson(`${API_BASE}/execution/state`),
  
  start: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/start`, { method: 'POST' }),
  
  pause: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/pause`, { method: 'POST' }),
  
  resume: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/resume`, { method: 'POST' }),
  
  step: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/step`, { method: 'POST' }),
  
  stop: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/stop`, { method: 'POST' }),
  
  restart: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/restart`, { method: 'POST' }),
  
  runTo: (flowIndex: string): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/run-to/${encodeURIComponent(flowIndex)}`, { method: 'POST' }),
  
  setBreakpoint: (flowIndex: string, enabled: boolean = true): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/breakpoints`, {
      method: 'POST',
      body: JSON.stringify({ flow_index: flowIndex, enabled }),
    }),
  
  clearBreakpoint: (flowIndex: string): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/breakpoints/${encodeURIComponent(flowIndex)}`, {
      method: 'DELETE',
    }),
  
  getBreakpoints: (): Promise<{ breakpoints: string[] }> =>
    fetchJson(`${API_BASE}/execution/breakpoints`),
  
  getConfig: (): Promise<ExecutionConfig> =>
    fetchJson(`${API_BASE}/execution/config`),
  
  getReference: (conceptName: string): Promise<ReferenceData> =>
    fetchJson(`${API_BASE}/execution/reference/${encodeURIComponent(conceptName)}`),
  
  getAllReferences: (): Promise<Record<string, ReferenceData>> =>
    fetchJson(`${API_BASE}/execution/references`),
  
  setVerboseLogging: (enabled: boolean): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/verbose-logging`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
  
  getStepProgress: (flowIndex?: string): Promise<StepProgressResponse> =>
    fetchJson(`${API_BASE}/execution/step-progress${flowIndex ? `?flow_index=${encodeURIComponent(flowIndex)}` : ''}`),
  
  // Phase 4: Modification & Re-run endpoints
  overrideValue: (conceptName: string, newValue: unknown, rerunDependents: boolean = false): Promise<ValueOverrideResponse> =>
    fetchJson(`${API_BASE}/execution/override/${encodeURIComponent(conceptName)}`, {
      method: 'POST',
      body: JSON.stringify({ new_value: newValue, rerun_dependents: rerunDependents }),
    }),
  
  rerunFrom: (flowIndex: string): Promise<RerunFromResponse> =>
    fetchJson(`${API_BASE}/execution/rerun-from/${encodeURIComponent(flowIndex)}`, { method: 'POST' }),
  
  modifyFunction: (flowIndex: string, modifications: FunctionModifyRequest): Promise<FunctionModifyResponse> =>
    fetchJson(`${API_BASE}/execution/modify-function/${encodeURIComponent(flowIndex)}`, {
      method: 'POST',
      body: JSON.stringify(modifications),
    }),
  
  getDependents: (conceptName: string): Promise<DependentsResponse> =>
    fetchJson(`${API_BASE}/execution/dependents/${encodeURIComponent(conceptName)}`),
  
  getDescendants: (flowIndex: string): Promise<DescendantsResponse> =>
    fetchJson(`${API_BASE}/execution/descendants/${encodeURIComponent(flowIndex)}`),
};

// Step progress response type
export interface StepProgressResponse {
  flow_index: string | null;
  sequence_type: string | null;
  current_step: string | null;
  current_step_index: number;
  total_steps: number;
  steps: string[];
  completed_steps: string[];
}

// Reference data type
export interface ReferenceData {
  concept_name: string;
  has_reference: boolean;
  data: unknown;
  axes: string[];
  shape: number[];
}

// Phase 4: Modification response types
export interface ValueOverrideResponse {
  success: boolean;
  overridden: string;
  stale_nodes: string[];
}

export interface RerunFromResponse {
  success: boolean;
  from_flow_index: string;
  reset_count: number;
  reset_nodes: string[];
}

export interface FunctionModifyRequest {
  paradigm?: string;
  prompt_location?: string;
  output_type?: string;
  retry?: boolean;
}

export interface FunctionModifyResponse {
  success: boolean;
  flow_index: string;
  modified_fields: string[];
}

export interface DependentsResponse {
  concept_name: string;
  dependents: string[];
  count: number;
}

export interface DescendantsResponse {
  flow_index: string;
  descendants: string[];
  count: number;
}

// Project endpoints
export const projectApi = {
  getCurrent: (): Promise<ProjectResponse | null> =>
    fetchJson(`${API_BASE}/project/current`),
  
  open: (request: OpenProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/open`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  create: (request: CreateProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/create`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  save: (request: SaveProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/save`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  close: (): Promise<{ status: string }> =>
    fetchJson(`${API_BASE}/project/close`, { method: 'POST' }),
  
  // Project registry endpoints
  getAll: (): Promise<ProjectListResponse> =>
    fetchJson(`${API_BASE}/project/all`),
  
  getRecent: (limit: number = 10): Promise<RecentProjectsResponse> =>
    fetchJson(`${API_BASE}/project/recent?limit=${limit}`),
  
  getProjectsInDirectory: (directory: string): Promise<DirectoryProjectsResponse> =>
    fetchJson(`${API_BASE}/project/directory?directory=${encodeURIComponent(directory)}`),
  
  scanDirectory: (request: ScanDirectoryRequest): Promise<DirectoryProjectsResponse> =>
    fetchJson(`${API_BASE}/project/scan`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  removeFromRegistry: (projectId: string): Promise<{ status: string; project_id: string }> =>
    fetchJson(`${API_BASE}/project/registry/${encodeURIComponent(projectId)}`, {
      method: 'DELETE',
    }),
  
  clearRegistry: (): Promise<{ status: string }> =>
    fetchJson(`${API_BASE}/project/registry`, { method: 'DELETE' }),
  
  loadRepositories: (): Promise<{ status: string; concepts_path: string; inferences_path: string; breakpoints_restored: number }> =>
    fetchJson(`${API_BASE}/project/load-repositories`, { method: 'POST' }),
  
  getPaths: (): Promise<{ concepts: string; inferences: string; inputs?: string; base_dir: string }> =>
    fetchJson(`${API_BASE}/project/paths`),
  
  updateSettings: (settings: ExecutionSettings): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};

// Agent endpoints
export interface AgentConfigApi {
  id: string;
  name: string;
  description: string;
  llm_model: string;
  file_system_enabled: boolean;
  file_system_base_dir?: string;
  python_interpreter_enabled: boolean;
  python_interpreter_timeout: number;
  user_input_enabled: boolean;
  user_input_mode: 'blocking' | 'async' | 'disabled';
  paradigm_dir?: string;
}

export interface MappingRuleApi {
  match_type: 'flow_index' | 'concept_name' | 'sequence_type';
  pattern: string;
  agent_id: string;
  priority: number;
}

export interface MappingStateApi {
  rules: MappingRuleApi[];
  explicit: Record<string, string>;
  default_agent: string;
}

export interface ToolCallEventApi {
  id: string;
  timestamp: string;
  flow_index: string;
  agent_id: string;
  tool_name: string;
  method: string;
  inputs: Record<string, unknown>;
  outputs?: unknown;
  duration_ms?: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}

export const agentApi = {
  // Agent CRUD
  listAgents: (): Promise<AgentConfigApi[]> =>
    fetchJson(`${API_BASE}/agents/`),
  
  getAgent: (agentId: string): Promise<AgentConfigApi> =>
    fetchJson(`${API_BASE}/agents/${encodeURIComponent(agentId)}`),
  
  createOrUpdateAgent: (config: AgentConfigApi): Promise<AgentConfigApi> =>
    fetchJson(`${API_BASE}/agents/`, {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  
  deleteAgent: (agentId: string): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/${encodeURIComponent(agentId)}`, {
      method: 'DELETE',
    }),
  
  // Mapping endpoints
  getMappingState: (): Promise<MappingStateApi> =>
    fetchJson(`${API_BASE}/agents/mappings/state`),
  
  addMappingRule: (rule: MappingRuleApi): Promise<{ success: boolean; rule: MappingRuleApi }> =>
    fetchJson(`${API_BASE}/agents/mappings/rules`, {
      method: 'POST',
      body: JSON.stringify(rule),
    }),
  
  removeMappingRule: (index: number): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/rules/${index}`, {
      method: 'DELETE',
    }),
  
  clearAllRules: (): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/rules`, {
      method: 'DELETE',
    }),
  
  setExplicitMapping: (flowIndex: string, agentId: string): Promise<{ success: boolean; flow_index: string; agent_id: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/explicit/${encodeURIComponent(flowIndex)}`, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId }),
    }),
  
  clearExplicitMapping: (flowIndex: string): Promise<{ success: boolean; flow_index: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/explicit/${encodeURIComponent(flowIndex)}`, {
      method: 'DELETE',
    }),
  
  clearAllExplicitMappings: (): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/explicit`, {
      method: 'DELETE',
    }),
  
  resolveAgentForInference: (flowIndex: string, conceptName?: string, sequenceType?: string): Promise<{ flow_index: string; agent_id: string; reason: string }> => {
    const params = new URLSearchParams();
    if (conceptName) params.set('concept_name', conceptName);
    if (sequenceType) params.set('sequence_type', sequenceType);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`${API_BASE}/agents/mappings/resolve/${encodeURIComponent(flowIndex)}${queryString}`);
  },
  
  setDefaultAgent: (agentId: string): Promise<{ success: boolean; default_agent: string }> =>
    fetchJson(`${API_BASE}/agents/mappings/default?agent_id=${encodeURIComponent(agentId)}`, {
      method: 'PUT',
    }),
  
  // Tool call history
  getToolCalls: (limit = 100): Promise<ToolCallEventApi[]> =>
    fetchJson(`${API_BASE}/agents/tool-calls?limit=${limit}`),
  
  clearToolCalls: (): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/tool-calls`, {
      method: 'DELETE',
    }),
  
  // Utility
  invalidateBodies: (): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/agents/invalidate-bodies`, {
      method: 'POST',
    }),
};

// Checkpoint endpoints
export const checkpointApi = {
  listRuns: (dbPath: string): Promise<RunInfo[]> =>
    fetchJson(`${API_BASE}/checkpoints/runs?db_path=${encodeURIComponent(dbPath)}`),
  
  listCheckpoints: (runId: string, dbPath: string): Promise<CheckpointInfo[]> =>
    fetchJson(`${API_BASE}/checkpoints/runs/${encodeURIComponent(runId)}/checkpoints?db_path=${encodeURIComponent(dbPath)}`),
  
  getRunMetadata: (runId: string, dbPath: string): Promise<Record<string, unknown>> =>
    fetchJson(`${API_BASE}/checkpoints/runs/${encodeURIComponent(runId)}/metadata?db_path=${encodeURIComponent(dbPath)}`),
  
  resume: (request: ResumeRequest): Promise<CheckpointLoadResult> =>
    fetchJson(`${API_BASE}/checkpoints/resume`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  fork: (request: ForkRequest): Promise<CheckpointLoadResult> =>
    fetchJson(`${API_BASE}/checkpoints/fork`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  checkDbExists: (dbPath: string): Promise<{ exists: boolean; path: string }> =>
    fetchJson(`${API_BASE}/checkpoints/db-exists?db_path=${encodeURIComponent(dbPath)}`),

  deleteRun: (runId: string, dbPath: string): Promise<{ success: boolean; message: string }> =>
    fetchJson(`${API_BASE}/checkpoints/runs/${encodeURIComponent(runId)}?db_path=${encodeURIComponent(dbPath)}`, {
      method: 'DELETE',
    }),
};

export { ApiError };
