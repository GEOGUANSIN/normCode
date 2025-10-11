import React, { useState } from 'react';
import { ConceptEntry, InferenceEntry, FlowData } from '../types';
import './FlowEditor.css';

interface FlowEditorProps {
  concepts: ConceptEntry[];
  inferences: InferenceEntry[];
  initialFlowData?: FlowData;
  onSave: (flowData: FlowData) => void;
}

interface FlowLine {
  id: string;
  index: string; // e.g., "1.1.2"
  type: 'inference' | 'concept';
  depth: number;
  inferenceId?: string;
  conceptId?: string;
  data: any;
}

const FlowEditor: React.FC<FlowEditorProps> = ({ 
  inferences, 
  initialFlowData,
  onSave 
}) => {
  function recalculateIndices(lines: FlowLine[]): FlowLine[] {
    const counters: number[] = [0];
    
    return lines.map((line) => {
      const depth = line.depth;
      
      // Ensure we have enough counter levels
      while (counters.length <= depth) {
        counters.push(0);
      }
      
      // Increment current level
      counters[depth]++;
      
      // Reset deeper levels
      counters.splice(depth + 1);
      
      return {
        ...line,
        index: counters.join('.'),
      };
    });
  }

  const [flowLines, setFlowLines] = useState<FlowLine[]>(() => {
    // Reconstruct the flow lines from the inference data
    const initialLines = initialFlowData?.nodes
      ?.map((node): FlowLine => ({ // Add explicit type here
        id: node.id,
        index: node.data.flow_info?.flow_index || '',
        type: 'inference',
        depth: node.data.flow_info?.depth || 0,
        inferenceId: node.data.id,
        conceptId: undefined,
        data: node.data,
      })) || [];
    // Do not recalculate indices on initial load as they come from the backend
    return initialLines;
  });
  
  const [selectedLineId, setSelectedLineId] = useState<string | null>(null);

  const addInferenceLine = (inference: InferenceEntry) => {
    const insertIndex = selectedLineId 
      ? flowLines.findIndex(l => l.id === selectedLineId) + 1
      : flowLines.length;
    
    const currentDepth = selectedLineId
      ? flowLines.find(l => l.id === selectedLineId)?.depth || 0
      : 0;

    const newLine: FlowLine = {
      id: `inference-${inference.id}-${Date.now()}`,
      index: '',
      type: 'inference',
      depth: currentDepth,
      inferenceId: inference.id,
      data: inference,
    };

    const newLines = [
      ...flowLines.slice(0, insertIndex),
      newLine,
      ...flowLines.slice(insertIndex),
    ];

    setFlowLines(recalculateIndices(newLines));
  };

  const indentLine = (lineId: string) => {
    const newLines = flowLines.map(line =>
      line.id === lineId ? { ...line, depth: Math.min(line.depth + 1, 10) } : line
    );
    setFlowLines(recalculateIndices(newLines));
  };

  const outdentLine = (lineId: string) => {
    const newLines = flowLines.map(line =>
      line.id === lineId ? { ...line, depth: Math.max(line.depth - 1, 0) } : line
    );
    setFlowLines(recalculateIndices(newLines));
  };

  const moveLineUp = (lineId: string) => {
    const idx = flowLines.findIndex(l => l.id === lineId);
    if (idx > 0) {
      const newLines = [...flowLines];
      [newLines[idx - 1], newLines[idx]] = [newLines[idx], newLines[idx - 1]];
      setFlowLines(recalculateIndices(newLines));
    }
  };

  const moveLineDown = (lineId: string) => {
    const idx = flowLines.findIndex(l => l.id === lineId);
    if (idx < flowLines.length - 1) {
      const newLines = [...flowLines];
      [newLines[idx], newLines[idx + 1]] = [newLines[idx + 1], newLines[idx]];
      setFlowLines(recalculateIndices(newLines));
    }
  };

  const deleteLine = (lineId: string) => {
    const newLines = flowLines.filter(l => l.id !== lineId);
    setFlowLines(recalculateIndices(newLines));
    if (selectedLineId === lineId) {
      setSelectedLineId(null);
    }
  };

  const handleSave = () => {
    const flowData: FlowData = {
      nodes: flowLines.map(line => ({
        id: line.id,
        type: line.type,
        position: { x: 0, y: 0 }, // Not used in line-by-line mode
        data: {
          ...line.data,
          flow_info: {
            flow_index: line.index,
            depth: line.depth,
          },
        },
      })),
      edges: [], // Auto-generated from hierarchy
    };
    onSave(flowData);
  };

  const clearFlow = () => {
    if (confirm('Are you sure you want to clear the entire flow?')) {
      setFlowLines([]);
      setSelectedLineId(null);
    }
  };

  const renderFlowLine = (line: FlowLine) => {
    const isSelected = selectedLineId === line.id;
    const indentPixels = line.depth * 24;

    // For inferences, we'll also render the concepts they use
    const renderInferenceWithConcepts = () => {
      const conceptsToShow = [];
      
      // Add function_concept first with <=
      if (line.data.function_concept) {
        conceptsToShow.push({
          arrow: '<=',
          name: line.data.function_concept,
          description: 'function'
        });
      }
      
      // Add value_concepts with <-
      if (line.data.value_concepts && Array.isArray(line.data.value_concepts)) {
        line.data.value_concepts.forEach((concept: string) => {
          conceptsToShow.push({
            arrow: '<-',
            name: concept,
            description: 'value'
          });
        });
      }

      return (
        <div className="flow-line-group">
          <div className="flow-line-inference">
            <span className="flow-line-main">
              {line.data.concept_to_infer}
            </span>
            <span className="flow-line-separator">|</span>
            <span className="flow-line-index">{line.index}.</span>
            <span className="flow-line-sequence">
              {line.data.inference_sequence}
            </span>
          </div>
          
          {conceptsToShow.length > 0 && (
            <div className="flow-line-concepts-list">
              {conceptsToShow.map((concept, idx) => (
                <div key={idx} className="flow-line-concept-item">
                  <span className="flow-line-arrow">{concept.arrow}</span>
                  <span className="flow-line-concept-name">{concept.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    };

    return (
      <div
        key={line.id}
        className={`flow-line ${isSelected ? 'selected' : ''}`}
        onClick={() => setSelectedLineId(line.id)}
      >
        <div className="flow-line-controls">
          <button 
            className="btn-icon" 
            onClick={(e) => { e.stopPropagation(); moveLineUp(line.id); }}
            disabled={flowLines[0].id === line.id}
            title="Move up"
          >
            ↑
          </button>
          <button 
            className="btn-icon" 
            onClick={(e) => { e.stopPropagation(); moveLineDown(line.id); }}
            disabled={flowLines[flowLines.length - 1].id === line.id}
            title="Move down"
          >
            ↓
          </button>
          <button 
            className="btn-icon" 
            onClick={(e) => { e.stopPropagation(); outdentLine(line.id); }}
            disabled={line.depth === 0}
            title="Decrease indent"
          >
            ←
          </button>
          <button 
            className="btn-icon" 
            onClick={(e) => { e.stopPropagation(); indentLine(line.id); }}
            title="Increase indent"
          >
            →
          </button>
          <button 
            className="btn-icon btn-delete" 
            onClick={(e) => { e.stopPropagation(); deleteLine(line.id); }}
            title="Delete"
          >
            ×
          </button>
        </div>
        
        <div className="flow-line-content" style={{ marginLeft: `${indentPixels}px` }}>
          {renderInferenceWithConcepts()}
        </div>
      </div>
    );
  };

  return (
    <div className="flow-editor-container">
      <div className="flow-sidebar">
        <div className="flow-sidebar-header">
          <h3>Add Inferences</h3>
          <p className="flow-sidebar-hint">
            Concepts are automatically shown with each inference
          </p>
        </div>

        <div className="flow-sidebar-content">
          {inferences.length === 0 ? (
            <div className="flow-empty-state">
              <p>No inferences available. Add some to the repository first.</p>
            </div>
          ) : (
            inferences.map(inference => (
              <div 
                key={inference.id} 
                className="flow-item"
                onClick={() => addInferenceLine(inference)}
              >
                <div className="flow-item-icon">🔄</div>
                <div className="flow-item-content">
                  <div className="flow-item-title">
                    {inference.concept_to_infer} ← {inference.function_concept}
                  </div>
                  <div className="flow-item-subtitle">
                    {inference.inference_sequence}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flow-sidebar-actions">
          <button className="btn btn-success btn-block" onClick={handleSave}>
            💾 Save Flow
          </button>
          <button className="btn btn-danger btn-block" onClick={clearFlow}>
            🗑️ Clear Flow
          </button>
        </div>
      </div>

      <div className="flow-canvas">
        <div className="flow-line-editor">
          <div className="flow-line-editor-header">
            <h3>Flow Structure</h3>
            <div className="flow-line-stats">
              <span>{flowLines.length} lines</span>
              {selectedLineId && <span className="selected-indicator">• Line selected</span>}
            </div>
          </div>
          
          <div className="flow-line-editor-content">
            {flowLines.length === 0 ? (
              <div className="flow-empty-state">
                <p>Start by adding inferences or concepts from the sidebar.</p>
                <p className="flow-hint">
                  Click on items in the sidebar to add them to the flow.
                  <br />
                  Use the arrow buttons to adjust hierarchy and order.
                </p>
              </div>
            ) : (
              flowLines.map(renderFlowLine)
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowEditor;

