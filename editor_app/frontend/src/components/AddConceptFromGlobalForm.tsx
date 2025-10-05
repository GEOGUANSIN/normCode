import React, { useState } from 'react';
import { ConceptEntry } from '../types';

interface AddConceptFromGlobalFormProps {
  globalConcepts: ConceptEntry[];
  onSubmit: (data: {
    global_concept_id: string;
    reference_data: any;
    reference_axis_names: string[];
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
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!selectedConceptId) {
      setError('Please select a concept.');
      return;
    }

    let parsedReferenceData: any;
    try {
      parsedReferenceData = referenceData ? JSON.parse(referenceData) : null;
    } catch (e) {
      setError('Invalid JSON in Reference Data.');
      return;
    }

    const axisNamesArray = axisNames.split(',').map(s => s.trim()).filter(Boolean);

    onSubmit({
      global_concept_id: selectedConceptId,
      reference_data: parsedReferenceData,
      reference_axis_names: axisNamesArray,
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
