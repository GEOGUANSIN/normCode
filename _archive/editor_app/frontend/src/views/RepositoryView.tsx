import React, { useState } from 'react';
import { RepositorySetMetadata, ConceptEntry, InferenceEntry } from '../types';
import ConceptCard from '../components/ConceptCard';
import InferenceCard from '../components/InferenceCard';
import FlowEditor from '../components/FlowEditor';
import FlowGraphView from '../components/FlowGraphView';
import LogViewer from '../components/LogViewer';
import AddConceptFromGlobalForm from '../components/AddConceptFromGlobalForm';
import AddInferenceFromGlobalForm from '../components/AddInferenceFromGlobalForm';

type ViewMode = 'concepts' | 'inferences' | 'flow' | 'graph' | 'logs';

interface Props {
  repositories: RepositorySetMetadata[];
  selectedRepoName: string;
  onSelectRepo: (name: string) => void;
  onCreateRepo: () => void;
  onDeleteRepo: () => void;
  onRunRepo: () => void;
  concepts: ConceptEntry[];
  inferences: InferenceEntry[];
  globalConcepts: ConceptEntry[];
  globalInferences: InferenceEntry[];
  flowData: { nodes: any[]; edges: any[] };
  graphData: any;
  logs: string;
  isRunning: boolean;
  onLoadGraphData: () => void;
  onAddGlobalConceptToRepo: (data: {
    global_concept_id: string;
    reference_data: any;
    reference_axis_names: string[];
    is_ground_concept: boolean;
    is_final_concept: boolean;
    is_invariant: boolean;
  }) => Promise<boolean>;
  onAddGlobalInferenceToRepo: (data: {
    global_inference_id: string;
    flow_info: any;
    working_interpretation: any;
    start_without_value: boolean;
    start_without_value_only_once: boolean;
    start_without_function: boolean;
    start_without_function_only_once: boolean;
    start_with_support_reference_only: boolean;
  }) => Promise<boolean>;
  onRemoveConceptFromRepo: (conceptId: string) => void;
  onRemoveInferenceFromRepo: (inferenceId: string) => void;
  onSaveFlow: (flowData: { nodes: any[]; edges: any[] }) => void;
}

const RepositoryView: React.FC<Props> = ({
  repositories,
  selectedRepoName,
  onSelectRepo,
  onCreateRepo,
  onDeleteRepo,
  onRunRepo,
  concepts,
  inferences,
  globalConcepts,
  globalInferences,
  flowData,
  graphData,
  logs,
  isRunning,
  onLoadGraphData,
  onAddGlobalConceptToRepo,
  onAddGlobalInferenceToRepo,
  onRemoveConceptFromRepo,
  onRemoveInferenceFromRepo,
  onSaveFlow,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('concepts');
  const [showAddConceptForm, setShowAddConceptForm] = useState(false);
  const [showAddInferenceForm, setShowAddInferenceForm] = useState(false);

  // Handle view mode changes - load graph data when switching to graph view
  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    if (mode === 'graph' && selectedRepoName) {
      onLoadGraphData();
    }
  };

  // Render repository list when none is selected
  if (!selectedRepoName) {
    return (
      <div className="content-wrapper">
        <div className="section">
          <div className="section-header">
            <div>
              <h2 className="section-title">Repositories</h2>
              <p className="section-description">Select a repository or create a new one</p>
            </div>
            <button className="btn btn-success" onClick={onCreateRepo}>
              + New Repository
            </button>
          </div>

          {repositories.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📦</div>
              <p>No repositories yet. Create your first one!</p>
            </div>
          ) : (
            repositories.map(repo => (
              <div
                key={repo.name}
                className="repo-list-item"
                onClick={() => onSelectRepo(repo.name)}
              >
                <h4>{repo.name}</h4>
                <div className="text-muted">
                  {repo.concepts.length} concepts • {repo.inferences.length} inferences
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // Render repository detail view
  return (
    <div className="content-wrapper" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <div className="page-header">
        <div style={{ flex: 1 }}>
          <h2>{selectedRepoName}</h2>
          <div className="page-subtitle">
            {concepts.length} concepts • {inferences.length} inferences
          </div>
        </div>
        <button 
          className={`btn ${isRunning ? 'btn-danger' : 'btn-success'}`}
          onClick={onRunRepo}
          disabled={isRunning}
        >
          {isRunning ? '⏹ Stop' : '▶ Run'}
        </button>
        <button className="btn btn-danger" onClick={onDeleteRepo}>
          Delete Repository
        </button>
        <button className="btn btn-ghost" onClick={() => onSelectRepo('')}>
          ← Back
        </button>
      </div>

      <div className="tabs">
        <button
          className={`tab ${viewMode === 'concepts' ? 'tab-active' : ''}`}
          onClick={() => handleViewModeChange('concepts')}
        >
          Concepts ({concepts.length})
        </button>
        <button
          className={`tab ${viewMode === 'inferences' ? 'tab-active' : ''}`}
          onClick={() => handleViewModeChange('inferences')}
        >
          Inferences ({inferences.length})
        </button>
        <button
          className={`tab ${viewMode === 'flow' ? 'tab-active' : ''}`}
          onClick={() => handleViewModeChange('flow')}
        >
          📝 Flow Editor
        </button>
        <button
          className={`tab ${viewMode === 'graph' ? 'tab-active' : ''}`}
          onClick={() => handleViewModeChange('graph')}
        >
          🔀 Graph View
        </button>
        <button
          className={`tab ${viewMode === 'logs' ? 'tab-active' : ''}`}
          onClick={() => handleViewModeChange('logs')}
        >
          📋 Logs
        </button>
      </div>

      <div className="content-wrapper" style={{ flex: 1, height: (viewMode === 'flow' || viewMode === 'graph' || viewMode === 'logs') ? 'calc(100vh - 180px)' : 'auto' }}>
        {viewMode === 'logs' ? (
          <LogViewer logContent={logs} isRunning={isRunning} />
        ) : viewMode === 'flow' ? (
          <FlowEditor 
            concepts={concepts}
            inferences={inferences}
            initialFlowData={flowData}
            onSave={onSaveFlow}
          />
        ) : viewMode === 'graph' ? (
          <FlowGraphView
            concepts={concepts}
            inferences={inferences}
            graphData={graphData}
          />
        ) : viewMode === 'concepts' ? (
          <>
            <div className="picker-card">
              <h4>Add from Global Concepts</h4>
              <div className="section-header">
                <button className="btn" onClick={() => setShowAddConceptForm(!showAddConceptForm)}>
                  {showAddConceptForm ? '✕ Cancel' : '+ Add Concept with Reference Data'}
                </button>
              </div>

              {showAddConceptForm && (
                <AddConceptFromGlobalForm
                  globalConcepts={globalConcepts}
                  onSubmit={async (data) => {
                    const success = await onAddGlobalConceptToRepo(data);
                    if (success) {
                      setShowAddConceptForm(false);
                    }
                  }}
                  onCancel={() => setShowAddConceptForm(false)}
                />
              )}
            </div>

            <div className="section">
              <h3 className="section-title">Concepts in Repository</h3>
              {concepts.length === 0 ? (
                <div className="empty-state">
                  <p>No concepts in this repository yet. Add some from the global pool above.</p>
                </div>
              ) : (
                concepts.map(concept => (
                  <ConceptCard 
                    key={concept.id} 
                    concept={concept} 
                    onDelete={onRemoveConceptFromRepo}
                    actionLabel="Remove"
                  />
                ))
              )}
            </div>
          </>
        ) : (
          <>
            <div className="picker-card">
              <h4>Add from Global Inferences</h4>
              <div className="section-header">
                <button className="btn" onClick={() => setShowAddInferenceForm(!showAddInferenceForm)}>
                  {showAddInferenceForm ? '✕ Cancel' : '+ Add Inference with Custom Data'}
                </button>
              </div>
              {showAddInferenceForm && (
                <AddInferenceFromGlobalForm
                  globalInferences={globalInferences}
                  onSubmit={async (data) => {
                    const success = await onAddGlobalInferenceToRepo(data);
                    if (success) {
                      setShowAddInferenceForm(false);
                    }
                  }}
                  onCancel={() => setShowAddInferenceForm(false)}
                />
              )}
            </div>

            <div className="section">
              <h3 className="section-title">Inferences in Repository</h3>
              {inferences.length === 0 ? (
                <div className="empty-state">
                  <p>No inferences in this repository yet. Add some from the global pool above.</p>
                </div>
              ) : (
                inferences.map(inference => (
                  <InferenceCard 
                    key={inference.id} 
                    inference={inference} 
                    onDelete={onRemoveInferenceFromRepo}
                    actionLabel="Remove"
                  />
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RepositoryView;

