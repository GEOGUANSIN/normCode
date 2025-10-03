import React from 'react';
import { ConceptEntry, ConceptType } from '../types';

interface ConceptFormProps {
  form: Partial<ConceptEntry>;
  conceptTypes: ConceptType[];
  onUpdate: (updates: Partial<ConceptEntry>) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isGlobal?: boolean;
}

const ConceptForm: React.FC<ConceptFormProps> = ({ 
  form, 
  conceptTypes, 
  onUpdate, 
  onSubmit, 
  onCancel,
  isGlobal = false 
}) => {
  return (
    <div className="form-card">
      <div className="form-header">
        <h3>New {isGlobal ? 'Global ' : ''}Concept</h3>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
      </div>
      
      <div className="form-grid">
        <div className="form-group">
          <label>Concept Name *</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter concept name"
            value={form.concept_name || ''}
            onChange={(e) => onUpdate({ concept_name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Type</label>
          <select
            className="form-control"
            value={form.type || '{}'}
            onChange={(e) => onUpdate({ type: e.target.value as ConceptType })}
          >
            {conceptTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="form-group form-group-full">
          <label>Description</label>
          <textarea
            className="form-control"
            placeholder="Enter description"
            value={form.description || ''}
            onChange={(e) => onUpdate({ description: e.target.value })}
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Context</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter context"
            value={form.context || ''}
            onChange={(e) => onUpdate({ context: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Axis Name</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter axis name"
            value={form.axis_name || ''}
            onChange={(e) => onUpdate({ axis_name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Natural Name</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter natural name"
            value={form.natural_name || ''}
            onChange={(e) => onUpdate({ natural_name: e.target.value })}
          />
        </div>

        <div className="form-group form-group-full">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.is_ground_concept || false}
                onChange={(e) => onUpdate({ is_ground_concept: e.target.checked })}
              />
              <span>Ground Concept</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.is_final_concept || false}
                onChange={(e) => onUpdate({ is_final_concept: e.target.checked })}
              />
              <span>Final Concept</span>
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.is_invariant || false}
                onChange={(e) => onUpdate({ is_invariant: e.target.checked })}
              />
              <span>Invariant</span>
            </label>
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={onSubmit}>
          Add {isGlobal ? 'Global ' : ''}Concept
        </button>
      </div>
    </div>
  );
};

export default ConceptForm;

