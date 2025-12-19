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
