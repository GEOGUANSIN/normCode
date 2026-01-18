/**
 * Deployment-related types for canvas app
 */

export interface DeploymentServer {
  id: string;
  name: string;
  url: string;
  description?: string;
  is_default: boolean;
  added_at?: string;
}

export interface ServerHealth {
  server_id: string;
  url: string;
  is_healthy: boolean;
  status: 'healthy' | 'unhealthy' | 'unreachable' | 'timeout' | 'error';
  plans_count?: number;
  active_runs?: number;      // Currently running/pending
  completed_runs?: number;   // Completed runs
  total_runs?: number;       // All runs in memory
  available_models?: LLMModel[];
  error?: string;
}

export interface LLMModel {
  id: string;
  name: string;
  is_mock?: boolean;
  base_url?: string;
}

export interface RemotePlan {
  id: string;
  name: string;
  description?: string;
  inputs: Record<string, PlanInput>;
  outputs: Record<string, PlanOutput>;
}

export interface PlanInput {
  type: string;
  required: boolean;
  description?: string;
}

export interface PlanOutput {
  type: string;
  description?: string;
}

export interface DeployResult {
  success: boolean;
  server_id: string;
  server_name: string;
  plan_id: string;
  plan_name: string;
  message: string;
  deployed_at?: string;
}

export interface RunProgress {
  completed_count: number;
  total_count: number;
  cycle_count: number;
  current_inference?: string;
}

export interface RemoteRunStatus {
  run_id: string;
  plan_id: string;
  server_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  started_at?: string;
  completed_at?: string;
  progress?: RunProgress;
  error?: string;
}

export interface RemoteRunResult {
  run_id: string;
  plan_id: string;
  server_id?: string;
  status: string;
  final_concepts: RemoteFinalConcept[];
}

export interface RemoteFinalConcept {
  name: string;
  has_value: boolean;
  shape?: number[];
  value?: string;
}

// Request types
export interface AddServerRequest {
  name: string;
  url: string;
  description?: string;
  is_default?: boolean;
}

export interface UpdateServerRequest {
  name?: string;
  url?: string;
  description?: string;
  is_default?: boolean;
}

export interface DeployProjectRequest {
  server_id: string;
  project_id?: string;
}

export interface StartRemoteRunRequest {
  server_id: string;
  plan_id: string;
  llm_model?: string;
  ground_inputs?: Record<string, unknown>;
}

// Server building types
export interface BuildServerRequest {
  output_dir?: string;
  include_test_plans?: boolean;
  create_zip?: boolean;
}

export interface BuildServerResponse {
  success: boolean;
  output_dir: string;
  zip_path?: string;
  message: string;
  server_name: string;
  files_included: string[];
}

// =============================================================================
// Remote Graph & Project Loading Types
// =============================================================================

export interface RemotePlanGraph {
  plan_id: string;
  plan_name: string;
  description?: string;
  concepts: unknown[];      // Full concept repository JSON
  inferences: unknown[];    // Full inference repository JSON
  provisions: Record<string, RemoteProvision>;
  llm_model?: string;
  max_cycles?: number;
}

/** Canvas-ready graph data from remote server */
export interface RemoteCanvasGraph {
  plan_id: string;
  plan_name: string;
  server_id: string;
  nodes: RemoteGraphNode[];
  edges: RemoteGraphEdge[];
  concepts_count: number;
  inferences_count: number;
}

export interface RemoteGraphNode {
  id: string;
  label: string;
  category: string;
  node_type: string;
  flow_index: string | null;
  level: number;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface RemoteGraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  label: string | null;
  flow_index: string;
}

export interface RemoteProvision {
  path: string;
  files: string[];
}

export interface RemotePlanFile {
  path: string;
  content: string;
  size: number;
  encoding?: 'base64';
}

// =============================================================================
// Remote Run Database Inspection Types
// =============================================================================

export interface RemoteRunDbOverview {
  run_id: string;
  path: string;
  size_bytes: number;
  tables: RemoteDbTable[];
  total_executions: number;
  total_checkpoints: number;
}

export interface RemoteDbTable {
  name: string;
  columns: { name: string; type: string }[];
  row_count: number;
}

export interface RemoteRunExecutions {
  run_id: string;
  executions: RemoteExecution[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface RemoteExecution {
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

export interface RemoteExecutionLogs {
  run_id: string;
  execution_id: number;
  log_content: string;
}

export interface RemoteRunStatistics {
  run_id: string;
  total_executions: number;
  completed: number;
  failed: number;
  in_progress: number;
  cycles_completed: number;
  unique_concepts_inferred: number;
  execution_by_type: Record<string, number>;
}

export interface RemoteRunCheckpoints {
  run_id: string;
  checkpoints: RemoteCheckpointInfo[];
  total_count: number;
}

export interface RemoteCheckpointInfo {
  cycle: number;
  inference_count: number;
  timestamp?: string;
  state_size: number;
}

export interface RemoteCheckpointState {
  run_id: string;
  cycle: number;
  inference_count: number;
  timestamp?: string;
  blackboard?: Record<string, unknown>;
  workspace?: Record<string, unknown>;
  tracker?: Record<string, unknown>;
  completed_concepts?: Record<string, unknown>;
  signatures?: Record<string, unknown>;
}

export interface RemoteBlackboardSummary {
  run_id: string;
  concept_statuses: Record<string, string>;
  item_statuses: Record<string, string>;
  item_results: Record<string, string>;
  concept_count: number;
  item_count: number;
  completed_concepts: number;
  completed_items: number;
}

export interface RemoteCompletedConcepts {
  run_id: string;
  concepts: Record<string, RemoteConceptInfo>;
  count: number;
}

export interface RemoteConceptInfo {
  has_tensor?: boolean;
  shape?: number[];
  axes?: string[];
  data_preview?: string;
  value?: string;
}

export interface RemoteResumeResult {
  status: string;
  run_id: string;
  plan_id: string;
  resumed_from: {
    run_id: string;
    cycle: number;
    inference_count: number;
  };
  is_fork: boolean;
}

// =============================================================================
// Remote Run Binding (Mirror remote execution to local canvas)
// =============================================================================

/** A remote run bound to the local canvas for real-time event streaming */
export interface BoundRemoteRun {
  run_id: string;
  server_id: string;
  plan_id: string;
  plan_name: string;
  status: 'connecting' | 'connected' | 'running' | 'paused' | 'stepping' | 'completed' | 'failed' | 'stopped' | 'cancelled' | 'error';
  is_active: boolean;
  completed_count: number;
  total_count: number;
  cycle_count: number;
}

