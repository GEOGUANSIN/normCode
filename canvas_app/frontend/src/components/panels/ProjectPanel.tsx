/**
 * ProjectPanel - Project management UI
 * Provides open project, create project, and recent projects functionality.
 * Supports multiple projects per directory.
 * Supports export/import of portable project archives.
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
  Trash2,
  Download,
  Upload,
  Package,
  FileArchive,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import { usePortableStore } from '../../stores/portableStore';
import { projectApi } from '../../services/api';
import type { RegisteredProject, DiscoveredPathsResponse } from '../../types/project';

type TabType = 'open' | 'create' | 'recent' | 'all' | 'export' | 'import';

export function ProjectPanel() {
  const {
    currentProject,
    projectPath,
    recentProjects,
    allProjects,
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
  const [maxCycles, setMaxCycles] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Discovery state
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredPaths, setDiscoveredPaths] = useState<DiscoveredPathsResponse | null>(null);
  
  // Export/Import state
  const [exportOutputDir, setExportOutputDir] = useState('');  // Empty = project directory
  const [exportIncludeDb, setExportIncludeDb] = useState(true);
  const [exportIncludeLogs, setExportIncludeLogs] = useState(true);
  const [importPath, setImportPath] = useState('');
  const [importTargetDir, setImportTargetDir] = useState('');
  const [importNewName, setImportNewName] = useState('');  // Empty = keep original name
  const [importOverwrite, setImportOverwrite] = useState(false);
  
  // Portable store
  const {
    isExporting,
    isImporting,
    isPreviewing,
    lastExportResult,
    lastImportResult,
    previewInfo,
    availableExports,
    error: portableError,
    quickExport,
    previewArchive,
    importProject,
    fetchAvailableExports,
    clearPreview,
    setError: setPortableError,
  } = usePortableStore();

  // Fetch config on mount
  useEffect(() => {
    fetchRecentProjects();
    fetchAllProjects();
  }, [fetchRecentProjects, fetchAllProjects]);
  
  // Fetch available exports when import tab is active
  useEffect(() => {
    if (activeTab === 'import') {
      fetchAvailableExports();
    }
  }, [activeTab, fetchAvailableExports]);

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
      
      // Show message about what was discovered
      const foundItems = [];
      if (discovered.concepts) foundItems.push('concepts');
      if (discovered.inferences) foundItems.push('inferences');
      if (discovered.inputs) foundItems.push('inputs');
      if (discovered.paradigm_dir) foundItems.push('paradigm (for agent)');
      
      if (foundItems.length === 0) {
        setError('No repository files found in this directory');
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
      maxCycles,
      // Note: paradigm_dir and llm_model are now configured per-agent, not per-project.
      // A default agent config will be auto-created with these settings detected from discovery.
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
        <div className="bg-white rounded-xl shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-slate-200">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-800">
              {activeTab === 'open' ? 'Open Project' : 
               activeTab === 'create' ? 'Create Project' : 
               activeTab === 'export' ? 'Export Project' :
               activeTab === 'import' ? 'Import Project' :
               'Recent Projects'}
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
            <div className="flex-1" />
            <button
              onClick={() => setActiveTab('export')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'export'
                  ? 'text-emerald-600 border-b-2 border-emerald-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Download className="w-4 h-4 inline mr-1" />
              Export
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'import'
                  ? 'text-orange-600 border-b-2 border-orange-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-1" />
              Import
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
                  
                  {/* Agent-centric note */}
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="text-xs text-purple-700">
                      <span className="font-semibold">💡 Note:</span> LLM model and paradigm directory are now configured per-agent.
                      A default agent will be created automatically and can be customized in the Agent Panel after project creation.
                    </div>
                    {discoveredPaths?.paradigm_dir_exists && discoveredPaths.paradigm_dir && (
                      <div className="mt-2 text-xs text-green-600">
                        ✓ Discovered paradigm directory: <span className="font-mono">{discoveredPaths.paradigm_dir}</span> 
                        (will be set in default agent)
                      </div>
                    )}
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
          
          {/* Export Tab */}
          {activeTab === 'export' && (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                <div className="flex items-center gap-3 mb-3">
                  <Package className="w-6 h-6 text-emerald-600" />
                  <div>
                    <h3 className="font-medium text-emerald-800">Export Current Project</h3>
                    <p className="text-xs text-emerald-600">Create a portable archive with all project data</p>
                  </div>
                </div>
                
                {currentProject ? (
                  <div className="space-y-3">
                    <div className="p-3 bg-white rounded border border-emerald-200">
                      <div className="text-sm font-medium text-slate-800">{currentProject.name}</div>
                      <div className="text-xs text-slate-500">{projectPath}</div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Output Directory
                      </label>
                      <input
                        type="text"
                        value={exportOutputDir}
                        onChange={(e) => setExportOutputDir(e.target.value)}
                        placeholder={projectPath || 'Project directory (default)'}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        Leave empty to export to project directory
                      </p>
                    </div>
                    
                    <p className="text-xs text-slate-600 mb-2">
                      The export will always include: project configuration, repositories, and provisions.
                    </p>
                    
                    <div className="space-y-2 p-3 bg-white rounded border border-emerald-200">
                      <label className="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={exportIncludeDb}
                          onChange={(e) => setExportIncludeDb(e.target.checked)}
                          className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                        Include execution database (runs, checkpoints)
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={exportIncludeLogs}
                          onChange={(e) => setExportIncludeLogs(e.target.checked)}
                          className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                          disabled={!exportIncludeDb}
                        />
                        <span className={!exportIncludeDb ? 'text-slate-400' : ''}>
                          Include log files
                        </span>
                      </label>
                    </div>
                    
                    <button
                      onClick={() => quickExport(currentProject.id, { 
                        includeDatabase: exportIncludeDb, 
                        includeLogs: exportIncludeLogs, 
                        outputDir: exportOutputDir 
                      })}
                      disabled={isExporting}
                      className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isExporting ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4" />
                          Export Project
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Open a project first to export it.</p>
                )}
              </div>
              
              {/* Last export result */}
              {lastExportResult && (
                <div className={`p-3 rounded-lg border ${
                  lastExportResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    {lastExportResult.success ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className={`text-sm font-medium ${
                      lastExportResult.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {lastExportResult.success ? 'Export Successful' : 'Export Failed'}
                    </span>
                  </div>
                  {lastExportResult.output_path && (
                    <p className="text-xs text-slate-600 break-all">{lastExportResult.output_path}</p>
                  )}
                  {lastExportResult.success && lastExportResult.archive_size && (
                    <p className="text-xs text-slate-500 mt-1">
                      {lastExportResult.files_count} files, {(lastExportResult.archive_size / 1024).toFixed(1)} KB
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* Import Tab */}
          {activeTab === 'import' && (
            <div className="space-y-4">
              {portableError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {portableError}
                  <button onClick={() => setPortableError(null)} className="ml-2 text-red-500 hover:text-red-700">×</button>
                </div>
              )}
              
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-center gap-3 mb-3">
                  <FileArchive className="w-6 h-6 text-orange-600" />
                  <div>
                    <h3 className="font-medium text-orange-800">Import Portable Project</h3>
                    <p className="text-xs text-orange-600">Restore a project from a portable archive</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Archive Path
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={importPath}
                        onChange={(e) => { setImportPath(e.target.value); clearPreview(); }}
                        placeholder="C:\path\to\project.normcode-portable.zip"
                        className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                      />
                      <button
                        onClick={() => previewArchive(importPath)}
                        disabled={isPreviewing || !importPath.trim()}
                        className="px-3 py-2 bg-orange-600 hover:bg-orange-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        {isPreviewing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        Preview
                      </button>
                    </div>
                  </div>
                  
                  {/* Preview info */}
                  {previewInfo && (
                    <div className="p-3 bg-white rounded border border-orange-200 space-y-2">
                      <div className="flex items-center gap-2">
                        <Package className="w-5 h-5 text-orange-500" />
                        <span className="font-medium text-slate-800">{previewInfo.project_name}</span>
                      </div>
                      {previewInfo.project_description && (
                        <p className="text-xs text-slate-500">{previewInfo.project_description}</p>
                      )}
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="text-slate-600">
                          <span className="text-slate-400">Files:</span> {previewInfo.files_count}
                        </div>
                        <div className="text-slate-600">
                          <span className="text-slate-400">Size:</span> {(previewInfo.archive_size / 1024).toFixed(1)} KB
                        </div>
                        <div className="text-slate-600">
                          <span className="text-slate-400">Database:</span> {previewInfo.has_database ? 'Yes' : 'No'}
                        </div>
                        <div className="text-slate-600">
                          <span className="text-slate-400">Runs:</span> {previewInfo.runs_count}
                        </div>
                      </div>
                      {/* Repository files */}
                      {previewInfo.repositories && Object.keys(previewInfo.repositories).length > 0 && (
                        <div className="text-xs text-slate-500 pt-1 border-t border-orange-100">
                          <span className="text-slate-400">Repositories:</span>{' '}
                          {Object.entries(previewInfo.repositories)
                            .filter(([, v]) => v)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(', ') || 'None'}
                        </div>
                      )}
                      {Object.keys(previewInfo.provisions).length > 0 && (
                        <div className="text-xs text-slate-500">
                          <span className="text-slate-400">Provisions:</span> {Object.keys(previewInfo.provisions).join(', ')}
                        </div>
                      )}
                      <div className="text-xs text-slate-400">
                        Exported: {new Date(previewInfo.exported_at).toLocaleString()}
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={importNewName}
                      onChange={(e) => setImportNewName(e.target.value)}
                      placeholder={previewInfo?.project_name || 'Keep original name'}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Leave empty to keep the original project name
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Import Location
                    </label>
                    <input
                      type="text"
                      value={importTargetDir}
                      onChange={(e) => setImportTargetDir(e.target.value)}
                      placeholder="C:\path\to\projects"
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Project will be created in a subdirectory: <span className="font-mono text-orange-600">
                        {importTargetDir ? `${importTargetDir}\\${(importNewName || previewInfo?.project_name || 'project').toLowerCase().replace(/\s+/g, '-')}` : '(select location)'}
                      </span>
                    </p>
                  </div>
                  
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={importOverwrite}
                      onChange={(e) => setImportOverwrite(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    Overwrite existing files
                  </label>
                  
                  <button
                    onClick={async () => {
                      const result = await importProject(importPath, {
                        target_directory: importTargetDir,
                        new_project_name: importNewName || undefined,
                        overwrite_existing: importOverwrite,
                        import_database: true,
                        import_runs: true,
                      });
                      if (result?.success) {
                        setImportPath('');
                        setImportTargetDir('');
                        setImportNewName('');
                        clearPreview();
                        // Open the imported project
                        if (result.project_id) {
                          await openProjectAction(result.project_path || undefined, result.config_file || undefined, result.project_id);
                        }
                      }
                    }}
                    disabled={isImporting || !importPath.trim() || !importTargetDir.trim()}
                    className="w-full py-2 bg-orange-600 hover:bg-orange-500 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isImporting ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Importing...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Import Project
                      </>
                    )}
                  </button>
                </div>
              </div>
              
              {/* Last import result */}
              {lastImportResult && (
                <div className={`p-3 rounded-lg border ${
                  lastImportResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    {lastImportResult.success ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className={`text-sm font-medium ${
                      lastImportResult.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {lastImportResult.success ? 'Import Successful' : 'Import Failed'}
                    </span>
                  </div>
                  {lastImportResult.project_path && (
                    <p className="text-xs text-slate-600 break-all">{lastImportResult.project_path}</p>
                  )}
                  {lastImportResult.success && (
                    <p className="text-xs text-slate-500 mt-1">
                      {lastImportResult.files_imported} files, {lastImportResult.runs_imported} runs imported
                    </p>
                  )}
                  {lastImportResult.warnings.length > 0 && (
                    <div className="mt-2 text-xs text-amber-600">
                      {lastImportResult.warnings.slice(0, 3).map((w, i) => (
                        <div key={i}>⚠ {w}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* Available exports */}
              {availableExports.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                    <FileArchive className="w-4 h-4" />
                    Recent Exports
                  </h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {availableExports.map((exp, i) => (
                      <button
                        key={i}
                        onClick={() => setImportPath(exp.path)}
                        className="w-full text-left p-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
                      >
                        <div className="text-sm text-slate-800 truncate">{exp.filename}</div>
                        <div className="text-xs text-slate-500 flex items-center gap-2">
                          {exp.project_name && <span>{exp.project_name}</span>}
                          {exp.exported_at && <span>• {new Date(exp.exported_at).toLocaleDateString()}</span>}
                          {exp.size && <span>• {(exp.size / 1024).toFixed(1)} KB</span>}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
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
