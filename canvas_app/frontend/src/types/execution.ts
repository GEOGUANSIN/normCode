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

// Step progress tracking
export interface StepProgress {
  flow_index: string;
  sequence_type: string | null;
  current_step: string | null;
  current_step_index: number;
  total_steps: number;
  steps: string[];
  completed_steps: string[];
  paradigm?: string | null;
}

// Step event from WebSocket
export interface StepEvent {
  flow_index: string;
  step_name: string;
  step_full_name?: string;
  step_index: number;
  total_steps: number;
  sequence_type: string | null;
  paradigm: string | null;
  steps: string[];
}

// Sequence event from WebSocket
export interface SequenceEvent {
  flow_index: string;
  sequence_type: string;
  total_steps?: number;
  steps?: string[];
}

// Step full names for display
export const STEP_FULL_NAMES: Record<string, string> = {
  IWI: "Input Working Interpretation",
  IR: "Input References",
  MFP: "Model Function Perception",
  MVP: "Memory Value Perception",
  TVA: "Tool Value Actuation",
  TIP: "Tool Inference Perception",
  MIA: "Memory Inference Actuation",
  OR: "Output Reference",
  OWI: "Output Working Interpretation",
  GR: "Grouping References",
  AR: "Assigning References",
  LR: "Looping References",
  QR: "Quantifying References",
  T: "Timing",
};

// Step descriptions for tooltips
export const STEP_DESCRIPTIONS: Record<string, string> = {
  IWI: "Parse working interpretation and configure execution",
  IR: "Load input references from value concepts",
  MFP: "Load function/paradigm configuration",
  MVP: "Prepare memory values for execution",
  TVA: "Execute the tool (e.g., LLM call)",
  TIP: "Process tool output",
  MIA: "Store inference result in memory",
  OR: "Create output reference",
  OWI: "Finalize working interpretation",
  GR: "Group references together",
  AR: "Assign/select references",
  LR: "Process loop iteration",
  QR: "Process quantifier iteration",
  T: "Check timing conditions",
};

// ============================================================================
// Checkpoint Types
// ============================================================================

export interface RunInfo {
  run_id: string;
  first_execution: string | null;
  last_execution: string | null;
  execution_count: number;
  max_cycle: number;
  config?: Record<string, unknown>;
}

export interface CheckpointInfo {
  cycle: number;
  inference_count: number;
  timestamp: string;
}

export type ReconciliationMode = 'PATCH' | 'OVERWRITE' | 'FILL_GAPS';

export interface ResumeRequest {
  concepts_path: string;
  inferences_path: string;
  inputs_path?: string;
  db_path: string;
  run_id: string;
  cycle?: number;
  mode?: ReconciliationMode;
  llm_model?: string;
  base_dir?: string;
  max_cycles?: number;
  paradigm_dir?: string;
}

export interface ForkRequest {
  concepts_path: string;
  inferences_path: string;
  inputs_path?: string;
  db_path: string;
  source_run_id: string;
  new_run_id?: string;
  cycle?: number;
  mode?: ReconciliationMode;
  llm_model?: string;
  base_dir?: string;
  max_cycles?: number;
  paradigm_dir?: string;
}

export interface CheckpointLoadResult {
  success: boolean;
  run_id: string;
  mode: 'resume' | 'fork';
  forked_from?: string;
  completed_count: number;
  total_count: number;
  message?: string;
}
