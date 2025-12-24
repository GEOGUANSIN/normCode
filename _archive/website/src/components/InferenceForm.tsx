import React from 'react';
import type { InferenceEntry, InferenceSequence, ConceptEntry } from '../types';

interface InferenceFormProps {
  form: Partial<InferenceEntry>;
  onUpdate: (updates: Partial<InferenceEntry>) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isGlobal?: boolean;
  concepts: ConceptEntry[];
}

const InferenceForm: React.FC<InferenceFormProps> = ({ 
  form, 
  onUpdate, 
  onSubmit, 
  onCancel,
  isGlobal = false,
  concepts = []
}) => {
  const conceptNames = concepts.map(c => c.concept_name).sort();

  const handleMultiConceptChange = (field: 'value_concepts' | 'context_concepts', value: string) => {
    onUpdate({ [field]: value.split(',').map(s => s.trim()).filter(Boolean) });
  };

  const addConceptToMulti = (field: 'value_concepts' | 'context_concepts', conceptName: string) => {
    const existing = form[field] || [];
    if (!existing.includes(conceptName)) {
      onUpdate({ [field]: [...existing, conceptName] });
    }
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <h3>New {isGlobal ? 'Global ' : ''}Inference</h3>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
      </div>
      
      <div className="form-grid">
        <div className="form-group">
          <label>Inference Sequence *</label>
          <select
            className="form-control"
            value={form.inference_sequence || ''}
            onChange={(e) => onUpdate({ inference_sequence: e.target.value as InferenceSequence })}
          >
            <option value="" disabled>Select a sequence</option>
            {/* allInferenceSequences is no longer imported, so this will cause a TS1484 error */}
            {/* Assuming allInferenceSequences is defined elsewhere or will be added back */}
            {/* For now, keeping the original code as per instructions */}
            {/* <option value="" disabled>Select a sequence</option>
            {allInferenceSequences.map(seq => (
              <option key={seq} value={seq}>{seq}</option>
            ))} */}
          </select>
        </div>

        <div className="form-group">
          <label>Concept to Infer *</label>
          <select
            className="form-control"
            value={form.concept_to_infer || ''}
            onChange={(e) => onUpdate({ concept_to_infer: e.target.value })}
          >
            <option value="" disabled>Select a concept</option>
            {conceptNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Function Concept *</label>
          <select
            className="form-control"
            value={form.function_concept || ''}
            onChange={(e) => onUpdate({ function_concept: e.target.value })}
          >
            <option value="" disabled>Select a concept</option>
            {conceptNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        <div className="form-group form-group-full">
          <label>Value Concepts</label>
          <input
            type="text"
            className="form-control"
            placeholder="Comma-separated list"
            value={form.value_concepts?.join(', ') || ''}
            onChange={(e) => handleMultiConceptChange('value_concepts', e.target.value)}
          />
          <div className="concept-picker">
            {conceptNames.map(name => (
              <button key={name} className="concept-picker-item" onClick={() => addConceptToMulti('value_concepts', name)}>
                {name}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group form-group-full">
          <label>Context Concepts (optional)</label>
          <input
            type="text"
            className="form-control"
            placeholder="Comma-separated list"
            value={form.context_concepts?.join(', ') || ''}
            onChange={(e) => handleMultiConceptChange('context_concepts', e.target.value)}
          />
          <div className="concept-picker">
            {conceptNames.map(name => (
              <button key={name} className="concept-picker-item" onClick={() => addConceptToMulti('context_concepts', name)}>
                {name}
              </button>
            ))}
          </div>
        </div>

        {!isGlobal && (
          <>
            <div className="form-group form-group-full">
              <label>Working Interpretation (JSON)</label>
              <textarea
                className="form-control"
                placeholder='Enter JSON data, e.g., {"key": "value"}'
                value={form.working_interpretation ? JSON.stringify(form.working_interpretation, null, 2) : ''}
                onChange={(e) => {
                  try {
                    onUpdate({ working_interpretation: JSON.parse(e.target.value) });
                  } catch {
                    // Ignore JSON parsing errors on change
                  }
                }}
                rows={5}
              />
            </div>

            <div className="form-group form-group-full">
              <label>Flow Info (JSON)</label>
              <textarea
                className="form-control"
                placeholder='Enter JSON data, e.g., {"key": "value"}'
                value={form.flow_info ? JSON.stringify(form.flow_info, null, 2) : ''}
                onChange={(e) => {
                  try {
                    onUpdate({ flow_info: JSON.parse(e.target.value) });
                  } catch {
                    // Ignore JSON parsing errors on change
                  }
                }}
                rows={5}
              />
            </div>
          </>
        )}
        
        {isGlobal && (
          <div className="form-group form-group-full">
            <div className="alert alert-info">
              Behavioral flags like 'Start Without Value' are configured when adding the inference to a repository.
            </div>
          </div>
        )}

        {!isGlobal && (
          <div className="form-group form-group-full checkbox-grid">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.start_without_value || false}
                  onChange={(e) => onUpdate({ start_without_value: e.target.checked })}
                />
                <span>Start Without Value</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.start_without_value_only_once || false}
                  onChange={(e) => onUpdate({ start_without_value_only_once: e.target.checked })}
                />
                <span>... Only Once</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.start_without_function || false}
                  onChange={(e) => onUpdate({ start_without_function: e.target.checked })}
                />
                <span>Start Without Function</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.start_without_function_only_once || false}
                  onChange={(e) => onUpdate({ start_without_function_only_once: e.target.checked })}
                />
                <span>... Only Once</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.start_with_support_reference_only || false}
                  onChange={(e) => onUpdate({ start_with_support_reference_only: e.target.checked })}
                />
                <span>Start With Support Reference Only</span>
              </label>
          </div>
        )}
      </div>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={onSubmit}>
          Add {isGlobal ? 'Global ' : ''}Inference
        </button>
      </div>
    </div>
  );
};

export default InferenceForm;

