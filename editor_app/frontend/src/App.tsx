import React, { useEffect, useReducer } from 'react';
import { RepositorySetMetadata, ConceptEntry, InferenceEntry, ConceptType } from './types';
import { apiService } from './services/api';
import './App.css';
import { initialState, reducer } from './state';
import Sidebar from './components/Sidebar';
import ConceptCard from './components/ConceptCard';
import InferenceCard from './components/InferenceCard';
import ConceptForm from './components/ConceptForm';
import InferenceForm from './components/InferenceForm';
import FlowEditor from './components/FlowEditor';
import FlowGraphView from './components/FlowGraphView';
import AddConceptFromGlobalForm from './components/AddConceptFromGlobalForm';
import AddInferenceFromGlobalForm from './components/AddInferenceFromGlobalForm';

const conceptTypes: ConceptType[] = [
  "<=", "<-", "$what?", "$how?", "$when?", "$=", "$::", "$.", "$%", "$+",
  "@by", "@if", "@if!", "@onlyIf", "@ifOnlyIf", "@after", "@before", "@with",
  "@while", "@until", "@afterstep", "&in", "&across", "&set", "&pair",
  "*every", "*some", "*count", "{}", "::", "<>", "<{}>", "::({})", "[]",
  ":S:", ":>:", ":<:", "{}?", "<:_>"
];

const App: React.FC = () => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const {
    sidebarMode,
    repositories,
    selectedRepoName,
    globalConcepts,
    globalInferences,
    concepts,
    inferences,
    viewMode,
    logs,
    logsCollapsed,
    message,
    isRunning,
    showConceptForm,
    showInferenceForm,
    conceptForm,
    inferenceForm,
    flowData,
    graphData,
    showAddConceptFromGlobalForm,
    showAddInferenceFromGlobalForm,
  } = state;

  useEffect(() => {
    loadGlobalData();
    loadRepositoryList();
  }, []);

  useEffect(() => {
    if (selectedRepoName) {
      loadRepositoryData();
    }
  }, [selectedRepoName]);

  useEffect(() => {
    if (selectedRepoName && viewMode === 'graph') {
      loadGraphData();
    }
  }, [selectedRepoName, viewMode]);

  const loadGlobalData = async () => {
    try {
      const [conceptsData, inferencesData] = await Promise.all([
        apiService.getGlobalConcepts(),
        apiService.getGlobalInferences()
      ]);
      dispatch({ type: 'SET_GLOBAL_CONCEPTS', payload: conceptsData });
      dispatch({ type: 'SET_GLOBAL_INFERENCES', payload: inferencesData });
    } catch (error) {
      showMessage('error', 'Failed to load global data');
    }
  };

  const loadRepositoryList = async () => {
    try {
      const repos = await apiService.fetchRepositorySets();
      dispatch({ type: 'SET_REPOSITORIES', payload: repos });
    } catch (error) {
      showMessage('error', 'Failed to load repositories');
    }
  };

  const loadRepositoryData = async () => {
    if (!selectedRepoName) return;
    try {
      const [conceptsData, inferencesData] = await Promise.all([
        apiService.getConcepts(selectedRepoName),
        apiService.getInferences(selectedRepoName)
      ]);
      dispatch({ type: 'SET_REPO_DATA', payload: { concepts: conceptsData, inferences: inferencesData } });
      
      // Load flow data
      try {
        const flowDataResult = await apiService.getFlow(selectedRepoName);
        dispatch({ type: 'SET_FLOW_DATA', payload: flowDataResult });
      } catch (flowError) {
        // Flow might not exist yet, that's okay
        dispatch({ type: 'SET_FLOW_DATA', payload: { nodes: [], edges: [] } });
      }
    } catch (error) {
      showMessage('error', 'Failed to load repository data');
    }
  };

  const loadGraphData = async () => {
    if (!selectedRepoName) return;
    try {
      const graphDataResult = await apiService.getGraph(selectedRepoName);
      dispatch({ type: 'SET_GRAPH_DATA', payload: graphDataResult });
    } catch (error) {
      showMessage('error', 'Failed to load graph data');
      dispatch({ type: 'SET_GRAPH_DATA', payload: null });
    }
  };

  const showMessage = (type: 'error' | 'success', text: string) => {
    dispatch({ type: 'SHOW_MESSAGE', payload: { type, text } });
    setTimeout(() => dispatch({ type: 'HIDE_MESSAGE' }), 3000);
  };

  // Global Concept Management
  const addGlobalConcept = async () => {
    if (!conceptForm.concept_name) {
      showMessage('error', 'Concept name is required');
      return;
    }

    try {
      const newConcept: ConceptEntry = {
        id: crypto.randomUUID(),
        concept_name: conceptForm.concept_name!,
        type: conceptForm.type || '{}',
        description: conceptForm.description,
        context: conceptForm.context,
        axis_name: conceptForm.axis_name,
        natural_name: conceptForm.natural_name,
        is_ground_concept: conceptForm.is_ground_concept || false,
        is_final_concept: conceptForm.is_final_concept || false,
        is_invariant: conceptForm.is_invariant || false,
        reference_data: conceptForm.reference_data,
        reference_axis_names: conceptForm.reference_axis_names,
      };
      
      await apiService.addGlobalConcept(newConcept);
      await loadGlobalData();
      dispatch({ type: 'RESET_CONCEPT_FORM' });
      showMessage('success', 'Global concept added');
    } catch (error) {
      showMessage('error', 'Failed to add global concept');
    }
  };

  const deleteGlobalConcept = async (conceptId: string) => {
    if (!confirm('Delete this global concept?')) return;

    try {
      await apiService.deleteGlobalConcept(conceptId);
      await loadGlobalData();
      showMessage('success', 'Global concept deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete global concept');
    }
  };

  // Global Inference Management
  const addGlobalInference = async () => {
    if (!inferenceForm.concept_to_infer || !inferenceForm.function_concept || !inferenceForm.inference_sequence) {
      showMessage('error', 'Required fields missing');
      return;
    }

    try {
      const newInference: InferenceEntry = {
        id: crypto.randomUUID(),
        inference_sequence: inferenceForm.inference_sequence!,
        concept_to_infer: inferenceForm.concept_to_infer,
        function_concept: inferenceForm.function_concept,
        value_concepts: inferenceForm.value_concepts || [],
        context_concepts: inferenceForm.context_concepts,
        flow_info: inferenceForm.flow_info,
        working_interpretation: inferenceForm.working_interpretation,
        start_without_value: inferenceForm.start_without_value || false,
        start_without_value_only_once: inferenceForm.start_without_value_only_once || false,
        start_without_function: inferenceForm.start_without_function || false,
        start_without_function_only_once: inferenceForm.start_without_function_only_once || false,
        start_with_support_reference_only: inferenceForm.start_with_support_reference_only || false,
      };
      
      await apiService.addGlobalInference(newInference);
      await loadGlobalData();
      dispatch({ type: 'RESET_INFERENCE_FORM' });
      showMessage('success', 'Global inference added');
    } catch (error) {
      showMessage('error', 'Failed to add global inference');
    }
  };

  const deleteGlobalInference = async (inferenceId: string) => {
    if (!confirm('Delete this global inference?')) return;

    try {
      await apiService.deleteGlobalInference(inferenceId);
      await loadGlobalData();
      showMessage('success', 'Global inference deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete global inference');
    }
  };

  // Repository Management
  const createNew = async () => {
    const name = prompt('Enter new repository name:');
    if (!name) return;

    try {
      const metadata: RepositorySetMetadata = { name, concepts: [], inferences: [] };
      await apiService.createRepositorySet(metadata);
      await loadRepositoryList();
      dispatch({ type: 'SELECT_REPO', payload: name });
      showMessage('success', `Created ${name}`);
    } catch (error) {
      showMessage('error', 'Failed to create repository');
    }
  };

  const deleteRepository = async () => {
    if (!selectedRepoName || !confirm(`Delete ${selectedRepoName}?`)) return;

    try {
      await apiService.deleteRepositorySet(selectedRepoName);
      await loadRepositoryList();
      dispatch({ type: 'DELETE_REPO' });
      showMessage('success', 'Repository deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete repository');
    }
  };

  const runRepository = async () => {
    if (!selectedRepoName) {
      showMessage('error', 'Select a repository first');
      return;
    }

    try {
      dispatch({ type: 'SET_RUNNING', payload: true });
      dispatch({ type: 'SET_LOGS', payload: `Running ${selectedRepoName}...\n` });
      const logFile = await apiService.runRepositorySet(selectedRepoName);
      
      const pollInterval = setInterval(async () => {
        try {
          const content = await apiService.getLogContent(logFile);
          dispatch({ type: 'SET_LOGS', payload: content });
          
          if (content.includes('Completed') || content.includes('Failed')) {
            clearInterval(pollInterval);
            dispatch({ type: 'SET_RUNNING', payload: false });
          }
        } catch {
          clearInterval(pollInterval);
          dispatch({ type: 'SET_RUNNING', payload: false });
        }
      }, 1000);
    } catch (error) {
      dispatch({ type: 'SET_RUNNING', payload: false });
      showMessage('error', 'Failed to run repository');
    }
  };

  const addGlobalConceptToRepo = async (data: {
    global_concept_id: string;
    reference_data: any;
    reference_axis_names: string[];
    is_ground_concept: boolean;
    is_final_concept: boolean;
    is_invariant: boolean;
  }) => {
    if (!selectedRepoName) return;

    try {
      await apiService.addConceptFromGlobal(selectedRepoName, data);
      await loadRepositoryData();
      dispatch({ type: 'TOGGLE_ADD_CONCEPT_FROM_GLOBAL_FORM' });
      showMessage('success', 'Concept added to repository');
    } catch (error) {
      showMessage('error', 'Failed to add concept to repository');
    }
  };

  const addGlobalInferenceToRepo = async (data: {
    global_inference_id: string;
    flow_info: any;
    working_interpretation: any;
    start_without_value: boolean;
    start_without_value_only_once: boolean;
    start_without_function: boolean;
    start_without_function_only_once: boolean;
    start_with_support_reference_only: boolean;
  }) => {
    if (!selectedRepoName) return;

    try {
      await apiService.addInferenceFromGlobal(selectedRepoName, data);
      await loadRepositoryData();
      dispatch({ type: 'TOGGLE_ADD_INFERENCE_FROM_GLOBAL_FORM' });
      showMessage('success', 'Inference added to repository');
    } catch (error) {
      showMessage('error', 'Failed to add inference to repository');
    }
  };

  const removeConceptFromRepo = async (conceptId: string) => {
    if (!selectedRepoName || !confirm('Remove this concept from repository?')) return;

    try {
      await apiService.deleteConcept(selectedRepoName, conceptId);
      await loadRepositoryData();
      showMessage('success', 'Concept removed');
    } catch (error) {
      showMessage('error', 'Failed to remove concept');
    }
  };

  const removeInferenceFromRepo = async (inferenceId: string) => {
    if (!selectedRepoName || !confirm('Remove this inference from repository?')) return;

    try {
      await apiService.deleteInference(selectedRepoName, inferenceId);
      await loadRepositoryData();
      showMessage('success', 'Inference removed');
    } catch (error) {
      showMessage('error', 'Failed to remove inference');
    }
  };

  const saveFlow = async (newFlowData: typeof flowData) => {
    if (!selectedRepoName) return;
    
    try {
      await apiService.saveFlow(selectedRepoName, newFlowData);
      dispatch({ type: 'SET_FLOW_DATA', payload: newFlowData });
      showMessage('success', 'Flow saved successfully');
    } catch (error) {
      showMessage('error', 'Failed to save flow');
    }
  };

  // Render Views
  const renderGlobalConceptsView = () => (
    <div className="content-wrapper">
      <div className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Global Concepts</h2>
            <p className="section-description">Manage concepts that can be shared across repositories</p>
          </div>
          <button className="btn btn-success" onClick={() => dispatch({ type: 'TOGGLE_CONCEPT_FORM' })}>
            {showConceptForm ? '✕ Cancel' : '+ Add Concept'}
          </button>
        </div>

        {showConceptForm && (
          <ConceptForm
            form={conceptForm}
            conceptTypes={conceptTypes}
            onUpdate={(updates) => dispatch({ type: 'UPDATE_CONCEPT_FORM', payload: updates })}
            onSubmit={addGlobalConcept}
            onCancel={() => dispatch({ type: 'RESET_CONCEPT_FORM' })}
            isGlobal
          />
        )}

        {globalConcepts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <p>No global concepts yet. Add your first one!</p>
          </div>
        ) : (
          globalConcepts.map(concept => (
            <ConceptCard key={concept.id} concept={concept} onDelete={deleteGlobalConcept} />
          ))
        )}
      </div>
    </div>
  );

  const renderGlobalInferencesView = () => (
    <div className="content-wrapper">
      <div className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Global Inferences</h2>
            <p className="section-description">Manage inferences that can be shared across repositories</p>
          </div>
          <button className="btn btn-success" onClick={() => dispatch({ type: 'TOGGLE_INFERENCE_FORM' })}>
            {showInferenceForm ? '✕ Cancel' : '+ Add Inference'}
          </button>
        </div>

        {showInferenceForm && (
          <InferenceForm
            form={inferenceForm}
            onUpdate={(updates) => dispatch({ type: 'UPDATE_INFERENCE_FORM', payload: updates })}
            onSubmit={addGlobalInference}
            onCancel={() => dispatch({ type: 'RESET_INFERENCE_FORM' })}
            isGlobal
            concepts={globalConcepts}
          />
        )}

        {globalInferences.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔄</div>
            <p>No global inferences yet. Add your first one!</p>
          </div>
        ) : (
          globalInferences.map(inference => (
            <InferenceCard key={inference.id} inference={inference} onDelete={deleteGlobalInference} />
          ))
        )}
      </div>
    </div>
  );

  const renderRepositoryView = () => {
    if (!selectedRepoName) {
      return (
        <div className="content-wrapper">
          <div className="section">
            <div className="section-header">
              <div>
                <h2 className="section-title">Repositories</h2>
                <p className="section-description">Select a repository or create a new one</p>
              </div>
              <button className="btn btn-success" onClick={createNew}>
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
                  onClick={() => dispatch({ type: 'SELECT_REPO', payload: repo.name })}
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

    return (
      <div style={{ flex: 1, display: 'flex' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="page-header">
            <div style={{ flex: 1 }}>
              <h2>{selectedRepoName}</h2>
              <div className="page-subtitle">
                {concepts.length} concepts • {inferences.length} inferences
              </div>
            </div>
            <button 
              className={`btn ${isRunning ? 'btn-danger' : 'btn-success'}`}
              onClick={runRepository}
              disabled={isRunning}
            >
              {isRunning ? '⏹ Stop' : '▶ Run'}
            </button>
            <button className="btn btn-danger" onClick={deleteRepository}>
              Delete Repository
            </button>
            <button className="btn btn-ghost" onClick={() => dispatch({ type: 'SELECT_REPO', payload: '' })}>
              ← Back
            </button>
          </div>

          <div className="tabs">
            <button
              className={`tab ${viewMode === 'concepts' ? 'tab-active' : ''}`}
              onClick={() => dispatch({ type: 'SET_VIEW_MODE', payload: 'concepts' })}
            >
              Concepts ({concepts.length})
            </button>
            <button
              className={`tab ${viewMode === 'inferences' ? 'tab-active' : ''}`}
              onClick={() => dispatch({ type: 'SET_VIEW_MODE', payload: 'inferences' })}
            >
              Inferences ({inferences.length})
            </button>
            <button
              className={`tab ${viewMode === 'flow' ? 'tab-active' : ''}`}
              onClick={() => dispatch({ type: 'SET_VIEW_MODE', payload: 'flow' })}
            >
              📝 Flow Editor
            </button>
            <button
              className={`tab ${viewMode === 'graph' ? 'tab-active' : ''}`}
              onClick={() => dispatch({ type: 'SET_VIEW_MODE', payload: 'graph' })}
            >
              🔀 Graph View
            </button>
          </div>

          <div className="content-wrapper" style={{ height: (viewMode === 'flow' || viewMode === 'graph') ? 'calc(100vh - 180px)' : 'auto' }}>
            {viewMode === 'flow' ? (
              <FlowEditor 
                concepts={concepts}
                inferences={inferences}
                initialFlowData={flowData}
                onSave={saveFlow}
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
                    <button className="btn" onClick={() => dispatch({ type: 'TOGGLE_ADD_CONCEPT_FROM_GLOBAL_FORM' })}>
                      {showAddConceptFromGlobalForm ? '✕ Cancel' : '+ Add Concept with Reference Data'}
                    </button>
                  </div>

                  {showAddConceptFromGlobalForm && (
                    <AddConceptFromGlobalForm
                      globalConcepts={globalConcepts}
                      onSubmit={addGlobalConceptToRepo}
                      onCancel={() => dispatch({ type: 'TOGGLE_ADD_CONCEPT_FROM_GLOBAL_FORM' })}
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
                        onDelete={removeConceptFromRepo}
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
                    <button className="btn" onClick={() => dispatch({ type: 'TOGGLE_ADD_INFERENCE_FROM_GLOBAL_FORM' })}>
                      {showAddInferenceFromGlobalForm ? '✕ Cancel' : '+ Add Inference with Custom Data'}
                    </button>
                  </div>
                  {showAddInferenceFromGlobalForm && (
                    <AddInferenceFromGlobalForm
                      globalInferences={globalInferences}
                      onSubmit={addGlobalInferenceToRepo}
                      onCancel={() => dispatch({ type: 'TOGGLE_ADD_INFERENCE_FROM_GLOBAL_FORM' })}
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
                        onDelete={removeInferenceFromRepo}
                        actionLabel="Remove"
                      />
                    ))
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <div className={`logs-panel ${logsCollapsed ? 'collapsed' : ''}`}>
          <div className="logs-header" onClick={() => dispatch({ type: 'TOGGLE_LOGS_COLLAPSED' })}>
            <span>Execution Logs</span>
            <button className="logs-toggle-btn">
              {logsCollapsed ? '▲' : '▼'}
            </button>
          </div>
          {!logsCollapsed && (
            <div className="logs-content">
              {logs || 'No logs yet. Run a repository to see execution logs.'}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      <Sidebar
        mode={sidebarMode}
        onModeChange={(mode) => dispatch({ type: 'SET_SIDEBAR_MODE', payload: mode })}
      />

      <div className="main-content">
        {message && (
          <div className={`message ${message.type === 'error' ? 'message-error' : 'message-success'}`}>
            {message.text}
          </div>
        )}

        {sidebarMode === 'concepts' && renderGlobalConceptsView()}
        {sidebarMode === 'inferences' && renderGlobalInferencesView()}
        {sidebarMode === 'repositories' && renderRepositoryView()}
      </div>
    </div>
  );
};

export default App;

