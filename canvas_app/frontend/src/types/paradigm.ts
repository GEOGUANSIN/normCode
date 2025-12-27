/**
 * Type definitions for Paradigm files.
 * 
 * Paradigms are JSON files that define reusable composition patterns for agent sequences.
 * They specify:
 *   - metadata: Description, inputs (vertical/horizontal), and outputs
 *   - env_spec: Tools and their affordances available in the paradigm
 *   - sequence_spec: Steps that set up and execute the composition
 */

// =============================================================================
// Core Types
// =============================================================================

/**
 * MetaValue - A reference to a result from a previous step.
 * Used in composition plans to reference function values stored in the context.
 */
export interface MetaValue {
  __type__: 'MetaValue';
  key: string;
}

/**
 * Check if a value is a MetaValue reference.
 */
export function isMetaValue(value: unknown): value is MetaValue {
  return (
    typeof value === 'object' &&
    value !== null &&
    (value as MetaValue).__type__ === 'MetaValue'
  );
}

// =============================================================================
// Environment Specification (Tools & Affordances)
// =============================================================================

/**
 * An affordance represents a specific capability/method of a tool.
 */
export interface AffordanceSpec {
  affordance_name: string;
  call_code: string;
}

/**
 * A tool with its available affordances.
 */
export interface ToolSpec {
  tool_name: string;
  affordances: AffordanceSpec[];
}

/**
 * Environment specification - defines available tools.
 */
export interface EnvSpec {
  tools: ToolSpec[];
}

// =============================================================================
// Sequence Specification (Steps)
// =============================================================================

/**
 * A composition plan step - represents a function call in the data flow.
 * This is the "horizontal" part of the paradigm - the runtime data flow.
 */
export interface CompositionPlanStep {
  output_key: string;
  function: MetaValue;
  params: Record<string, string>;  // Maps param names to variable keys
  literal_params?: Record<string, string | number | boolean>;  // Static/literal values
}

/**
 * Parameters for a step - can include a composition plan.
 */
export interface StepParams {
  [key: string]: unknown;
  plan?: CompositionPlanStep[];
  return_key?: string;
  template_key?: string;
}

/**
 * A sequence step - represents a tool affordance invocation.
 * This is the "vertical" part of the paradigm - the setup steps.
 */
export interface SequenceStep {
  step_index: number;
  affordance: string;  // Format: "tool_name.affordance_name"
  params: StepParams;
  result_key: string;
}

/**
 * Sequence specification - ordered list of steps.
 */
export interface SequenceSpec {
  steps: SequenceStep[];
}

// =============================================================================
// Metadata
// =============================================================================

/**
 * Input specification for paradigm inputs.
 */
export interface InputSpec {
  vertical: Record<string, string>;   // Composition-time inputs (from agent state)
  horizontal: Record<string, string>; // Runtime inputs (passed at invocation)
}

/**
 * Output specification.
 */
export interface OutputSpec {
  type: string;         // e.g., 'FileLocation', 'Literal', 'Normal', 'Text'
  description: string;
}

/**
 * Paradigm metadata - describes the paradigm's purpose and interface.
 */
export interface ParadigmMetadata {
  description: string;
  inputs: InputSpec;
  outputs: OutputSpec;
}

// =============================================================================
// Complete Paradigm
// =============================================================================

/**
 * Complete paradigm file structure.
 */
export interface Paradigm {
  metadata: ParadigmMetadata;
  env_spec: EnvSpec;
  sequence_spec: SequenceSpec;
}

// =============================================================================
// Parsed Paradigm (for Editor)
// =============================================================================

/**
 * Parsed representation of an affordance for the editor.
 */
export interface ParsedAffordance {
  index: number;
  tool_name: string;
  affordance_name: string;
  call_code: string;
  full_id: string;  // "tool_name.affordance_name"
}

/**
 * Parsed representation of a tool for the editor.
 */
export interface ParsedTool {
  index: number;
  tool_name: string;
  affordances: ParsedAffordance[];
}

/**
 * Parsed representation of a composition step for the editor.
 */
export interface ParsedCompositionStep {
  index: number;
  output_key: string;
  function_ref: string;  // The key from MetaValue
  params: Array<{ name: string; value: string; is_literal: boolean }>;
}

/**
 * Parsed representation of a sequence step for the editor.
 */
export interface ParsedSequenceStep {
  index: number;
  step_index: number;
  affordance: string;
  tool_name: string;
  affordance_name: string;
  params: StepParams;
  result_key: string;
  has_composition_plan: boolean;
  composition_steps: ParsedCompositionStep[];
}

/**
 * Parsed representation of an input parameter.
 */
export interface ParsedInput {
  name: string;
  description: string;
  type: 'vertical' | 'horizontal';
}

/**
 * Fully parsed paradigm structure for the editor.
 */
export interface ParsedParadigm {
  // Metadata
  description: string;
  inputs: ParsedInput[];
  output_type: string;
  output_description: string;
  
  // Environment (tools)
  tools: ParsedTool[];
  all_affordances: ParsedAffordance[];
  
  // Sequence (vertical steps + horizontal composition)
  steps: ParsedSequenceStep[];
  
  // Track which step contains the main composition
  composition_step_index: number | null;
  
  // Validation
  errors: string[];
  warnings: string[];
}

// =============================================================================
// Editor Types
// =============================================================================

/**
 * Editor view mode for paradigm files.
 */
export type ParadigmViewMode = 'visual' | 'json' | 'flow';

/**
 * Section being edited in the paradigm editor.
 */
export type ParadigmSection = 'metadata' | 'tools' | 'steps' | 'composition';

/**
 * Drag and drop item types.
 */
export type DragItemType = 'tool' | 'affordance' | 'step' | 'composition-step';

/**
 * State for paradigm editor.
 */
export interface ParadigmEditorState {
  // Current paradigm
  paradigm: Paradigm | null;
  parsed: ParsedParadigm | null;
  
  // Edit state
  isModified: boolean;
  activeSection: ParadigmSection;
  viewMode: ParadigmViewMode;
  
  // Selection
  selectedToolIndex: number | null;
  selectedStepIndex: number | null;
  selectedCompositionStepIndex: number | null;
  
  // Expansion state
  expandedTools: Set<number>;
  expandedSteps: Set<number>;
  
  // Validation
  errors: string[];
  warnings: string[];
}

// =============================================================================
// API Types
// =============================================================================

export interface ParadigmParseRequest {
  content: string;
  format: 'paradigm' | 'json';
}

export interface ParadigmParseResponse {
  success: boolean;
  parsed: ParsedParadigm | null;
  errors: string[];
  warnings: string[];
}

export interface ParadigmSerializeRequest {
  parsed: ParsedParadigm;
  format: 'paradigm' | 'json';
}

export interface ParadigmSerializeResponse {
  success: boolean;
  content: string;
  errors: string[];
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Parse an affordance string into tool and affordance names.
 */
export function parseAffordanceId(affordance: string): { tool: string; affordance: string } {
  const parts = affordance.split('.');
  return {
    tool: parts[0] || '',
    affordance: parts[1] || '',
  };
}

/**
 * Create an affordance ID from tool and affordance names.
 */
export function createAffordanceId(tool: string, affordance: string): string {
  return `${tool}.${affordance}`;
}

/**
 * Get a display name for a step based on its affordance.
 */
export function getStepDisplayName(step: SequenceStep): string {
  const { affordance } = parseAffordanceId(step.affordance);
  return `${step.step_index}. ${affordance} → ${step.result_key}`;
}

/**
 * Get a display name for a composition step.
 */
export function getCompositionStepDisplayName(step: CompositionPlanStep): string {
  return `${step.function.key}(...) → ${step.output_key}`;
}

/**
 * Parse a paradigm filename to extract its components.
 * Format: [inputs]-[composition]-[outputs].json
 */
export function parseParadigmFilename(filename: string): {
  inputs: string[];
  composition: string[];
  outputs: string;
} | null {
  // Remove .json extension
  const baseName = filename.replace(/\.json$/, '');
  
  // Split by hyphen groups
  const parts = baseName.split('-');
  
  const inputs: string[] = [];
  const composition: string[] = [];
  let outputs = '';
  
  let currentSection: 'inputs' | 'composition' | 'outputs' = 'inputs';
  
  for (const part of parts) {
    if (part.startsWith('h_') || part.startsWith('v_')) {
      if (currentSection === 'inputs') {
        inputs.push(part);
      }
    } else if (part.startsWith('c_')) {
      currentSection = 'composition';
      // Split by underscore within composition
      const compParts = part.substring(2).split('_');
      composition.push(...compParts);
    } else if (part.startsWith('o_')) {
      currentSection = 'outputs';
      outputs = part.substring(2);
    } else if (currentSection === 'composition') {
      // Additional composition parts joined by hyphen
      composition.push(part);
    }
  }
  
  return { inputs, composition, outputs };
}

