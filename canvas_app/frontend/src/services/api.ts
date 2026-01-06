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
  DiscoverPathsRequest,
  DiscoveredPathsResponse,
  // Multi-project (tabs) support
  OpenProjectInstance,
  OpenProjectsResponse,
  SwitchProjectRequest,
  CloseProjectRequest,
  OpenProjectInTabRequest,
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
  
  /**
   * Reload the graph for the current project FROM DISK.
   * DEPRECATED: Use swap() for tab switching instead.
   * Only use reload() when files have actually changed on disk.
   */
  reload: (): Promise<GraphData> =>
    fetchJson(`${API_BASE}/graph/reload`, { method: 'POST' }),
  
  /**
   * Swap to the cached graph for a specific project.
   * This uses cached data from the ExecutionController instead of
   * re-reading from disk, making tab switching much faster.
   */
  swap: (projectId: string): Promise<GraphData> =>
    fetchJson(`${API_BASE}/graph/swap/${encodeURIComponent(projectId)}`, { method: 'POST' }),
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
  
  // Iteration history - get past values from loop iterations
  getReferenceHistory: (conceptName: string, limit: number = 50): Promise<IterationHistoryResponse> =>
    fetchJson(`${API_BASE}/execution/reference/${encodeURIComponent(conceptName)}/history?limit=${limit}`),
  
  getFlowHistory: (flowIndex: string, limit: number = 50): Promise<IterationHistoryResponse> =>
    fetchJson(`${API_BASE}/execution/flow/${encodeURIComponent(flowIndex)}/history?limit=${limit}`),
  
  // Worker-specific iteration history (for chat controller, etc.)
  getWorkerReferenceHistory: (workerId: string, conceptName: string, limit: number = 50): Promise<IterationHistoryResponse> =>
    fetchJson(`${API_BASE}/execution/workers/${encodeURIComponent(workerId)}/reference/${encodeURIComponent(conceptName)}/history?limit=${limit}`),
  
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

  // User input (human-in-the-loop) endpoints
  getPendingUserInputs: (): Promise<UserInputsResponse> =>
    fetchJson(`${API_BASE}/execution/user-input/pending`),

  submitUserInput: (requestId: string, response: unknown): Promise<UserInputSubmitResponse> =>
    fetchJson(`${API_BASE}/execution/user-input/${encodeURIComponent(requestId)}/submit`, {
      method: 'POST',
      body: JSON.stringify({ response }),
    }),

  cancelUserInput: (requestId: string): Promise<UserInputSubmitResponse> =>
    fetchJson(`${API_BASE}/execution/user-input/${encodeURIComponent(requestId)}/cancel`, {
      method: 'POST',
    }),
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

// Iteration history types - for viewing past loop iteration values
export interface IterationHistoryEntry {
  iteration_index: number;
  cycle_number: number;
  flow_index?: string;
  concept_name?: string;
  data: unknown;
  axes: string[];
  shape: number[];
  timestamp: number;
  has_data: boolean;
}

export interface IterationHistoryResponse {
  concept_name?: string;
  flow_index?: string;
  run_id: string | null;
  history: IterationHistoryEntry[];
  total_iterations: number;
  message?: string;
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

// User input types
export interface UserInputsResponse {
  requests: {
    request_id: string;
    prompt: string;
    interaction_type: string;
    options?: Record<string, unknown>;
    created_at?: number;
  }[];
  count: number;
}

export interface UserInputSubmitResponse {
  success: boolean;
  request_id: string;
  message: string;
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
  
  discoverPaths: (request: DiscoverPathsRequest): Promise<DiscoveredPathsResponse> =>
    fetchJson(`${API_BASE}/project/discover`, {
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
  
  updateRepositories: (paths: { concepts?: string; inferences?: string; inputs?: string }): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/repositories`, {
      method: 'PUT',
      body: JSON.stringify(paths),
    }),
  
  // Multi-project (tabs) endpoints
  getOpenTabs: (): Promise<OpenProjectsResponse> =>
    fetchJson(`${API_BASE}/project/tabs`),
  
  openAsTab: (request: OpenProjectInTabRequest): Promise<OpenProjectInstance> =>
    fetchJson(`${API_BASE}/project/tabs/open`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  switchTab: (request: SwitchProjectRequest): Promise<OpenProjectInstance> =>
    fetchJson(`${API_BASE}/project/tabs/switch`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  closeTab: (request: CloseProjectRequest): Promise<OpenProjectsResponse> =>
    fetchJson(`${API_BASE}/project/tabs/close`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  closeAllTabs: (): Promise<{ status: string; message: string }> =>
    fetchJson(`${API_BASE}/project/tabs/close-all`, { method: 'POST' }),
  
  getActiveTab: (): Promise<OpenProjectInstance | null> =>
    fetchJson(`${API_BASE}/project/tabs/active`),
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

// ============================================================================
// Chat API - Controller-driven chat interface
// ============================================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'compiler' | 'controller';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

// Controller info (available chat controllers)
export interface ControllerInfo {
  project_id: string;
  name: string;
  path: string;
  config_file?: string;
  description?: string;
  is_builtin: boolean;
}

export interface ControllersListResponse {
  controllers: ControllerInfo[];
  current_controller_id: string | null;
}

// Controller state
export interface ControllerState {
  controller_id: string | null;
  controller_name: string | null;
  controller_path: string | null;
  status: 'disconnected' | 'connecting' | 'connected' | 'running' | 'paused' | 'error';
  current_flow_index: string | null;
  error_message: string | null;
  pending_input: {
    id: string;
    prompt: string;
    input_type: 'text' | 'code' | 'confirm' | 'select';
    options?: string[];
    placeholder?: string;
  } | null;
  is_execution_active: boolean;
}

// Backward compatibility alias
export interface CompilerState {
  compiler: {
    project_id: string | null;
    project_name: string;
    status: 'disconnected' | 'connecting' | 'connected' | 'running' | 'error';
    is_loaded: boolean;
    is_read_only: boolean;
    current_step: string | null;
    error_message: string | null;
  };
  pending_input: {
    id: string;
    prompt: string;
    input_type: 'text' | 'code' | 'confirm' | 'select';
    options?: string[];
    placeholder?: string;
  } | null;
}

export interface SendMessageResponse {
  success: boolean;
  message_id?: string;
  error?: string;
}

export interface GetMessagesResponse {
  messages: ChatMessage[];
  has_more: boolean;
  total_count: number;
}

export interface StartControllerResponse {
  success: boolean;
  controller_id?: string;
  controller_name?: string;
  controller_path?: string;
  status: 'disconnected' | 'connecting' | 'connected' | 'running' | 'paused' | 'error';
  error?: string;
}

// Backward compatibility alias
export interface StartCompilerResponse {
  success: boolean;
  project_id?: string;
  project_path?: string;
  project_config_file?: string;
  status: 'disconnected' | 'connecting' | 'connected' | 'running' | 'error';
  error?: string;
}

export interface ChatBufferResponse {
  success: boolean;
  buffer_full?: boolean;
  delivered?: boolean;
  buffered_message?: string;
  reason?: string;
}

export interface ChatBufferStatus {
  execution_active: boolean;
  has_pending_request: boolean;
  has_buffered_message: boolean;
  buffered_message: string | null;
}

export const chatApi = {
  // =========================================================================
  // Controller Management (NEW)
  // =========================================================================
  
  /**
   * List all available chat controller projects.
   */
  listControllers: (refresh = false): Promise<ControllersListResponse> =>
    fetchJson(`${API_BASE}/chat/controllers?refresh=${refresh}`),
  
  /**
   * Select a chat controller project.
   */
  selectController: (controllerId: string): Promise<ControllerState> =>
    fetchJson(`${API_BASE}/chat/controllers/select`, {
      method: 'POST',
      body: JSON.stringify({ controller_id: controllerId }),
    }),
  
  /**
   * Get the current controller state.
   */
  getControllerState: (): Promise<ControllerState> =>
    fetchJson(`${API_BASE}/chat/state`),
  
  /**
   * Start the chat controller.
   */
  startController: (autoRun = true): Promise<StartControllerResponse> =>
    fetchJson(`${API_BASE}/chat/start`, {
      method: 'POST',
      body: JSON.stringify({ auto_run: autoRun }),
    }),
  
  /**
   * Pause the controller execution.
   */
  pauseController: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/pause`, { method: 'POST' }),
  
  /**
   * Resume paused controller execution.
   */
  resumeController: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/resume`, { method: 'POST' }),
  
  /**
   * Stop the controller execution (but keep it connected).
   */
  stopController: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/stop`, { method: 'POST' }),
  
  /**
   * Disconnect the controller completely.
   */
  disconnectController: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/disconnect`, { method: 'POST' }),
  
  // =========================================================================
  // Backward Compatibility Aliases
  // =========================================================================
  
  getState: (): Promise<ControllerState> =>
    fetchJson(`${API_BASE}/chat/state`),
  
  startCompiler: (autoRun = true): Promise<StartCompilerResponse> =>
    fetchJson(`${API_BASE}/chat/start`, {
      method: 'POST',
      body: JSON.stringify({ auto_run: autoRun }),
    }),
  
  stopCompiler: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/stop`, { method: 'POST' }),
  
  disconnectCompiler: (): Promise<{ success: boolean; status: string }> =>
    fetchJson(`${API_BASE}/chat/disconnect`, { method: 'POST' }),
  
  // =========================================================================
  // Messages
  // =========================================================================
  
  /**
   * Get chat message history.
   */
  getMessages: (limit = 100, offset = 0): Promise<GetMessagesResponse> =>
    fetchJson(`${API_BASE}/chat/messages?limit=${limit}&offset=${offset}`),
  
  /**
   * Send a message to the controller.
   * This is the main endpoint for user chat input.
   */
  sendMessage: (content: string, metadata?: Record<string, unknown>): Promise<SendMessageResponse> =>
    fetchJson(`${API_BASE}/chat/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, metadata }),
    }),
  
  /**
   * Clear all chat messages.
   */
  clearMessages: (): Promise<{ success: boolean }> =>
    fetchJson(`${API_BASE}/chat/messages`, { method: 'DELETE' }),
  
  // =========================================================================
  // Input Handling
  // =========================================================================
  
  /**
   * Submit a response to a pending input request (controller service).
   */
  submitInput: (requestId: string, value: string): Promise<{ success: boolean }> =>
    fetchJson(`${API_BASE}/chat/input/${encodeURIComponent(requestId)}`, {
      method: 'POST',
      body: JSON.stringify({ request_id: requestId, value }),
    }),
  
  /**
   * Submit a response to a pending input request (execution service).
   * Used when source="execution" in the input request.
   */
  submitExecutionInput: (requestId: string, value: string): Promise<{ success: boolean }> =>
    fetchJson(`${API_BASE}/execution/chat-input/${encodeURIComponent(requestId)}`, {
      method: 'POST',
      body: JSON.stringify({ value }),
    }),
  
  /**
   * Buffer a message for the running execution plan.
   * Only ONE message can be buffered at a time.
   * Used when execution is active but no input request is pending yet.
   */
  bufferMessage: (message: string): Promise<ChatBufferResponse> =>
    fetchJson(`${API_BASE}/execution/chat-buffer`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  
  /**
   * Get the status of the execution chat buffer.
   */
  getBufferStatus: (): Promise<ChatBufferStatus> =>
    fetchJson(`${API_BASE}/execution/chat-buffer/status`),
  
  /**
   * Cancel a pending input request.
   */
  cancelInput: (requestId: string): Promise<{ success: boolean }> =>
    fetchJson(`${API_BASE}/chat/input/${encodeURIComponent(requestId)}`, {
      method: 'DELETE',
    }),
};

// ============================================================================
// Database Inspector API - Read-only database exploration
// ============================================================================

export interface ExecutionRecord {
  id: number;
  run_id?: string;
  cycle: number;
  flow_index: string;
  inference_type?: string;
  status: string;
  concept_inferred?: string;
  timestamp?: string;
  log_content?: string;
}

export interface ExecutionHistoryResponse {
  executions: ExecutionRecord[];
  total_count: number;
  run_id: string;
}

export interface TableSchema {
  name: string;
  columns: { name: string; type: string }[];
  row_count: number;
}

export interface DatabaseOverview {
  path: string;
  size_bytes: number;
  tables: TableSchema[];
  run_count: number;
  total_executions: number;
  total_checkpoints: number;
}

export interface RunStatistics {
  run_id: string;
  total_executions: number;
  completed: number;
  failed: number;
  in_progress: number;
  cycles_completed: number;
  unique_concepts_inferred: number;
  execution_by_type: Record<string, number>;
}

export interface CheckpointStateResponse {
  cycle: number;
  inference_count: number;
  timestamp?: string;
  blackboard?: Record<string, unknown>;
  workspace?: Record<string, unknown>;
  tracker?: Record<string, unknown>;
  completed_concepts?: Record<string, unknown>;
  signatures?: Record<string, unknown>;
}

export interface BlackboardSummary {
  concept_statuses: Record<string, string>;
  item_statuses: Record<string, string>;
  item_results: Record<string, string>;
  item_completion_details: Record<string, string>;
  execution_counts: Record<string, number>;
  concept_count: number;
  item_count: number;
  completed_concepts: number;
  completed_items: number;
}

export interface QueryResult {
  rows: Record<string, unknown>[];
  total_count: number;
  table: string;
}

export const dbInspectorApi = {
  /**
   * Get an overview of the database structure and contents.
   */
  getOverview: (dbPath: string): Promise<DatabaseOverview> =>
    fetchJson(`${API_BASE}/db-inspector/overview?db_path=${encodeURIComponent(dbPath)}`),

  /**
   * Get execution history for a run.
   */
  getExecutionHistory: (
    runId: string,
    dbPath: string,
    options?: { includeLogs?: boolean; limit?: number; offset?: number }
  ): Promise<ExecutionHistoryResponse> => {
    const params = new URLSearchParams({
      db_path: dbPath,
      include_logs: String(options?.includeLogs ?? false),
      limit: String(options?.limit ?? 500),
      offset: String(options?.offset ?? 0),
    });
    return fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/executions?${params}`);
  },

  /**
   * Get logs for a specific execution.
   */
  getExecutionLogs: (
    runId: string,
    executionId: number,
    dbPath: string
  ): Promise<{ execution_id: number; log_content: string }> =>
    fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/executions/${executionId}/logs?db_path=${encodeURIComponent(dbPath)}`),

  /**
   * Get statistics for a run.
   */
  getRunStatistics: (runId: string, dbPath: string): Promise<RunStatistics> =>
    fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/statistics?db_path=${encodeURIComponent(dbPath)}`),

  /**
   * Get checkpoint state data.
   */
  getCheckpointState: (
    runId: string,
    cycle: number,
    dbPath: string,
    inferenceCount?: number
  ): Promise<CheckpointStateResponse> => {
    const params = new URLSearchParams({ db_path: dbPath });
    if (inferenceCount !== undefined) {
      params.set('inference_count', String(inferenceCount));
    }
    return fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/checkpoints/${cycle}?${params}`);
  },

  /**
   * Get blackboard summary from a checkpoint.
   */
  getBlackboardSummary: (
    runId: string,
    dbPath: string,
    cycle?: number
  ): Promise<BlackboardSummary> => {
    const params = new URLSearchParams({ db_path: dbPath });
    if (cycle !== undefined) {
      params.set('cycle', String(cycle));
    }
    return fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/blackboard?${params}`);
  },

  /**
   * Get completed concepts from a checkpoint.
   */
  getCompletedConcepts: (
    runId: string,
    dbPath: string,
    cycle?: number
  ): Promise<{ concepts: Record<string, unknown>; count: number }> => {
    const params = new URLSearchParams({ db_path: dbPath });
    if (cycle !== undefined) {
      params.set('cycle', String(cycle));
    }
    return fetchJson(`${API_BASE}/db-inspector/runs/${encodeURIComponent(runId)}/concepts?${params}`);
  },

  /**
   * Run a custom query against a table.
   */
  query: (
    dbPath: string,
    table: string,
    options?: { limit?: number; offset?: number; where?: string }
  ): Promise<QueryResult> => {
    const params = new URLSearchParams({
      db_path: dbPath,
      table,
      limit: String(options?.limit ?? 100),
      offset: String(options?.offset ?? 0),
    });
    if (options?.where) {
      params.set('where', options.where);
    }
    return fetchJson(`${API_BASE}/db-inspector/query?${params}`);
  },
};

export { ApiError };
