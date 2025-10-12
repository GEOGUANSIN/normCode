import React, { useReducer } from 'react';
import { ConceptEntry, InferenceEntry, InferenceSequence } from '../types';
import InferenceCard from '../components/InferenceCard';
import InferenceForm from '../components/InferenceForm';

interface InferenceFormState {
  inference_sequence?: InferenceSequence;
  concept_to_infer?: string;
  function_concept?: string;
  value_concepts?: string[];
  context_concepts?: string[];
  flow_info?: any;
  working_interpretation?: any;
  start_without_value?: boolean;
  start_without_value_only_once?: boolean;
  start_without_function?: boolean;
  start_without_function_only_once?: boolean;
  start_with_support_reference_only?: boolean;
}

type FormAction =
  | { type: 'UPDATE_FORM'; payload: Partial<InferenceFormState> }
  | { type: 'RESET_FORM' };

const initialFormState: InferenceFormState = {
  value_concepts: [],
  start_without_value: false,
  start_without_value_only_once: false,
  start_without_function: false,
  start_without_function_only_once: false,
  start_with_support_reference_only: false,
};

const formReducer = (state: InferenceFormState, action: FormAction): InferenceFormState => {
  switch (action.type) {
    case 'UPDATE_FORM':
      return { ...state, ...action.payload };
    case 'RESET_FORM':
      return initialFormState;
    default:
      return state;
  }
};

interface Props {
  globalInferences: InferenceEntry[];
  globalConcepts: ConceptEntry[];
  onAddInference: (inference: InferenceEntry) => Promise<boolean>;
  onDeleteInference: (inferenceId: string) => void;
}

const GlobalInferencesView: React.FC<Props> = ({ 
  globalInferences, 
  globalConcepts,
  onAddInference, 
  onDeleteInference 
}) => {
  const [showForm, setShowForm] = React.useState(false);
  const [form, dispatch] = useReducer(formReducer, initialFormState);

  const handleSubmit = async () => {
    if (!form.concept_to_infer || !form.function_concept || !form.inference_sequence) {
      return;
    }

    const newInference: InferenceEntry = {
      id: crypto.randomUUID(),
      inference_sequence: form.inference_sequence!,
      concept_to_infer: form.concept_to_infer,
      function_concept: form.function_concept,
      value_concepts: form.value_concepts || [],
      context_concepts: form.context_concepts,
      flow_info: form.flow_info,
      working_interpretation: form.working_interpretation,
      start_without_value: form.start_without_value || false,
      start_without_value_only_once: form.start_without_value_only_once || false,
      start_without_function: form.start_without_function || false,
      start_without_function_only_once: form.start_without_function_only_once || false,
      start_with_support_reference_only: form.start_with_support_reference_only || false,
    };
    
    const success = await onAddInference(newInference);
    if (success) {
      dispatch({ type: 'RESET_FORM' });
      setShowForm(false);
    }
  };

  const handleCancel = () => {
    dispatch({ type: 'RESET_FORM' });
    setShowForm(false);
  };

  return (
    <div className="content-wrapper">
      <div className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Global Inferences</h2>
            <p className="section-description">Manage inferences that can be shared across repositories</p>
          </div>
          <button className="btn btn-success" onClick={() => setShowForm(!showForm)}>
            {showForm ? '✕ Cancel' : '+ Add Inference'}
          </button>
        </div>

        {showForm && (
          <InferenceForm
            form={form}
            onUpdate={(updates) => dispatch({ type: 'UPDATE_FORM', payload: updates })}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isGlobal
            concepts={globalConcepts}
          />
        )}

        {globalInferences.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔄</div>
            <p>No global inferences yet. Add your first one!</p>
          </div>
        ) : (
          globalInferences.map(inference => (
            <InferenceCard key={inference.id} inference={inference} onDelete={onDeleteInference} />
          ))
        )}
      </div>
    </div>
  );
};

export default GlobalInferencesView;

