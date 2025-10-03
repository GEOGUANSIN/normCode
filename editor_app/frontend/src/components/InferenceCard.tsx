import React from 'react';
import { InferenceEntry } from '../types';

interface InferenceCardProps {
  inference: InferenceEntry;
  onDelete: (id: string) => void;
  actionLabel?: string;
}

const InferenceCard: React.FC<InferenceCardProps> = ({ inference, onDelete, actionLabel = 'Delete' }) => {
  return (
    <div className="card">
      <div className="card-content">
        <div className="card-header">
          <div>
            <h4>{inference.concept_to_infer} ← {inference.function_concept}</h4>
            <div className="text-muted">Sequence: {inference.inference_sequence}</div>
          </div>
          <button className="btn btn-danger btn-sm" onClick={() => onDelete(inference.id)}>
            {actionLabel}
          </button>
        </div>
        
        <div className="card-details">
          <div><strong>Values:</strong> {inference.value_concepts.join(', ') || 'none'}</div>
          {inference.context_concepts && inference.context_concepts.length > 0 && (
            <div><strong>Context:</strong> {inference.context_concepts.join(', ')}</div>
          )}
        </div>
        
        {(inference.start_without_value || inference.start_without_function || inference.start_with_support_reference_only) && (
          <div className="card-flags">
            {inference.start_without_value && <span className="flag">Start w/o value</span>}
            {inference.start_without_function && <span className="flag">Start w/o function</span>}
            {inference.start_with_support_reference_only && <span className="flag">Support ref only</span>}
          </div>
        )}
      </div>
    </div>
  );
};

export default InferenceCard;

