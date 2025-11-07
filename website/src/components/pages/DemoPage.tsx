import React from 'react';
import FlowEditor from '../components/FlowEditor';
import { ConceptEntry, InferenceEntry, FlowData } from '../types';

const mockConcepts: ConceptEntry[] = [
  { id: '1', name: '{digit sum}', description: 'The sum of digits' },
  { id: '2', name: '[all digits]', description: 'A list of all digits' },
  { id: '3', name: '{carry-over}', description: 'The carry-over value' },
];

const mockInferences: InferenceEntry[] = [
  { 
    id: '1', 
    concept_to_infer: '{digit sum}', 
    function_concept: '::(sum {1} and {2})', 
    value_concepts: ['[all digits]', '{carry-over}'],
    inference_sequence: 'Calculate the sum of digits'
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
