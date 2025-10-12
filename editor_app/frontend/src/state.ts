import { RepositorySetMetadata, ConceptEntry, InferenceEntry, FlowData } from './types';

export type ViewMode = 'concepts' | 'inferences' | 'flow' | 'graph' | 'logs';
export type SidebarMode = 'concepts' | 'inferences' | 'repositories';

export interface AppState {
  sidebarMode: SidebarMode;
  repositories: RepositorySetMetadata[];
  selectedRepoName: string;
  globalConcepts: ConceptEntry[];
  globalInferences: InferenceEntry[];
  concepts: ConceptEntry[];
  inferences: InferenceEntry[];
  viewMode: ViewMode;
  logs: string;
  message: { type: 'error' | 'success', text: string } | null;
  isRunning: boolean;
  showConceptForm: boolean;
  showInferenceForm: boolean;
  conceptForm: Partial<ConceptEntry>;
  inferenceForm: Partial<InferenceEntry>;
  flowData: FlowData;
  graphData: any | null;
  showAddConceptFromGlobalForm: boolean;
  showAddInferenceFromGlobalForm: boolean;
}

export const initialConceptForm: Partial<ConceptEntry> = {
  concept_name: '',
  type: '{}',
  description: '',
  is_ground_concept: false,
  is_final_concept: false,
  is_invariant: false,
  context: '',
  axis_name: '',
  natural_name: '',
};

export const initialInferenceForm: Partial<InferenceEntry> = {
  concept_to_infer: '',
  function_concept: '',
  value_concepts: [],
  inference_sequence: undefined,
  start_without_value: false,
  start_without_value_only_once: false,
  start_without_function: false,
  start_without_function_only_once: false,
  start_with_support_reference_only: false,
};

export const initialState: AppState = {
  sidebarMode: 'repositories',
  repositories: [],
  selectedRepoName: '',
  globalConcepts: [],
  globalInferences: [],
  concepts: [],
  inferences: [],
  viewMode: 'concepts',
  logs: '',
  message: null,
  isRunning: false,
  showConceptForm: false,
  showInferenceForm: false,
  conceptForm: initialConceptForm,
  inferenceForm: initialInferenceForm,
  flowData: { nodes: [], edges: [] },
  graphData: null,
  showAddConceptFromGlobalForm: false,
  showAddInferenceFromGlobalForm: false,
};

export type Action =
  | { type: 'SET_SIDEBAR_MODE'; payload: SidebarMode }
  | { type: 'SET_REPOSITORIES'; payload: RepositorySetMetadata[] }
  | { type: 'SELECT_REPO'; payload: string }
  | { type: 'SET_REPO_DATA'; payload: { concepts: ConceptEntry[]; inferences: InferenceEntry[] } }
  | { type: 'SET_GLOBAL_CONCEPTS'; payload: ConceptEntry[] }
  | { type: 'SET_GLOBAL_INFERENCES'; payload: InferenceEntry[] }
  | { type: 'DELETE_REPO' }
  | { type: 'SET_VIEW_MODE'; payload: ViewMode }
  | { type: 'SET_LOGS'; payload: string }
  | { type: 'SHOW_MESSAGE'; payload: { type: 'error' | 'success'; text: string } }
  | { type: 'HIDE_MESSAGE' }
  | { type: 'SET_RUNNING'; payload: boolean }
  | { type: 'TOGGLE_CONCEPT_FORM' }
  | { type: 'TOGGLE_INFERENCE_FORM' }
  | { type: 'UPDATE_CONCEPT_FORM'; payload: Partial<ConceptEntry> }
  | { type: 'UPDATE_INFERENCE_FORM'; payload: Partial<InferenceEntry> }
  | { type: 'RESET_CONCEPT_FORM' }
  | { type: 'RESET_INFERENCE_FORM' }
  | { type: 'TOGGLE_ADD_CONCEPT_FROM_GLOBAL_FORM' }
  | { type: 'TOGGLE_ADD_INFERENCE_FROM_GLOBAL_FORM' }
  | { type: 'SET_FLOW_DATA'; payload: FlowData }
  | { type: 'SET_GRAPH_DATA'; payload: any };

export function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_SIDEBAR_MODE':
      return { ...state, sidebarMode: action.payload };
    case 'SET_REPOSITORIES':
      return { ...state, repositories: action.payload };
    case 'SELECT_REPO':
      return { ...state, selectedRepoName: action.payload, concepts: [], inferences: [] };
    case 'SET_REPO_DATA':
      return { ...state, concepts: action.payload.concepts, inferences: action.payload.inferences };
    case 'SET_GLOBAL_CONCEPTS':
      return { ...state, globalConcepts: action.payload };
    case 'SET_GLOBAL_INFERENCES':
      return { ...state, globalInferences: action.payload };
    case 'DELETE_REPO':
        return { ...state, selectedRepoName: '', concepts: [], inferences: [], logs: '' };
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload };
    case 'SET_LOGS':
      return { ...state, logs: action.payload };
    case 'SHOW_MESSAGE':
      return { ...state, message: action.payload };
    case 'HIDE_MESSAGE':
      return { ...state, message: null };
    case 'SET_RUNNING':
      return { ...state, isRunning: action.payload };
    case 'TOGGLE_CONCEPT_FORM':
      return { ...state, showConceptForm: !state.showConceptForm };
    case 'TOGGLE_INFERENCE_FORM':
        return { ...state, showInferenceForm: !state.showInferenceForm };
    case 'UPDATE_CONCEPT_FORM':
      return { ...state, conceptForm: { ...state.conceptForm, ...action.payload } };
    case 'UPDATE_INFERENCE_FORM':
      return { ...state, inferenceForm: { ...state.inferenceForm, ...action.payload } };
    case 'RESET_CONCEPT_FORM':
      return { ...state, conceptForm: initialConceptForm, showConceptForm: false };
    case 'RESET_INFERENCE_FORM':
      return { ...state, inferenceForm: initialInferenceForm, showInferenceForm: false };
    case 'TOGGLE_ADD_CONCEPT_FROM_GLOBAL_FORM':
      return { ...state, showAddConceptFromGlobalForm: !state.showAddConceptFromGlobalForm };
    case 'TOGGLE_ADD_INFERENCE_FROM_GLOBAL_FORM':
      return { ...state, showAddInferenceFromGlobalForm: !state.showAddInferenceFromGlobalForm };
    case 'SET_FLOW_DATA':
      return { ...state, flowData: action.payload };
    case 'SET_GRAPH_DATA':
      return { ...state, graphData: action.payload };
    default:
      return state;
  }
}
