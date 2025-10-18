import React, { useState } from 'react';
import { ConceptEntry } from '../types';

interface AddConceptFromGlobalFormProps {
  globalConcepts: ConceptEntry[];
  onSubmit: (data: {
    global_concept_id: string;
    reference_data: any;
    reference_axis_names: string[];
    is_ground_concept: boolean;
    is_final_concept: boolean;
    is_invariant: boolean;
  }) => void;
  onCancel: () => void;
}

const AddConceptFromGlobalForm: React.FC<AddConceptFromGlobalFormProps> = ({
  globalConcepts,
  onSubmit,
  onCancel,
}) => {
  const [selectedConceptId, setSelectedConceptId] = useState<string>('');
  const [referenceData, setReferenceData] = useState<string>('');
  const [axisNames, setAxisNames] = useState<string>('');
  const [isGroundConcept, setIsGroundConcept] = useState<boolean>(false);
  const [isFinalConcept, setIsFinalConcept] = useState<boolean>(false);
  const [isInvariant, setIsInvariant] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!selectedConceptId) {
      setError('Please select a concept.');
      return;
    }

    let parsedReferenceData: any;
    try {
      // Convert Python-style booleans and None to JSON format
      const jsonCompatible = referenceData
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
        .replace(/\bNone\b/g, 'null');
      parsedReferenceData = referenceData ? JSON.parse(jsonCompatible) : null;
    } catch (e) {
      setError('Invalid JSON in Reference Data.');
      return;
    }

    const axisNamesArray = axisNames.split(',').map(s => s.trim()).filter(Boolean);

    onSubmit({
      global_concept_id: selectedConceptId,
      reference_data: parsedReferenceData,
      reference_axis_names: axisNamesArray,
      is_ground_concept: isGroundConcept,
      is_final_concept: isFinalConcept,
      is_invariant: isInvariant,
    });
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <h3>Add Concept from Global</h3>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      
      <div className="form-grid">
        <div className="form-group form-group-full">
          <label>Global Concept *</label>
          <select
            className="form-control"
            value={selectedConceptId}
            onChange={(e) => setSelectedConceptId(e.target.value)}
          >
            <option value="" disabled>Select a concept</option>
            {globalConcepts.map(concept => (
              <option key={concept.id} value={concept.id}>{concept.concept_name}</option>
            ))}
          </select>
        </div>

        <div className="form-group form-group-full">
          <label>Reference Data (JSON)</label>
          <textarea
            className="form-control"
            placeholder='Enter JSON data, e.g., ["a", "b"] or {"key": "value"}'
            value={referenceData}
            onChange={(e) => setReferenceData(e.target.value)}
            rows={5}
          />
        </div>

        <div className="form-group form-group-full">
          <label>Reference Axis Names (comma-separated)</label>
          <input
            type="text"
            className="form-control"
            placeholder="e.g., axis1, axis2"
            value={axisNames}
            onChange={(e) => setAxisNames(e.target.value)}
          />
        </div>

        <div className="form-group form-group-full">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isGroundConcept}
                onChange={(e) => setIsGroundConcept(e.target.checked)}
              />
              <span>Ground Concept</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isFinalConcept}
                onChange={(e) => setIsFinalConcept(e.target.checked)}
              />
              <span>Final Concept</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isInvariant}
                onChange={(e) => setIsInvariant(e.target.checked)}
              />
              <span>Invariant</span>
            </label>
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={handleSubmit}>
          Add Concept to Repository
        </button>
      </div>
    </div>
  );
};

export default AddConceptFromGlobalForm;
