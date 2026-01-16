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
  active_runs?: number;
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

export interface RemoteRunStatus {
  run_id: string;
  plan_id: string;
  server_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface RemoteRunResult {
  run_id: string;
  plan_id: string;
  server_id: string;
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

