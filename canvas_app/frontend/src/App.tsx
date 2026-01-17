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
  Bot,
  AlertTriangle,
  Save,
  Sparkles,
  Workflow,
  Rocket,
} from 'lucide-react';
import { GraphCanvas } from './components/graph/GraphCanvas';
import { ControlPanel } from './components/panels/ControlPanel';
import { DetailPanel } from './components/panels/DetailPanel';
import { LoadPanel } from './components/panels/LoadPanel';
import { LogPanel } from './components/panels/LogPanel';
import { SettingsPanel } from './components/panels/SettingsPanel';
import { ProjectPanel } from './components/panels/ProjectPanel';
import { EditorPanel } from './components/panels/EditorPanel';
import { CheckpointPanel } from './components/panels/CheckpointPanel';
import { AgentPanel } from './components/panels/AgentPanel';
import { WorkersPanel } from './components/panels/WorkersPanel';
import { UserInputModal } from './components/panels/UserInputModal';
import { ProjectTabs } from './components/panels/ProjectTabs';
import { ChatPanel } from './components/panels/ChatPanel';
import { DeploymentPanel } from './components/panels/DeploymentPanel';
import { ToastContainer } from './components/common/ToastNotification';
import { useWebSocket } from './hooks/useWebSocket';
import { useGraphStore } from './stores/graphStore';
import { useExecutionStore } from './stores/executionStore';
import { useProjectStore } from './stores/projectStore';
import { useChatStore } from './stores/chatStore';
import { useNotificationStore } from './stores/notificationStore';

// View modes for the main content area
type ViewMode = 'canvas' | 'editor';

// Modal for editing repository paths
interface RepositoryPathsModalProps {
  currentPaths: { concepts: string; inferences: string; inputs?: string };
  onSave: (paths: { concepts: string; inferences: string; inputs?: string }) => Promise<void>;
  onClose: () => void;
}

function RepositoryPathsModal({ currentPaths, onSave, onClose }: RepositoryPathsModalProps) {
  const [concepts, setConceptsPath] = useState(currentPaths.concepts);
  const [inferences, setInferencesPath] = useState(currentPaths.inferences);
  const [inputs, setInputsPath] = useState(currentPaths.inputs || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave({
      concepts,
      inferences,
      inputs: inputs || undefined,
    });
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            <h2 className="text-lg font-semibold text-slate-800">Edit Repository Paths</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          <p className="text-sm text-slate-600">
            Update the paths to your repository files. Paths are relative to the project directory.
          </p>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Concepts File <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={concepts}
              onChange={(e) => setConceptsPath(e.target.value)}
              placeholder="e.g., repos/concepts.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Inferences File <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={inferences}
              onChange={(e) => setInferencesPath(e.target.value)}
              placeholder="e.g., repos/inferences.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Inputs File <span className="text-slate-400">(optional)</span>
            </label>
            <input
              type="text"
              value={inputs}
              onChange={(e) => setInputsPath(e.target.value)}
              placeholder="e.g., repos/inputs.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-slate-200 bg-slate-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!concepts || !inferences || saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {saving ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Paths
          </button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [showLoadPanel, setShowLoadPanel] = useState(false);
  const [showDetailPanel, setShowDetailPanel] = useState(true);
  const [showLogPanel, setShowLogPanel] = useState(true);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [showCheckpointPanel, setShowCheckpointPanel] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [showWorkersPanel, setShowWorkersPanel] = useState(false);
  const [showDeploymentPanel, setShowDeploymentPanel] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('canvas');
  const [detailPanelFullscreen, setDetailPanelFullscreen] = useState(false);
  const [showRepoPathsModal, setShowRepoPathsModal] = useState(false);
  
  const graphData = useGraphStore((s) => s.graphData);
  const status = useExecutionStore((s) => s.status);
  const logs = useExecutionStore((s) => s.logs);
  const wsConnected = useWebSocket();
  const showError = useNotificationStore((s) => s.showError);
  const showWarning = useNotificationStore((s) => s.showWarning);
  
  // Track shown error logs to avoid duplicates
  const [lastErrorLogCount, setLastErrorLogCount] = useState(0);
  
  // Chat state
  const { isOpen: isChatOpen, togglePanel: toggleChatPanel, controllerStatus } = useChatStore();
  
  
  // Project state
  const {
    currentProject,
    projectPath,
    isLoaded,
    repositoriesExist,
    isLoading: projectLoading,
    openTabs,
    activeTabId,
    remoteProjectTabs,
    fetchCurrentProject,
    fetchRecentProjects,
    fetchOpenTabs,
    loadProjectRepositories,
    closeProject,
    setProjectPanelOpen,
    updateRepositories,
  } = useProjectStore();
  
  // Check if current project is read-only (compiler project)
  // Remote projects are "read-only" in terms of editing, but can still be executed
  const activeTab = openTabs.find(tab => tab.id === activeTabId);
  const isReadOnlyProject = activeTab?.is_read_only ?? false;
  const isRemoteProject = activeTab?.is_remote ?? false;

  // Fetch project state on startup
  useEffect(() => {
    fetchCurrentProject();
    fetchRecentProjects();
    fetchOpenTabs();
  }, [fetchCurrentProject, fetchRecentProjects, fetchOpenTabs]);
  
  // Show toast notifications for new error/warning logs
  useEffect(() => {
    const errorLogs = logs.filter(log => log.level === 'error');
    
    // Only show toasts for new errors (not ones we've already seen)
    if (errorLogs.length > lastErrorLogCount) {
      const newErrors = errorLogs.slice(lastErrorLogCount);
      
      // Show toast for each new error (limit to avoid spam)
      newErrors.slice(0, 3).forEach((log, idx) => {
        // Slight delay between toasts for visual effect
        setTimeout(() => {
          showError(
            log.flowIndex ? `Error in ${log.flowIndex}` : 'Error',
            log.message,
          );
        }, idx * 100);
      });
      
      // If more than 3 new errors, show summary
      if (newErrors.length > 3) {
        setTimeout(() => {
          showWarning(
            'Multiple Errors',
            `${newErrors.length - 3} more errors occurred. Check the log panel for details.`,
          );
        }, 400);
      }
      
      setLastErrorLogCount(errorLogs.length);
    }
  }, [logs, lastErrorLogCount, showError, showWarning]);

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
          <img src="/psylens-logo.png" alt="NormCode Canvas" className="w-6 h-6" />
          
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
                  onClick={loadProjectRepositories}
                  disabled={projectLoading}
                  className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
                  title="Reload repositories (refresh from source files)"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${projectLoading ? 'animate-spin' : ''}`} />
                </button>
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
              <button
                onClick={() => setShowRepoPathsModal(true)}
                className="px-2 py-0.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 text-xs rounded-full flex items-center gap-1 transition-colors cursor-pointer"
                title="Click to edit repository paths"
              >
                <AlertTriangle className="w-3 h-3" />
                Missing files
              </button>
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
          {/* Left panel toggles (Workers, Agent) */}
          {viewMode === 'canvas' && (
            <>
              {/* Plans in Work Panel Toggle */}
              <button
                onClick={() => setShowWorkersPanel(!showWorkersPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showWorkersPanel
                    ? 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title="Plans in Work - View all active NormCode plans"
              >
                <Workflow size={18} />
              </button>
              
              {/* Agent Panel Toggle */}
              <button
                onClick={() => setShowAgentPanel(!showAgentPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showAgentPanel
                    ? 'text-purple-600 bg-purple-50 hover:bg-purple-100'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title="Agent Configuration Panel"
              >
                <Bot size={18} />
              </button>
            </>
          )}
          
          {/* Panel toggles - show in canvas mode */}
          {viewMode === 'canvas' && (
            <>
              <div className="w-px h-6 bg-slate-200 mx-1" />
              {/* Detail panel toggle - only when graph loaded */}
              {graphData && (
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
              )}
              {/* Log panel toggle - always available to see loading errors */}
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
          
          {/* Deploy */}
          <button
            onClick={() => setShowDeploymentPanel(true)}
            className="p-2 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
            title="Deploy Project"
          >
            <Rocket size={18} />
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
          
          <div className="w-px h-6 bg-slate-200 mx-1" />
          
          {/* Chat Panel Toggle - compiler-driven chat */}
          <button
            onClick={toggleChatPanel}
            className={`p-2 rounded-lg transition-colors flex items-center gap-1.5 ${
              isChatOpen
                ? 'text-purple-600 bg-purple-50 hover:bg-purple-100'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
            }`}
            title="Compiler Chat"
          >
            <Sparkles size={18} />
            <span className="text-sm font-medium">Chat</span>
            {controllerStatus === 'running' && (
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            )}
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

      {/* Main Content Area with Chat Panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left side: Tabs + Main Content (includes ControlPanel when in canvas mode) */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Project Tabs Bar - shows when multiple projects are open or remote tabs exist */}
          {(openTabs.length > 1 || remoteProjectTabs.length > 0) && (
            <ProjectTabs onOpenProjectPanel={() => setProjectPanelOpen(true)} />
          )}
          {/* Control Panel - show in canvas mode when graph is loaded
              Read-only projects hide the control panel UNLESS they are remote projects
              (remote projects are read-only for editing but can still be executed)
              Remote execution is handled through the unified worker system - remote proxy workers
              show up in WorkersPanel and ControlPanel uses the bound worker's API */}
          {graphData && viewMode === 'canvas' && (!isReadOnlyProject || isRemoteProject) && (
            <ControlPanel 
              onCheckpointToggle={() => setShowCheckpointPanel(!showCheckpointPanel)}
              checkpointPanelOpen={showCheckpointPanel}
            />
          )}

          {/* Checkpoint Panel - dropdown below control panel */}
          <CheckpointPanel 
            isOpen={showCheckpointPanel && viewMode === 'canvas'} 
            onToggle={() => setShowCheckpointPanel(!showCheckpointPanel)} 
          />

          {/* Main Content */}
          <main className="flex-1 flex flex-col overflow-hidden relative z-0">
            {viewMode === 'editor' ? (
              // Editor View
              <EditorPanel />
            ) : (!isLoaded && !graphData) ? (
          // Show message when repositories not loaded yet AND no worker graph is loaded (Canvas mode)
          // Include LogPanel at the bottom for loading errors visibility
          <>
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
            {/* Log Panel - available even before loading for error visibility */}
            {showLogPanel && <LogPanel />}
          </>
        ) : (
          // Canvas View
          <>
            <div className="flex-1 flex overflow-hidden">
              {/* Left side panels */}
              {showWorkersPanel && <WorkersPanel />}
              {showAgentPanel && <AgentPanel />}
              
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
        </div>

        {/* Chat Panel - appears on right side, independent of view mode */}
        <ChatPanel />
      </div>

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

      {/* Repository Paths Modal */}
      {showRepoPathsModal && (
        <RepositoryPathsModal
          currentPaths={currentProject.repositories}
          onSave={async (paths) => {
            const success = await updateRepositories(paths);
            if (success) {
              setShowRepoPathsModal(false);
            }
          }}
          onClose={() => setShowRepoPathsModal(false)}
        />
      )}

      {/* User Input Modal (human-in-the-loop) */}
      <UserInputModal />

      {/* Deployment Panel */}
      <DeploymentPanel
        isOpen={showDeploymentPanel}
        onClose={() => setShowDeploymentPanel(false)}
      />

      {/* Toast Notifications - prominent alerts for errors/warnings */}
      <ToastContainer />

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
