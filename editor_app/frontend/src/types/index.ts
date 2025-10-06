// Matches backend ConceptEntrySchema
export type ConceptType =
  | "<=" | "<-" | "$what?" | "$how?" | "$when?" | "$=" | "$::" | "$." | "$%" | "$+"
  | "@by" | "@if" | "@if!" | "@onlyIf" | "@ifOnlyIf" | "@after" | "@before" | "@with"
  | "@while" | "@until" | "@afterstep" | "&in" | "&across" | "&set" | "&pair"
  | "*every" | "*some" | "*count" | "{}" | "::" | "<>" | "<{}>" | "::({})" | "[]"
  | ":S:" | ":>:" | ":<:" | "{}?" | "<:_>";

export interface ConceptEntry {
  id: string;
  concept_name: string;
  type: ConceptType;
  context?: string;
  axis_name?: string;
  natural_name?: string;
  description?: string;
  is_ground_concept: boolean;
  is_final_concept: boolean;
  is_invariant: boolean;
  reference_data?: any;
  reference_axis_names?: string[];
}

// Matches backend InferenceEntrySchema
export type InferenceSequence = "simple" | "imperative" | "judgement" | "grouping" | "assigning" | "quantifying" | "timing";

export const allInferenceSequences: InferenceSequence[] = ["simple", "imperative", "judgement", "grouping", "assigning", "quantifying", "timing"];

export interface InferenceEntry {
  id: string;
  inference_sequence: InferenceSequence;
  concept_to_infer: string;
  function_concept: string;
  value_concepts: string[];
  context_concepts?: string[];
  flow_info?: any;
  working_interpretation?: any;
  start_without_value: boolean;
  start_without_value_only_once: boolean;
  start_without_function: boolean;
  start_without_function_only_once: boolean;
  start_with_support_reference_only: boolean;
}

// Matches backend RepositorySetSchema (just metadata)
export interface RepositorySetMetadata {
  name: string;
  concepts: string[];  // IDs
  inferences: string[];  // IDs
}

// Matches backend RepositorySetData (full data)
export interface RepositorySetData {
  name: string;
  concepts: ConceptEntry[];
  inferences: InferenceEntry[];
}

export interface RunResponse {
  status: string;
  log_file: string;
}

export interface LogContentResponse {
  content: string;
}

export interface ApiError {
  message: string;
  status?: number;
}

// Flow-related types for the visual flow editor
export interface FlowNode {
  id: string;
  type: 'inference' | 'concept';
  position: { x: number; y: number };
  data: InferenceEntry;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
}

export interface FlowData {
  nodes: FlowNode[];
  edges: FlowEdge[];
}

export interface RepositorySetMetadataWithFlow {
  name: string;
  concepts: string[];
  inferences: string[];
  flow?: FlowData;
}