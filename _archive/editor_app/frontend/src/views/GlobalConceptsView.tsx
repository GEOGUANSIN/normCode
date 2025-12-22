import React, { useReducer } from 'react';
import { ConceptEntry, ConceptType } from '../types';
import ConceptCard from '../components/ConceptCard';
import ConceptForm from '../components/ConceptForm';

const conceptTypes: ConceptType[] = [
  "<=", "<-", "$what?", "$how?", "$when?", "$=", "$::", "$.", "$%", "$+",
  "@by", "@if", "@if!", "@onlyIf", "@ifOnlyIf", "@after", "@before", "@with",
  "@while", "@until", "@afterstep", "&in", "&across", "&set", "&pair",
  "*every", "*some", "*count", "{}", "::", "<>", "<{}>", "::({})", "[]",
  ":S:", ":>:", ":<:", "{}?", "<:_>"
];

interface ConceptFormState {
  concept_name?: string;
  type?: ConceptType;
  description?: string;
  context?: string;
  axis_name?: string;
  natural_name?: string;
  is_ground_concept?: boolean;
  is_final_concept?: boolean;
  is_invariant?: boolean;
  reference_data?: any;
  reference_axis_names?: string[];
}

type FormAction =
  | { type: 'UPDATE_FORM'; payload: Partial<ConceptFormState> }
  | { type: 'RESET_FORM' };

const initialFormState: ConceptFormState = {
  type: '{}',
  is_ground_concept: false,
  is_final_concept: false,
  is_invariant: false,
};

const formReducer = (state: ConceptFormState, action: FormAction): ConceptFormState => {
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
  globalConcepts: ConceptEntry[];
  onAddConcept: (concept: ConceptEntry) => Promise<boolean>;
  onDeleteConcept: (conceptId: string) => void;
}

const GlobalConceptsView: React.FC<Props> = ({ globalConcepts, onAddConcept, onDeleteConcept }) => {
  const [showForm, setShowForm] = React.useState(false);
  const [form, dispatch] = useReducer(formReducer, initialFormState);

  const handleSubmit = async () => {
    if (!form.concept_name) {
      return;
    }

    const newConcept: ConceptEntry = {
      id: crypto.randomUUID(),
      concept_name: form.concept_name!,
      type: form.type || '{}',
      description: form.description,
      context: form.context,
      axis_name: form.axis_name,
      natural_name: form.natural_name,
      is_ground_concept: form.is_ground_concept || false,
      is_final_concept: form.is_final_concept || false,
      is_invariant: form.is_invariant || false,
      reference_data: form.reference_data,
      reference_axis_names: form.reference_axis_names,
    };
    
    const success = await onAddConcept(newConcept);
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
            <h2 className="section-title">Global Concepts</h2>
            <p className="section-description">Manage concepts that can be shared across repositories</p>
          </div>
          <button className="btn btn-success" onClick={() => setShowForm(!showForm)}>
            {showForm ? '✕ Cancel' : '+ Add Concept'}
          </button>
        </div>

        {showForm && (
          <ConceptForm
            form={form}
            conceptTypes={conceptTypes}
            onUpdate={(updates) => dispatch({ type: 'UPDATE_FORM', payload: updates })}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isGlobal
          />
        )}

        {globalConcepts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <p>No global concepts yet. Add your first one!</p>
          </div>
        ) : (
          globalConcepts.map(concept => (
            <ConceptCard key={concept.id} concept={concept} onDelete={onDeleteConcept} />
          ))
        )}
      </div>
    </div>
  );
};

export default GlobalConceptsView;

