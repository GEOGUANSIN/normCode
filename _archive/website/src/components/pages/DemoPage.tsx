import React from 'react';
import FlowEditor from '../FlowEditor';
import type { ConceptEntry, InferenceEntry, FlowData } from '../../types';

const mockConcepts: ConceptEntry[] = [
  { id: '1', concept_name: '{digit sum}', description: 'The sum of digits', type: '{}', is_ground_concept: false, is_final_concept: true, is_invariant: false },
  { id: '2', concept_name: '[all digits]', description: 'A list of all digits', type: '[]', is_ground_concept: true, is_final_concept: false, is_invariant: false },
  { id: '3', concept_name: '{carry-over}', description: 'The carry-over value', type: '{}', is_ground_concept: true, is_final_concept: false, is_invariant: false },
];

const mockInferences: InferenceEntry[] = [
  { 
    id: '1', 
    concept_to_infer: '{digit sum}', 
    function_concept: '::(sum {1} and {2})', 
    value_concepts: ['[all digits]', '{carry-over}'],
    inference_sequence: 'imperative',
    start_without_value: false,
    start_without_value_only_once: false,
    start_without_function: false,
    start_without_function_only_once: false,
    start_with_support_reference_only: false
  },
];

const DemoPage: React.FC = () => {
  const handleSave = (flowData: FlowData) => {
    console.log('Flow data saved:', flowData);
    alert('Flow data saved! Check the console for the output.');
  };

  return (
    <div>
      <h1>NormCode Demo</h1>
      <FlowEditor 
        concepts={mockConcepts}
        inferences={mockInferences}
        onSave={handleSave}
      />
    </div>
  );
};

export default DemoPage;
