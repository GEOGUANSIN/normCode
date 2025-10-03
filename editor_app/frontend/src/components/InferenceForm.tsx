import React from 'react';
import { InferenceEntry, allInferenceSequences, InferenceSequence } from '../types';

interface InferenceFormProps {
  form: Partial<InferenceEntry>;
  onUpdate: (updates: Partial<InferenceEntry>) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isGlobal?: boolean;
}

const InferenceForm: React.FC<InferenceFormProps> = ({ 
  form, 
  onUpdate, 
  onSubmit, 
  onCancel,
  isGlobal = false 
}) => {
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
            {allInferenceSequences.map(seq => (
              <option key={seq} value={seq}>{seq}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Concept to Infer *</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter concept name"
            value={form.concept_to_infer || ''}
            onChange={(e) => onUpdate({ concept_to_infer: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Function Concept *</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter function concept"
            value={form.function_concept || ''}
            onChange={(e) => onUpdate({ function_concept: e.target.value })}
          />
        </div>

        <div className="form-group form-group-full">
          <label>Value Concepts</label>
          <input
            type="text"
            className="form-control"
            placeholder="Comma-separated list"
            value={form.value_concepts?.join(', ') || ''}
            onChange={(e) => onUpdate({ 
              value_concepts: e.target.value.split(',').map(s => s.trim()).filter(Boolean) 
            })}
          />
        </div>

        <div className="form-group form-group-full">
          <label>Context Concepts (optional)</label>
          <input
            type="text"
            className="form-control"
            placeholder="Comma-separated list"
            value={form.context_concepts?.join(', ') || ''}
            onChange={(e) => onUpdate({ 
              context_concepts: e.target.value.split(',').map(s => s.trim()).filter(Boolean) 
            })}
          />
        </div>

        <div className="form-group form-group-full">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.start_without_value || false}
                onChange={(e) => onUpdate({ start_without_value: e.target.checked })}
              />
              <span>Start without value</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.start_without_value_only_once || false}
                onChange={(e) => onUpdate({ start_without_value_only_once: e.target.checked })}
              />
              <span>Only once (value)</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.start_without_function || false}
                onChange={(e) => onUpdate({ start_without_function: e.target.checked })}
              />
              <span>Start without function</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.start_without_function_only_once || false}
                onChange={(e) => onUpdate({ start_without_function_only_once: e.target.checked })}
              />
              <span>Only once (function)</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.start_with_support_reference_only || false}
                onChange={(e) => onUpdate({ start_with_support_reference_only: e.target.checked })}
              />
              <span>Support reference only</span>
            </label>
          </div>
        </div>
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

