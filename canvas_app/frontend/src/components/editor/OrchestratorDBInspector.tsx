/**
 * OrchestratorDBInspector - Component for inspecting orchestrator databases.
 * 
 * Provides a comprehensive UI for:
 * - Browsing database structure and tables
 * - Viewing run executions and logs
 * - Inspecting checkpoint states (blackboard, workspace, concepts)
 * - Viewing run statistics
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Database,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Table,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Play,
  FileText,
  BarChart3,
  Box,
  Layers,
  Search,
  FolderOpen,
  X,
  Loader2,
} from 'lucide-react';
import {
  dbInspectorApi,
  checkpointApi,
  type DatabaseOverview,
  type RunStatistics,
  type ExecutionRecord,
  type BlackboardSummary,
  type CheckpointStateResponse,
  type RunInfo,
  type CheckpointInfo,
} from '../../services/api';

interface OrchestratorDBInspectorProps {
  /** Initial database path to load */
  initialDbPath?: string;
  /** Callback when path changes */
  onPathChange?: (path: string) => void;
  /** Custom class name */
  className?: string;
}

type ViewMode = 'overview' | 'runs' | 'executions' | 'checkpoints' | 'blackboard' | 'concepts' | 'query';

export function OrchestratorDBInspector({
  initialDbPath = '',
  onPathChange,
  className = '',
}: OrchestratorDBInspectorProps) {
  // Database path state
  const [dbPath, setDbPath] = useState(initialDbPath);
  const [inputPath, setInputPath] = useState(initialDbPath);
  
  // Loading and error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // View mode
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  
  // Data states
  const [overview, setOverview] = useState<DatabaseOverview | null>(null);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [checkpoints, setCheckpoints] = useState<CheckpointInfo[]>([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<number | null>(null);
  
  // Detail states
  const [statistics, setStatistics] = useState<RunStatistics | null>(null);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [blackboard, setBlackboard] = useState<BlackboardSummary | null>(null);
  const [checkpointState, setCheckpointState] = useState<CheckpointStateResponse | null>(null);
  const [concepts, setConcepts] = useState<Record<string, unknown> | null>(null);
  
  // Expanded sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['runs', 'views']));
  
  // Auto-load flag
  const [hasAutoLoaded, setHasAutoLoaded] = useState(false);
  
  // Load database when path changes
  const loadDatabase = useCallback(async (path: string) => {
    if (!path) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Check if database exists
      const dbCheck = await checkpointApi.checkDbExists(path);
      if (!dbCheck.exists) {
        setError(`Database not found: ${path}`);
        setOverview(null);
        setRuns([]);
        return;
      }
      
      // Load overview
      const overviewData = await dbInspectorApi.getOverview(path);
      setOverview(overviewData);
      
      // Load runs
      const runsList = await checkpointApi.listRuns(path);
      setRuns(runsList);
      
      // Auto-select first run
      if (runsList.length > 0) {
        setSelectedRun(runsList[0].run_id);
      }
      
      onPathChange?.(path);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to load database';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [onPathChange]);
  
  // Auto-load database on mount if initialDbPath is provided
  useEffect(() => {
    if (initialDbPath && !hasAutoLoaded) {
      setHasAutoLoaded(true);
      setDbPath(initialDbPath);
      setInputPath(initialDbPath);
      loadDatabase(initialDbPath);
    }
  }, [initialDbPath, hasAutoLoaded, loadDatabase]);
  
  // Load checkpoints when run is selected
  useEffect(() => {
    if (!selectedRun || !dbPath) return;
    
    const loadRunData = async () => {
      try {
        // Load checkpoints
        const cpList = await checkpointApi.listCheckpoints(selectedRun, dbPath);
        setCheckpoints(cpList);
        
        // Auto-select latest checkpoint
        if (cpList.length > 0) {
          setSelectedCheckpoint(cpList[cpList.length - 1].cycle);
        }
        
        // Load statistics
        const stats = await dbInspectorApi.getRunStatistics(selectedRun, dbPath);
        setStatistics(stats);
      } catch (e) {
        console.error('Failed to load run data:', e);
      }
    };
    
    loadRunData();
  }, [selectedRun, dbPath]);
  
  // Load view-specific data
  useEffect(() => {
    if (!selectedRun || !dbPath) return;
    
    const loadViewData = async () => {
      setLoading(true);
      try {
        switch (viewMode) {
          case 'executions':
            const execData = await dbInspectorApi.getExecutionHistory(
              selectedRun, dbPath, { includeLogs: false, limit: 200 }
            );
            setExecutions(execData.executions);
            break;
          case 'blackboard':
            const bb = await dbInspectorApi.getBlackboardSummary(
              selectedRun, dbPath, selectedCheckpoint ?? undefined
            );
            setBlackboard(bb);
            break;
          case 'checkpoints':
            if (selectedCheckpoint !== null) {
              const cpState = await dbInspectorApi.getCheckpointState(
                selectedRun, selectedCheckpoint, dbPath
              );
              setCheckpointState(cpState);
            }
            break;
          case 'concepts':
            const conceptData = await dbInspectorApi.getCompletedConcepts(
              selectedRun, dbPath, selectedCheckpoint ?? undefined
            );
            setConcepts(conceptData.concepts);
            break;
        }
      } catch (e) {
        console.error('Failed to load view data:', e);
      } finally {
        setLoading(false);
      }
    };
    
    loadViewData();
  }, [viewMode, selectedRun, selectedCheckpoint, dbPath]);
  
  const handleLoadPath = () => {
    setDbPath(inputPath);
    loadDatabase(inputPath);
  };
  
  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };
  
  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  const formatDate = (isoString: string | null) => {
    if (!isoString) return '—';
    const date = new Date(isoString);
    return date.toLocaleString();
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'complete':
        return 'text-emerald-600 bg-emerald-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      case 'in_progress':
      case 'pending':
        return 'text-amber-600 bg-amber-50';
      default:
        return 'text-slate-600 bg-slate-50';
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'complete':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'failed':
        return <XCircle className="w-3 h-3" />;
      case 'in_progress':
        return <Play className="w-3 h-3" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  return (
    <div className={`flex flex-col h-full bg-slate-50 ${className}`}>
      {/* Header with path input */}
      <div className="flex-shrink-0 border-b border-slate-200 bg-white p-3">
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-800 text-sm">Orchestrator DB Inspector</span>
        </div>
        
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLoadPath()}
              placeholder="Enter database path (e.g., ./orchestration.db)"
              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono"
            />
            <FolderOpen className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          </div>
          <button
            onClick={handleLoadPath}
            disabled={loading || !inputPath}
            className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            Load
          </button>
        </div>
        
        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md flex items-center gap-2 text-red-700 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
      
      {/* Main content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left sidebar - navigation */}
        <div className="w-56 flex-shrink-0 border-r border-slate-200 bg-white overflow-y-auto">
          {overview && (
            <>
              {/* Overview section */}
              <div className="border-b border-slate-100">
                <button
                  onClick={() => toggleSection('overview')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  {expandedSections.has('overview') ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  <Database className="w-3 h-3" />
                  Database Overview
                </button>
                {expandedSections.has('overview') && (
                  <div className="px-3 pb-2 space-y-1">
                    <button
                      onClick={() => setViewMode('overview')}
                      className={`w-full text-left px-2 py-1 text-xs rounded ${
                        viewMode === 'overview' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Table className="w-3 h-3" />
                        Tables & Structure
                      </div>
                    </button>
                  </div>
                )}
              </div>
              
              {/* Runs section */}
              <div className="border-b border-slate-100">
                <button
                  onClick={() => toggleSection('runs')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  {expandedSections.has('runs') ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  <Play className="w-3 h-3" />
                  Runs ({runs.length})
                </button>
                {expandedSections.has('runs') && (
                  <div className="px-3 pb-2 space-y-1 max-h-48 overflow-y-auto">
                    {runs.map((run) => (
                      <button
                        key={run.run_id}
                        onClick={() => {
                          setSelectedRun(run.run_id);
                          setViewMode('executions');
                        }}
                        className={`w-full text-left px-2 py-1.5 text-xs rounded ${
                          selectedRun === run.run_id
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <div className="font-mono truncate" title={run.run_id}>
                          {run.run_id.slice(0, 12)}...
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Cycle {run.max_cycle} • {run.execution_count} execs
                        </div>
                      </button>
                    ))}
                    {runs.length === 0 && (
                      <div className="text-xs text-slate-400 italic px-2">No runs found</div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Views section */}
              {selectedRun && (
                <div className="border-b border-slate-100">
                  <button
                    onClick={() => toggleSection('views')}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
                  >
                    {expandedSections.has('views') ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                    <Layers className="w-3 h-3" />
                    Views
                  </button>
                  {expandedSections.has('views') && (
                    <div className="px-3 pb-2 space-y-1">
                      <button
                        onClick={() => setViewMode('executions')}
                        className={`w-full text-left px-2 py-1 text-xs rounded flex items-center gap-2 ${
                          viewMode === 'executions' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <FileText className="w-3 h-3" />
                        Executions
                      </button>
                      <button
                        onClick={() => setViewMode('checkpoints')}
                        className={`w-full text-left px-2 py-1 text-xs rounded flex items-center gap-2 ${
                          viewMode === 'checkpoints' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Clock className="w-3 h-3" />
                        Checkpoints
                      </button>
                      <button
                        onClick={() => setViewMode('blackboard')}
                        className={`w-full text-left px-2 py-1 text-xs rounded flex items-center gap-2 ${
                          viewMode === 'blackboard' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Box className="w-3 h-3" />
                        Blackboard
                      </button>
                      <button
                        onClick={() => setViewMode('concepts')}
                        className={`w-full text-left px-2 py-1 text-xs rounded flex items-center gap-2 ${
                          viewMode === 'concepts' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <Layers className="w-3 h-3" />
                        Concepts
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              {/* Checkpoints selector */}
              {selectedRun && checkpoints.length > 0 && (
                <div className="p-3 border-b border-slate-100">
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Checkpoint</label>
                  <select
                    value={selectedCheckpoint ?? ''}
                    onChange={(e) => setSelectedCheckpoint(e.target.value ? Number(e.target.value) : null)}
                    className="w-full text-xs border border-slate-300 rounded px-2 py-1 focus:ring-1 focus:ring-indigo-500"
                  >
                    {checkpoints.map((cp) => (
                      <option key={`${cp.cycle}-${cp.inference_count}`} value={cp.cycle}>
                        Cycle {cp.cycle} ({cp.inference_count} infs)
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}
          
          {!overview && !loading && dbPath && (
            <div className="p-4 text-center text-slate-400 text-xs">
              No database loaded
            </div>
          )}
        </div>
        
        {/* Main content area */}
        <div className="flex-1 overflow-auto p-4">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          )}
          
          {!loading && viewMode === 'overview' && overview && (
            <OverviewView overview={overview} formatBytes={formatBytes} />
          )}
          
          {!loading && viewMode === 'executions' && (
            <ExecutionsView
              executions={executions}
              statistics={statistics}
              formatDate={formatDate}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
            />
          )}
          
          {!loading && viewMode === 'checkpoints' && checkpointState && (
            <CheckpointView checkpointState={checkpointState} />
          )}
          
          {!loading && viewMode === 'blackboard' && blackboard && (
            <BlackboardView
              blackboard={blackboard}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
            />
          )}
          
          {!loading && viewMode === 'concepts' && concepts && (
            <ConceptsView concepts={concepts} />
          )}
          
          {!loading && !overview && dbPath && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <Database className="w-12 h-12 mb-2 opacity-30" />
              <p className="text-sm">Enter a database path and click Load</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Sub-components for different views
// ============================================================================

function OverviewView({
  overview,
  formatBytes,
}: {
  overview: DatabaseOverview;
  formatBytes: (bytes: number) => string;
}) {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" />
          Database Info
        </h3>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-500">Path:</span>
            <span className="ml-2 font-mono text-slate-700 break-all">{overview.path}</span>
          </div>
          <div>
            <span className="text-slate-500">Size:</span>
            <span className="ml-2 text-slate-700">{formatBytes(overview.size_bytes)}</span>
          </div>
          <div>
            <span className="text-slate-500">Runs:</span>
            <span className="ml-2 text-slate-700">{overview.run_count}</span>
          </div>
          <div>
            <span className="text-slate-500">Total Executions:</span>
            <span className="ml-2 text-slate-700">{overview.total_executions}</span>
          </div>
          <div>
            <span className="text-slate-500">Total Checkpoints:</span>
            <span className="ml-2 text-slate-700">{overview.total_checkpoints}</span>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Table className="w-4 h-4 text-indigo-600" />
          Tables
        </h3>
        <div className="space-y-3">
          {overview.tables.map((table) => (
            <div key={table.name} className="border border-slate-100 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-sm text-slate-800">{table.name}</span>
                <span className="text-xs text-slate-500">{table.row_count} rows</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {table.columns.map((col) => (
                  <span
                    key={col.name}
                    className="px-1.5 py-0.5 bg-slate-100 rounded text-[10px] font-mono text-slate-600"
                    title={col.type}
                  >
                    {col.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ExecutionsView({
  executions,
  statistics,
  formatDate,
  getStatusColor,
  getStatusIcon,
}: {
  executions: ExecutionRecord[];
  statistics: RunStatistics | null;
  formatDate: (s: string | null) => string;
  getStatusColor: (s: string) => string;
  getStatusIcon: (s: string) => React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      {statistics && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-indigo-600" />
            Run Statistics
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-slate-50 rounded-lg">
              <div className="text-2xl font-bold text-slate-800">{statistics.total_executions}</div>
              <div className="text-xs text-slate-500">Total Executions</div>
            </div>
            <div className="text-center p-3 bg-emerald-50 rounded-lg">
              <div className="text-2xl font-bold text-emerald-600">{statistics.completed}</div>
              <div className="text-xs text-emerald-600">Completed</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{statistics.failed}</div>
              <div className="text-xs text-red-600">Failed</div>
            </div>
            <div className="text-center p-3 bg-indigo-50 rounded-lg">
              <div className="text-2xl font-bold text-indigo-600">{statistics.cycles_completed}</div>
              <div className="text-xs text-indigo-600">Cycles</div>
            </div>
          </div>
          
          {Object.keys(statistics.execution_by_type).length > 0 && (
            <div className="mt-4">
              <div className="text-xs font-medium text-slate-600 mb-2">By Inference Type</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(statistics.execution_by_type).map(([type, count]) => (
                  <span
                    key={type}
                    className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-700"
                  >
                    {type}: {count}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="px-4 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            Execution History ({executions.length})
          </h3>
        </div>
        <div className="max-h-[500px] overflow-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">ID</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Cycle</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Flow Index</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Type</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Concept</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Status</th>
                <th className="px-3 py-2 text-left text-slate-600 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {executions.map((exec) => (
                <tr key={exec.id} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-slate-500">{exec.id}</td>
                  <td className="px-3 py-2">{exec.cycle}</td>
                  <td className="px-3 py-2 font-mono">{exec.flow_index}</td>
                  <td className="px-3 py-2">{exec.inference_type || '—'}</td>
                  <td className="px-3 py-2 font-mono truncate max-w-[150px]" title={exec.concept_inferred}>
                    {exec.concept_inferred || '—'}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${getStatusColor(exec.status)}`}>
                      {getStatusIcon(exec.status)}
                      {exec.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500">{formatDate(exec.timestamp ?? null)}</td>
                </tr>
              ))}
              {executions.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-slate-400">
                    No executions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function CheckpointView({ checkpointState }: { checkpointState: CheckpointStateResponse }) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());
  
  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };
  
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-600" />
          Checkpoint: Cycle {checkpointState.cycle}, Inference {checkpointState.inference_count}
        </h3>
        <div className="text-xs text-slate-500 mb-4">
          Timestamp: {checkpointState.timestamp}
        </div>
        
        <div className="space-y-3">
          {['blackboard', 'workspace', 'tracker', 'completed_concepts', 'signatures'].map((key) => {
            const data = checkpointState[key as keyof CheckpointStateResponse];
            if (!data) return null;
            
            return (
              <div key={key} className="border border-slate-200 rounded">
                <button
                  onClick={() => toggleKey(key)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  {expandedKeys.has(key) ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  {key}
                  <span className="text-slate-400 ml-auto">
                    {typeof data === 'object' ? Object.keys(data as object).length + ' keys' : ''}
                  </span>
                </button>
                {expandedKeys.has(key) && (
                  <div className="px-3 pb-3">
                    <pre className="text-[10px] bg-slate-50 p-2 rounded overflow-auto max-h-64 font-mono">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function BlackboardView({
  blackboard,
  getStatusColor,
  getStatusIcon,
}: {
  blackboard: BlackboardSummary;
  getStatusColor: (s: string) => string;
  getStatusIcon: (s: string) => React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-slate-800">{blackboard.concept_count}</div>
          <div className="text-xs text-slate-500">Concepts</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-emerald-600">{blackboard.completed_concepts}</div>
          <div className="text-xs text-emerald-600">Completed</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-slate-800">{blackboard.item_count}</div>
          <div className="text-xs text-slate-500">Items</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-emerald-600">{blackboard.completed_items}</div>
          <div className="text-xs text-emerald-600">Completed</div>
        </div>
      </div>
      
      {/* Concept statuses */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="px-4 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-800">Concept Statuses</h3>
        </div>
        <div className="max-h-64 overflow-auto p-2">
          <div className="flex flex-wrap gap-1">
            {Object.entries(blackboard.concept_statuses).map(([name, status]) => (
              <span
                key={name}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(status)}`}
                title={name}
              >
                {getStatusIcon(status)}
                <span className="font-mono truncate max-w-[120px]">{name}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
      
      {/* Item statuses */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="px-4 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-800">Item Statuses</h3>
        </div>
        <div className="max-h-64 overflow-auto p-2">
          <div className="flex flex-wrap gap-1">
            {Object.entries(blackboard.item_statuses).map(([flowIndex, status]) => (
              <span
                key={flowIndex}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(status)}`}
              >
                {getStatusIcon(status)}
                <span className="font-mono">{flowIndex}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ConceptsView({ concepts }: { concepts: Record<string, unknown> }) {
  const [search, setSearch] = useState('');
  const [expandedConcept, setExpandedConcept] = useState<string | null>(null);
  
  const filteredConcepts = Object.entries(concepts).filter(([name]) =>
    name.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            Completed Concepts ({Object.keys(concepts).length})
          </h3>
          <div className="flex-1" />
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search concepts..."
              className="pl-8 pr-3 py-1 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-indigo-500"
            />
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400" />
          </div>
        </div>
        
        <div className="space-y-2 max-h-[500px] overflow-auto">
          {filteredConcepts.map(([name, data]) => (
            <div key={name} className="border border-slate-200 rounded">
              <button
                onClick={() => setExpandedConcept(expandedConcept === name ? null : name)}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-mono text-slate-700 hover:bg-slate-50"
              >
                {expandedConcept === name ? (
                  <ChevronDown className="w-3 h-3 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-3 h-3 flex-shrink-0" />
                )}
                <span className="truncate">{name}</span>
                {typeof data === 'object' && data !== null && 'shape' in data && (
                  <span className="text-slate-400 ml-auto flex-shrink-0">
                    shape: [{(data as { shape?: number[] }).shape?.join(', ')}]
                  </span>
                )}
              </button>
              {expandedConcept === name && (
                <div className="px-3 pb-3">
                  <pre className="text-[10px] bg-slate-50 p-2 rounded overflow-auto max-h-48 font-mono">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
          {filteredConcepts.length === 0 && (
            <div className="text-center py-8 text-slate-400 text-xs">
              {search ? 'No concepts match your search' : 'No concepts found'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OrchestratorDBInspector;

