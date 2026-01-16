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

