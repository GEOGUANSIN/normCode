import React, { useState } from 'react';
import type { InferenceEntry } from '../types';

interface AddInferenceFromGlobalFormProps {
  globalInferences: InferenceEntry[];
  onSubmit: (data: {
    global_inference_id: string;
    flow_info: any;
    working_interpretation: any;
    start_without_value: boolean;
    start_without_value_only_once: boolean;
    start_without_function: boolean;
    start_without_function_only_once: boolean;
    start_with_support_reference_only: boolean;
  }) => void;
  onCancel: () => void;
}

const AddInferenceFromGlobalForm: React.FC<AddInferenceFromGlobalFormProps> = ({
  globalInferences,
  onSubmit,
  onCancel,
}) => {
  const [selectedInferenceId, setSelectedInferenceId] = useState<string>('');
  const [flowInfo, setFlowInfo] = useState<string>('');
  const [workingInterpretation, setWorkingInterpretation] = useState<string>('');
  const [startWithoutValue, setStartWithoutValue] = useState<boolean>(false);
  const [startWithoutValueOnlyOnce, setStartWithoutValueOnlyOnce] = useState<boolean>(false);
  const [startWithoutFunction, setStartWithoutFunction] = useState<boolean>(false);
  const [startWithoutFunctionOnlyOnce, setStartWithoutFunctionOnlyOnce] = useState<boolean>(false);
  const [startWithSupportReferenceOnly, setStartWithSupportReferenceOnly] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!selectedInferenceId) {
      setError('Please select an inference.');
      return;
    }

    let parsedFlowInfo: any;
    try {
      // Convert Python-style booleans and None to JSON format
      const jsonCompatible = flowInfo
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
        .replace(/\bNone\b/g, 'null');
      parsedFlowInfo = flowInfo ? JSON.parse(jsonCompatible) : null;
    } catch (e) {
      setError('Invalid JSON in Flow Info.');
      return;
    }

    let parsedWorkingInterpretation: any;
    try {
      // Convert Python-style booleans and None to JSON format
      const jsonCompatible = workingInterpretation
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
        .replace(/\bNone\b/g, 'null');
      parsedWorkingInterpretation = workingInterpretation ? JSON.parse(jsonCompatible) : null;
    } catch (e) {
      setError('Invalid JSON in Working Interpretation.');
      return;
    }

    onSubmit({
      global_inference_id: selectedInferenceId,
      flow_info: parsedFlowInfo,
      working_interpretation: parsedWorkingInterpretation,
      start_without_value: startWithoutValue,
      start_without_value_only_once: startWithoutValueOnlyOnce,
      start_without_function: startWithoutFunction,
      start_without_function_only_once: startWithoutFunctionOnlyOnce,
      start_with_support_reference_only: startWithSupportReferenceOnly,
    });
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <h3>Add Inference from Global</h3>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      
      <div className="form-grid">
        <div className="form-group form-group-full">
          <label>Global Inference *</label>
          <select
            className="form-control"
            value={selectedInferenceId}
            onChange={(e) => setSelectedInferenceId(e.target.value)}
          >
            <option value="" disabled>Select an inference</option>
            {globalInferences.map(inference => (
              <option key={inference.id} value={inference.id}>{inference.concept_to_infer}</option>
            ))}
          </select>
        </div>

        <div className="form-group form-group-full">
          <label>Flow Info (JSON)</label>
          <textarea
            className="form-control"
            placeholder='Enter JSON data, e.g., {"key": "value"}'
            value={flowInfo}
            onChange={(e) => setFlowInfo(e.target.value)}
            rows={5}
          />
        </div>

        <div className="form-group form-group-full">
            <label>Working Interpretation (JSON)</label>
            <textarea
                className="form-control"
                placeholder='Enter JSON data, e.g., {"key": "value"}'
                value={workingInterpretation}
                onChange={(e) => setWorkingInterpretation(e.target.value)}
                rows={5}
            />
        </div>

        <div className="form-group form-group-full checkbox-grid">
            <label className="checkbox-label">
                <input type="checkbox" checked={startWithoutValue} onChange={(e) => setStartWithoutValue(e.target.checked)} />
                <span>Start Without Value</span>
            </label>
            <label className="checkbox-label">
                <input type="checkbox" checked={startWithoutValueOnlyOnce} onChange={(e) => setStartWithoutValueOnlyOnce(e.target.checked)} />
                <span>... Only Once</span>
            </label>
            <label className="checkbox-label">
                <input type="checkbox" checked={startWithoutFunction} onChange={(e) => setStartWithoutFunction(e.target.checked)} />
                <span>Start Without Function</span>
            </label>
            <label className="checkbox-label">
                <input type="checkbox" checked={startWithoutFunctionOnlyOnce} onChange={(e) => setStartWithoutFunctionOnlyOnce(e.target.checked)} />
                <span>... Only Once</span>
            </label>
            <label className="checkbox-label">
                <input type="checkbox" checked={startWithSupportReferenceOnly} onChange={(e) => setStartWithSupportReferenceOnly(e.target.checked)} />
                <span>Start With Support Reference Only</span>
            </label>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={handleSubmit}>
          Add Inference to Repository
        </button>
      </div>
    </div>
  );
};

export default AddInferenceFromGlobalForm;
