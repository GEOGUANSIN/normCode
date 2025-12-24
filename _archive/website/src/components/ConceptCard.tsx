import React from 'react';
import type { ConceptEntry } from '../types';

interface ConceptCardProps {
  concept: ConceptEntry;
  onDelete: (id: string) => void;
  actionLabel?: string;
}

const ConceptCard: React.FC<ConceptCardProps> = ({ concept, onDelete, actionLabel = 'Delete' }) => {
  return (
    <div className="card">
      <div className="card-content">
        <div className="card-header">
          <h4>{concept.concept_name}</h4>
          <button className="btn btn-danger btn-sm" onClick={() => onDelete(concept.id)}>
            {actionLabel}
          </button>
        </div>
        
        <div className="card-meta">
          <span className="badge">{concept.type}</span>
          {concept.is_ground_concept && <span className="badge badge-success">Ground</span>}
          {concept.is_final_concept && <span className="badge badge-warning">Final</span>}
          {concept.is_invariant && <span className="badge badge-info">Invariant</span>}
        </div>
        
        {concept.description && <p className="card-description">{concept.description}</p>}
        
        {(concept.context || concept.axis_name || concept.natural_name) && (
          <div className="card-details">
            {concept.context && <div><strong>Context:</strong> {concept.context}</div>}
            {concept.axis_name && <div><strong>Axis:</strong> {concept.axis_name}</div>}
            {concept.natural_name && <div><strong>Natural Name:</strong> {concept.natural_name}</div>}
          </div>
        )}

        {concept.reference_data && (
            <div className="card-details">
                <strong>Reference Data:</strong>
                <pre>{JSON.stringify(concept.reference_data, null, 2)}</pre>
            </div>
        )}
      </div>
    </div>
  );
};

export default ConceptCard;

