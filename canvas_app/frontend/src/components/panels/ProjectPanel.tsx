/**
 * ProjectPanel - Project management UI
 * Provides open project, create project, and recent projects functionality.
 * Supports multiple projects per directory.
 */
import { useState, useEffect } from 'react';
import { 
  FolderOpen, 
  Plus, 
  Clock, 
  X, 
  ChevronDown, 
  ChevronRight,
  Folder,
  RefreshCw,
  Search,
  File,
  Trash2
} from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import { executionApi, projectApi } from '../../services/api';
import type { ExecutionConfig } from '../../types/execution';
import type { RegisteredProject, DiscoveredPathsResponse } from '../../types/project';

type TabType = 'open' | 'create' | 'recent' | 'all';

export function ProjectPanel() {
  const {
    currentProject,
    recentProjects,
    allProjects,
    directoryProjects,
    isProjectPanelOpen,
    isLoading,
    error,
    setProjectPanelOpen,
    setError,
    fetchRecentProjects,
    fetchAllProjects,
    scanDirectory,
    openProject,
    openProjectAsTab,
    createProject,
    removeProjectFromRegistry,
  } = useProjectStore();
  
  // Use openProjectAsTab when a project is already open (multi-project mode)
  const openProjectAction = currentProject ? openProjectAsTab : openProject;

  const [activeTab, setActiveTab] = useState<TabType>('recent');
  const [openPath, setOpenPath] = useState('');
  const [scannedProjects, setScannedProjects] = useState<RegisteredProject[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  
  // Create project form state
  const [createPath, setCreatePath] = useState('');
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [conceptsPath, setConceptsPath] = useState('concepts.json');
  const [inferencesPath, setInferencesPath] = useState('inferences.json');
  const [inputsPath, setInputsPath] = useState('');
  const [paradigmDir, setParadigmDir] = useState('');
  const [llmModel, setLlmModel] = useState('demo');
  const [maxCycles, setMaxCycles] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Discovery state
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredPaths, setDiscoveredPaths] = useState<DiscoveredPathsResponse | null>(null);
  
  // Available models
  const [availableModels, setAvailableModels] = useState<string[]>(['demo']);

  // Fetch config on mount
  useEffect(() => {
    fetchRecentProjects();
    fetchAllProjects();
    executionApi.getConfig().then((config: ExecutionConfig) => {
      setAvailableModels(config.available_models);
    }).catch(console.error);
  }, [fetchRecentProjects, fetchAllProjects]);

  // Discover paths in directory
  const handleDiscoverPaths = async () => {
    if (!createPath.trim()) {
      setError('Please enter a directory path first');
      return;
    }
    setIsDiscovering(true);
    setError(null);
    try {
      const discovered = await projectApi.discoverPaths({ directory: createPath.trim() });
      setDiscoveredPaths(discovered);
      
      // Auto-populate form fields with discovered paths
      if (discovered.concepts) {
        setConceptsPath(discovered.concepts);
      }
      if (discovered.inferences) {
        setInferencesPath(discovered.inferences);
      }
      if (discovered.inputs) {
        setInputsPath(discovered.inputs);
      }
      if (discovered.paradigm_dir) {
        setParadigmDir(discovered.paradigm_dir);
        // Show advanced settings if paradigm dir was discovered
        setShowAdvanced(true);
      }
      
      // Show message about what was discovered
      const foundItems = [];
      if (discovered.concepts) foundItems.push('concepts');
      if (discovered.inferences) foundItems.push('inferences');
      if (discovered.inputs) foundItems.push('inputs');
      if (discovered.paradigm_dir) foundItems.push('paradigm dir');
      
      if (foundItems.length === 0) {
        setError('No repository files or paradigm directories found in this directory');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to discover paths');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Clear discovered paths when create path changes
  const handleCreatePathChange = (value: string) => {
    setCreatePath(value);
    setDiscoveredPaths(null);
  };

  // Scan directory for projects
  const handleScanDirectory = async () => {
    if (!openPath.trim()) {
      setError('Please enter a directory path');
      return;
    }
    setIsScanning(true);
    setError(null);
    try {
      const projects = await scanDirectory(openPath.trim(), true);
      setScannedProjects(projects);
      if (projects.length === 0) {
        setError('No project configs found in this directory');
      } else if (projects.length === 1) {
        // Auto-open if only one project found
        await openProjectAction(undefined, undefined, projects[0].id);
      }
    } finally {
      setIsScanning(false);
    }
  };

  // Open a specific project from scanned list
  const handleOpenScannedProject = async (project: RegisteredProject) => {
    const success = await openProjectAction(project.directory, project.config_file, project.id);
    if (success) {
      setOpenPath('');
      setScannedProjects([]);
    }
  };

  const handleCreateProject = async () => {
    if (!createPath.trim() || !projectName.trim()) {
      setError('Project path and name are required');
      return;
    }
    const success = await createProject(createPath.trim(), projectName.trim(), {
      description: description || undefined,
      conceptsPath: conceptsPath || 'concepts.json',
      inferencesPath: inferencesPath || 'inferences.json',
      inputsPath: inputsPath || undefined,
      paradigmDir: paradigmDir || undefined,
      llmModel,
      maxCycles,
    });
    if (success) {
      setCreatePath('');
      setProjectName('');
      setDescription('');
    }
  };

  const handleOpenRecent = async (project: RegisteredProject) => {
    await openProjectAction(undefined, undefined, project.id);
  };
  
  const handleRemoveFromRegistry = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    await removeProjectFromRegistry(projectId);
  };

  if (!isProjectPanelOpen && !currentProject) {
    // Show welcome screen when no project is open
    return (
      <div className="fixed inset-0 bg-slate-100 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl p-8 max-w-2xl w-full mx-4 border border-slate-200">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <img src="/psylens-logo.png" alt="Psylens" className="w-10 h-10" />
              <h1 className="text-3xl font-bold text-slate-800">NormCode Canvas</h1>
            </div>
            <p className="text-slate-500">Visual execution and debugging for NormCode plans</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
              <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">×</button>
            </div>
          )}

          {/* Recent Projects - Show only the 2 most recent */}
          {recentProjects.length > 0 && (
            <div className="mb-6">
              <h2 className="text-sm font-semibold text-slate-600 mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Recent Projects
              </h2>
              <div className="space-y-2">
                {recentProjects.slice(0, 2).map((project) => (
                  <div
                    key={project.id}
                    onClick={() => !isLoading && handleOpenRecent(project)}
                    className={`w-full text-left p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex items-center gap-3 group cursor-pointer ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
                  >
                    <Folder className="w-5 h-5 text-blue-500" />
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-800 font-medium truncate">{project.name}</div>
                      <div className="text-slate-500 text-xs truncate flex items-center gap-1">
                        <File className="w-3 h-3" />
                        {project.config_file}
                        <span className="text-slate-400 mx-1">in</span>
                        {project.directory}
                      </div>
                    </div>
                    <div className="text-slate-400 text-xs">
                      {project.last_opened ? new Date(project.last_opened).toLocaleDateString() : ''}
                    </div>
                    <button
                      onClick={(e) => handleRemoveFromRegistry(e, project.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity"
                      title="Remove from list"
                    >
                      <Trash2 className="w-4 h-4 text-red-400 hover:text-red-600" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => { setProjectPanelOpen(true); setActiveTab('open'); }}
              className="p-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex flex-col items-center gap-2"
            >
              <FolderOpen className="w-8 h-8 text-green-500" />
              <span className="text-slate-800 font-medium">Open Project</span>
              <span className="text-slate-500 text-xs">Open existing project folder</span>
            </button>
            <button
              onClick={() => { setProjectPanelOpen(true); setActiveTab('create'); }}
              className="p-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex flex-col items-center gap-2"
            >
              <Plus className="w-8 h-8 text-blue-500" />
              <span className="text-slate-800 font-medium">New Project</span>
              <span className="text-slate-500 text-xs">Create project configuration</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Project panel modal (for open/create when project is already open)
  if (isProjectPanelOpen) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl p-6 max-w-xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-slate-200">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-800">
              {activeTab === 'open' ? 'Open Project' : activeTab === 'create' ? 'Create Project' : 'Recent Projects'}
            </h2>
            <button
              onClick={() => setProjectPanelOpen(false)}
              className="p-1 hover:bg-slate-100 rounded"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-200 mb-4">
            <button
              onClick={() => setActiveTab('open')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'open'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <FolderOpen className="w-4 h-4 inline mr-2" />
              Open
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'create'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Plus className="w-4 h-4 inline mr-2" />
              Create
            </button>
            <button
              onClick={() => setActiveTab('recent')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'recent'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Clock className="w-4 h-4 inline mr-2" />
              Recent
            </button>
            <button
              onClick={() => { setActiveTab('all'); fetchAllProjects(); }}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'all'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Folder className="w-4 h-4 inline mr-2" />
              All ({allProjects.length})
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
              <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">×</button>
            </div>
          )}

          {/* Open Tab */}
          {activeTab === 'open' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Project Directory
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={openPath}
                    onChange={(e) => { setOpenPath(e.target.value); setScannedProjects([]); }}
                    placeholder="C:\path\to\project"
                    className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    onKeyDown={(e) => e.key === 'Enter' && handleScanDirectory()}
                  />
                  <button
                    onClick={handleScanDirectory}
                    disabled={isScanning || !openPath.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isScanning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    Scan
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Scan directory for project configs (*.normcode-canvas.json)
                </p>
              </div>

              {/* Scanned projects list */}
              {scannedProjects.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-slate-700">
                    Found {scannedProjects.length} project{scannedProjects.length > 1 ? 's' : ''} in this directory:
                  </h3>
                  {scannedProjects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => handleOpenScannedProject(project)}
                      disabled={isLoading}
                      className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors flex items-center gap-3 disabled:opacity-50"
                    >
                      <File className="w-5 h-5 text-blue-500" />
                      <div className="flex-1 min-w-0">
                        <div className="text-slate-800 font-medium">{project.name}</div>
                        <div className="text-slate-500 text-xs truncate">
                          {project.config_file}
                          {project.description && <span className="text-slate-400 ml-2">— {project.description}</span>}
                        </div>
                      </div>
                      <FolderOpen className="w-4 h-4 text-blue-400" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Create Tab */}
          {activeTab === 'create' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Project Directory *
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={createPath}
                    onChange={(e) => handleCreatePathChange(e.target.value)}
                    placeholder="C:\path\to\project"
                    className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    onKeyDown={(e) => e.key === 'Enter' && handleDiscoverPaths()}
                  />
                  <button
                    onClick={handleDiscoverPaths}
                    disabled={isDiscovering || !createPath.trim()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    title="Auto-discover repository files and paradigm directory"
                  >
                    {isDiscovering ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    Discover
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Click "Discover" to auto-detect concepts, inferences, and paradigm directory
                </p>
              </div>
              
              {/* Discovery results indicator */}
              {discoveredPaths && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-sm">
                  <div className="font-medium text-purple-700 mb-2">Auto-discovered paths:</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className={discoveredPaths.concepts_exists ? 'text-green-600' : 'text-slate-400'}>
                      ✓ Concepts: {discoveredPaths.concepts || '(not found)'}
                    </div>
                    <div className={discoveredPaths.inferences_exists ? 'text-green-600' : 'text-slate-400'}>
                      ✓ Inferences: {discoveredPaths.inferences || '(not found)'}
                    </div>
                    <div className={discoveredPaths.inputs_exists ? 'text-green-600' : 'text-slate-400'}>
                      {discoveredPaths.inputs ? `✓ Inputs: ${discoveredPaths.inputs}` : '○ Inputs: (optional, not found)'}
                    </div>
                    <div className={discoveredPaths.paradigm_dir_exists ? 'text-green-600' : 'text-slate-400'}>
                      {discoveredPaths.paradigm_dir ? `✓ Paradigm: ${discoveredPaths.paradigm_dir}` : '○ Paradigm: (optional, not found)'}
                    </div>
                  </div>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Project Name *
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My NormCode Project"
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Repository paths */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                    Concepts File
                    {discoveredPaths?.concepts_exists && conceptsPath === discoveredPaths.concepts && (
                      <span className="text-xs text-green-600 font-normal">(discovered)</span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={conceptsPath}
                    onChange={(e) => setConceptsPath(e.target.value)}
                    placeholder="concepts.json"
                    className={`w-full px-3 py-2 bg-white border rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm ${
                      discoveredPaths?.concepts_exists && conceptsPath === discoveredPaths.concepts 
                        ? 'border-green-400 bg-green-50' 
                        : 'border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                    Inferences File
                    {discoveredPaths?.inferences_exists && inferencesPath === discoveredPaths.inferences && (
                      <span className="text-xs text-green-600 font-normal">(discovered)</span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={inferencesPath}
                    onChange={(e) => setInferencesPath(e.target.value)}
                    placeholder="inferences.json"
                    className={`w-full px-3 py-2 bg-white border rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm ${
                      discoveredPaths?.inferences_exists && inferencesPath === discoveredPaths.inferences 
                        ? 'border-green-400 bg-green-50' 
                        : 'border-slate-300'
                    }`}
                  />
                </div>
              </div>

              {/* Advanced settings toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800"
              >
                {showAdvanced ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                Advanced Settings
              </button>

              {showAdvanced && (
                <div className="space-y-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                      Inputs File (optional)
                      {discoveredPaths?.inputs_exists && inputsPath === discoveredPaths.inputs && (
                        <span className="text-xs text-green-600 font-normal">(discovered)</span>
                      )}
                    </label>
                    <input
                      type="text"
                      value={inputsPath}
                      onChange={(e) => setInputsPath(e.target.value)}
                      placeholder="inputs.json"
                      className={`w-full px-3 py-2 bg-white border rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm ${
                        discoveredPaths?.inputs_exists && inputsPath === discoveredPaths.inputs 
                          ? 'border-green-400 bg-green-50' 
                          : 'border-slate-300'
                      }`}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                      Paradigm Directory (optional)
                      {discoveredPaths?.paradigm_dir_exists && paradigmDir === discoveredPaths.paradigm_dir && (
                        <span className="text-xs text-green-600 font-normal">(discovered)</span>
                      )}
                    </label>
                    <input
                      type="text"
                      value={paradigmDir}
                      onChange={(e) => setParadigmDir(e.target.value)}
                      placeholder="provision/paradigm"
                      className={`w-full px-3 py-2 bg-white border rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm ${
                        discoveredPaths?.paradigm_dir_exists && paradigmDir === discoveredPaths.paradigm_dir 
                          ? 'border-green-400 bg-green-50' 
                          : 'border-slate-300'
                      }`}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        LLM Model
                      </label>
                      <select
                        value={llmModel}
                        onChange={(e) => setLlmModel(e.target.value)}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      >
                        {availableModels.map((model) => (
                          <option key={model} value={model}>{model}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Max Cycles
                      </label>
                      <input
                        type="number"
                        value={maxCycles}
                        onChange={(e) => setMaxCycles(parseInt(e.target.value) || 50)}
                        min={1}
                        max={1000}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={handleCreateProject}
                disabled={isLoading || !createPath.trim() || !projectName.trim()}
                className="w-full py-2 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Create Project
              </button>
            </div>
          )}

          {/* Recent Tab */}
          {activeTab === 'recent' && (
            <div className="space-y-2">
              {recentProjects.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No recent projects</p>
              ) : (
                recentProjects.map((project) => (
                  <div
                    key={project.id}
                    onClick={() => !isLoading && handleOpenRecent(project)}
                    className={`w-full text-left p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex items-center gap-3 group cursor-pointer ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
                  >
                    <Folder className="w-5 h-5 text-blue-500" />
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-800 font-medium truncate">{project.name}</div>
                      <div className="text-slate-500 text-xs truncate flex items-center gap-1">
                        <File className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{project.config_file}</span>
                        <span className="text-slate-400 mx-1 flex-shrink-0">in</span>
                        <span className="truncate">{project.directory}</span>
                      </div>
                    </div>
                    <div className="text-slate-400 text-xs flex-shrink-0">
                      {project.last_opened ? new Date(project.last_opened).toLocaleDateString() : ''}
                    </div>
                    <button
                      onClick={(e) => handleRemoveFromRegistry(e, project.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity flex-shrink-0"
                      title="Remove from list"
                    >
                      <Trash2 className="w-4 h-4 text-red-400 hover:text-red-600" />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
          
          {/* All Projects Tab */}
          {activeTab === 'all' && (
            <div className="space-y-2">
              {allProjects.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No registered projects</p>
              ) : (
                <>
                  <p className="text-xs text-slate-500 mb-2">
                    {allProjects.length} project{allProjects.length !== 1 ? 's' : ''} registered
                  </p>
                  {allProjects.map((project) => (
                    <div
                      key={project.id}
                      onClick={() => !isLoading && handleOpenRecent(project)}
                      className={`w-full text-left p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex items-center gap-3 group cursor-pointer ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
                    >
                      <Folder className="w-5 h-5 text-blue-500" />
                      <div className="flex-1 min-w-0">
                        <div className="text-slate-800 font-medium truncate">{project.name}</div>
                        <div className="text-slate-500 text-xs truncate flex items-center gap-1">
                          <File className="w-3 h-3 flex-shrink-0" />
                          <span className="truncate">{project.config_file}</span>
                        </div>
                        <div className="text-slate-400 text-xs truncate">{project.directory}</div>
                      </div>
                      <button
                        onClick={(e) => handleRemoveFromRegistry(e, project.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity flex-shrink-0"
                        title="Remove from registry"
                      >
                        <Trash2 className="w-4 h-4 text-red-400 hover:text-red-600" />
                      </button>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // When project is open and panel is not shown, render nothing
  // (Project header is now in App.tsx)
  return null;
}
