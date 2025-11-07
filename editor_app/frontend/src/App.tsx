import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import GlobalConceptsView from './views/GlobalConceptsView';
import GlobalInferencesView from './views/GlobalInferencesView';
import RepositoryView from './views/RepositoryView';
import { useMessage } from './hooks/useMessage';
import { useGlobalData } from './hooks/useGlobalData';
import { useRepository } from './hooks/useRepository';
import { useRepositoryRunner } from './hooks/useRepositoryRunner';

type SidebarMode = 'concepts' | 'inferences' | 'repositories';

const App: React.FC = () => {
  const [sidebarMode, setSidebarMode] = useState<SidebarMode>('repositories');
  
  // Custom hooks
  const { message, showMessage } = useMessage();
  const {
    globalConcepts,
    globalInferences,
    addGlobalConcept,
    deleteGlobalConcept,
    addGlobalInference,
    deleteGlobalInference,
  } = useGlobalData(showMessage);

  const {
    repositories,
    selectedRepoName,
    setSelectedRepoName,
    concepts,
    inferences,
    flowData,
    graphData,
    loadGraphData,
    createRepository,
    deleteRepository,
    addGlobalConceptToRepo,
    addGlobalInferenceToRepo,
    removeConceptFromRepo,
    removeInferenceFromRepo,
    saveFlow,
  } = useRepository(showMessage);

  const { logs, isRunning, runRepository } = useRepositoryRunner(showMessage);

  // Repository management handlers
  const handleCreateRepository = () => {
    const name = prompt('Enter new repository name:');
    if (name) {
      createRepository(name);
    }
  };

  const handleRunRepository = () => {
    if (selectedRepoName) {
      runRepository(selectedRepoName);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        mode={sidebarMode}
        onModeChange={setSidebarMode}
      />

      <div className="main-content">
        {message && (
          <div className={`message ${message.type === 'error' ? 'message-error' : 'message-success'}`}>
            {message.text}
          </div>
        )}

        {sidebarMode === 'concepts' && (
          <GlobalConceptsView
            globalConcepts={globalConcepts}
            onAddConcept={addGlobalConcept}
            onDeleteConcept={deleteGlobalConcept}
          />
        )}

        {sidebarMode === 'inferences' && (
          <GlobalInferencesView
            globalInferences={globalInferences}
            globalConcepts={globalConcepts}
            onAddInference={addGlobalInference}
            onDeleteInference={deleteGlobalInference}
          />
        )}

        {sidebarMode === 'repositories' && (
          <RepositoryView
            repositories={repositories}
            selectedRepoName={selectedRepoName}
            onSelectRepo={setSelectedRepoName}
            onCreateRepo={handleCreateRepository}
            onDeleteRepo={deleteRepository}
            onRunRepo={handleRunRepository}
            concepts={concepts}
            inferences={inferences}
            globalConcepts={globalConcepts}
            globalInferences={globalInferences}
            flowData={flowData}
            graphData={graphData}
            logs={logs}
            isRunning={isRunning}
            onLoadGraphData={loadGraphData}
            onAddGlobalConceptToRepo={addGlobalConceptToRepo}
            onAddGlobalInferenceToRepo={addGlobalInferenceToRepo}
            onRemoveConceptFromRepo={removeConceptFromRepo}
            onRemoveInferenceFromRepo={removeInferenceFromRepo}
            onSaveFlow={saveFlow}
          />
        )}
      </div>
    </div>
  );
};

export default App;
