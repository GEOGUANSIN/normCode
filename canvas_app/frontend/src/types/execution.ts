/**
 * Execution type definitions
 */

export type ExecutionStatus = 'idle' | 'running' | 'paused' | 'stepping' | 'completed' | 'failed';
export type NodeStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface ExecutionState {
  status: ExecutionStatus;
  current_inference: string | null;
  completed_count: number;
  total_count: number;
  node_statuses: Record<string, NodeStatus>;
  breakpoints: string[];
}

export interface LoadRepositoryRequest {
  concepts_path: string;
  inferences_path: string;
  inputs_path?: string;
  llm_model?: string;
  base_dir?: string;
  max_cycles?: number;
  db_path?: string;
  paradigm_dir?: string;
}

export interface ExecutionConfig {
  llm_model: string;
  max_cycles: number;
  db_path: string | null;
  base_dir: string | null;
  paradigm_dir: string | null;
  available_models: string[];
  default_max_cycles: number;
  default_db_path: string;
}

export interface LoadResponse {
  success: boolean;
  message: string;
  run_id?: string;
  total_inferences: number;
  concepts_count: number;
}

export interface CommandResponse {
  success: boolean;
  message: string;
}

export interface WebSocketEvent {
  type: string;
  data: Record<string, unknown>;
}

export interface RepositoryExample {
  name: string;
  concepts_path: string;
  inferences_path: string;
}
