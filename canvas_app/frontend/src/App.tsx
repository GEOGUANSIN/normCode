/**
 * Main Application Component
 * Project-based NormCode Canvas - opens like a PyCharm/IDE project
 */

import { useState, useEffect } from 'react';
import { 
  FolderOpen, 
  Settings, 
  HelpCircle, 
  PanelRight, 
  PanelRightClose, 
  PanelBottom, 
  PanelBottomClose,
  Folder,
  RefreshCw,
  X,
  GitGraph,
  FileCode,
} from 'lucide-react';
import { GraphCanvas } from './components/graph/GraphCanvas';
import { ControlPanel } from './components/panels/ControlPanel';
import { DetailPanel } from './components/panels/DetailPanel';
import { LoadPanel } from './components/panels/LoadPanel';
import { LogPanel } from './components/panels/LogPanel';
import { SettingsPanel } from './components/panels/SettingsPanel';
import { ProjectPanel } from './components/panels/ProjectPanel';
import { EditorPanel } from './components/panels/EditorPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useGraphStore } from './stores/graphStore';
import { useExecutionStore } from './stores/executionStore';
import { useProjectStore } from './stores/projectStore';

// View modes for the main content area
type ViewMode = 'canvas' | 'editor';

function App() {
  const [showLoadPanel, setShowLoadPanel] = useState(false);
  const [showDetailPanel, setShowDetailPanel] = useState(true);
  const [showLogPanel, setShowLogPanel] = useState(true);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('canvas');
  const [detailPanelFullscreen, setDetailPanelFullscreen] = useState(false);
  
  const graphData = useGraphStore((s) => s.graphData);
  const status = useExecutionStore((s) => s.status);
  const wsConnected = useWebSocket();
  
  // Project state
  const {
    currentProject,
    projectPath,
    isLoaded,
    repositoriesExist,
    isLoading: projectLoading,
    fetchCurrentProject,
    fetchRecentProjects,
    loadProjectRepositories,
    closeProject,
    setProjectPanelOpen,
  } = useProjectStore();

  // Fetch project state on startup
  useEffect(() => {
    fetchCurrentProject();
    fetchRecentProjects();
  }, [fetchCurrentProject, fetchRecentProjects]);

  // If no project is open, show project welcome screen
  if (!currentProject) {
    return <ProjectPanel />;
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-50">
      {/* Single Unified Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between">
        {/* Left side: Logo + Project Info */}
        <div className="flex items-center gap-4">
          {/* App Logo */}
          <img src="/logo.png" alt="NormCode Canvas" className="w-6 h-6 opacity-90" style={{ filter: 'brightness(1.1)' }} />
          
          {/* Project Info */}
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-700">{currentProject.name}</span>
            {isLoaded ? (
              <div className="flex items-center gap-1">
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                  Loaded
                </span>
                <button
                  onClick={() => setShowLoadPanel(true)}
                  className="text-xs text-slate-400 hover:text-slate-600 hover:underline transition-colors"
                  title="Load different repositories"
                >
                  (change)
                </button>
              </div>
            ) : repositoriesExist ? (
              <button
                onClick={loadProjectRepositories}
                disabled={projectLoading}
                className="px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-700 text-xs rounded-full flex items-center gap-1 transition-colors"
              >
                {projectLoading ? (
                  <RefreshCw className="w-3 h-3 animate-spin" />
                ) : (
                  <FolderOpen className="w-3 h-3" />
                )}
                Load
              </button>
            ) : (
              <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                Missing files
              </span>
            )}
          </div>
          
          {/* Config summary */}
          <span className="text-xs text-slate-400">
            {currentProject.execution.llm_model} • {currentProject.execution.max_cycles} cycles
          </span>
          
          {/* View Mode Tabs */}
          <div className="w-px h-6 bg-slate-200 mx-2" />
          <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('canvas')}
              className={`flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all ${
                viewMode === 'canvas'
                  ? 'bg-white text-blue-600 shadow-sm font-medium'
                  : 'text-slate-600 hover:text-slate-800'
              }`}
            >
              <GitGraph size={14} />
              Canvas
            </button>
            <button
              onClick={() => setViewMode('editor')}
              className={`flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all ${
                viewMode === 'editor'
                  ? 'bg-white text-blue-600 shadow-sm font-medium'
                  : 'text-slate-600 hover:text-slate-800'
              }`}
            >
              <FileCode size={14} />
              Editor
            </button>
          </div>
        </div>
        
        {/* Right side: Actions */}
        <div className="flex items-center gap-1">
          {/* Panel toggles - only show in canvas mode */}
          {graphData && viewMode === 'canvas' && (
            <>
              <div className="w-px h-6 bg-slate-200 mx-1" />
              <button
                onClick={() => setShowDetailPanel(!showDetailPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showDetailPanel 
                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100' 
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title={showDetailPanel ? 'Hide detail panel' : 'Show detail panel'}
              >
                {showDetailPanel ? <PanelRightClose size={18} /> : <PanelRight size={18} />}
              </button>
              <button
                onClick={() => setShowLogPanel(!showLogPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showLogPanel 
                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100' 
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title={showLogPanel ? 'Hide log panel' : 'Show log panel'}
              >
                {showLogPanel ? <PanelBottomClose size={18} /> : <PanelBottom size={18} />}
              </button>
            </>
          )}
          
          <div className="w-px h-6 bg-slate-200 mx-1" />
          
          {/* Settings */}
          <button
            onClick={() => setShowSettingsPanel(!showSettingsPanel)}
            className={`p-2 rounded-lg transition-colors ${
              showSettingsPanel
                ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
            }`}
            title="Execution Settings"
          >
            <Settings size={18} />
          </button>
          
          {/* Project settings */}
          <button
            onClick={() => setProjectPanelOpen(true)}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Project Settings"
          >
            <Folder size={18} />
          </button>
          
          {/* Help */}
          <button
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Help"
          >
            <HelpCircle size={18} />
          </button>
          
          {/* Close project */}
          <button
            onClick={closeProject}
            className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            title="Close Project"
          >
            <X size={18} />
          </button>
        </div>
      </header>

      {/* Settings Panel */}
      <SettingsPanel 
        isOpen={showSettingsPanel} 
        onToggle={() => setShowSettingsPanel(!showSettingsPanel)} 
      />

      {/* Control Panel - only show in canvas mode when graph is loaded */}
      {graphData && viewMode === 'canvas' && <ControlPanel />}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative z-0">
        {viewMode === 'editor' ? (
          // Editor View
          <EditorPanel />
        ) : !isLoaded ? (
          // Show message when repositories not loaded yet (Canvas mode)
          <div className="flex-1 flex items-center justify-center bg-white">
            <div className="text-center p-8">
              <Folder className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-700 mb-2">Project Ready</h2>
              <p className="text-slate-500 mb-4 max-w-md">
                {repositoriesExist 
                  ? 'Click "Load" in the header to start working with your NormCode plan.'
                  : 'Repository files not found. Make sure concepts.json and inferences.json exist in the project directory.'
                }
              </p>
              {repositoriesExist && (
                <button
                  onClick={loadProjectRepositories}
                  disabled={projectLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center gap-2 mx-auto transition-colors"
                >
                  {projectLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <FolderOpen className="w-4 h-4" />
                  )}
                  Load Repositories
                </button>
              )}
            </div>
          </div>
        ) : (
          // Canvas View
          <>
            <div className="flex-1 flex overflow-hidden">
              {/* Graph Canvas */}
              <div className="flex-1 overflow-hidden">
                <GraphCanvas />
              </div>

              {/* Detail Panel */}
              {graphData && showDetailPanel && !detailPanelFullscreen && (
                <DetailPanel 
                  isFullscreen={false}
                  onToggleFullscreen={() => setDetailPanelFullscreen(true)}
                />
              )}
            </div>

            {/* Log Panel */}
            {graphData && showLogPanel && <LogPanel />}
          </>
        )}
      </main>

      {/* Fullscreen Detail Panel */}
      {graphData && detailPanelFullscreen && (
        <DetailPanel 
          isFullscreen={true}
          onToggleFullscreen={() => setDetailPanelFullscreen(false)}
        />
      )}

      {/* Load Panel Modal (for loading different repositories) */}
      {showLoadPanel && (
        <LoadPanel 
          onClose={() => setShowLoadPanel(false)} 
          onOpenSettings={() => setShowSettingsPanel(true)}
        />
      )}

      {/* Project Panel Modal */}
      <ProjectPanel />

      {/* Status Bar */}
      <footer className="bg-white border-t border-slate-200 px-4 py-1 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <span className={`flex items-center gap-1 ${
            status === 'running' ? 'text-green-600' :
            status === 'paused' ? 'text-yellow-600' :
            status === 'failed' ? 'text-red-600' :
            status === 'completed' ? 'text-green-600' :
            'text-slate-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              status === 'running' ? 'bg-green-500 animate-pulse' :
              status === 'paused' ? 'bg-yellow-500' :
              status === 'failed' ? 'bg-red-500' :
              status === 'completed' ? 'bg-green-500' :
              'bg-slate-400'
            }`} />
            {status === 'idle' ? 'Ready' : status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
          {graphData && (
            <>
              <span>•</span>
              <span>{graphData.nodes.length} nodes</span>
              <span>•</span>
              <span>{graphData.edges.length} edges</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 truncate max-w-xs" title={projectPath || ''}>
            {projectPath}
          </span>
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            {wsConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
