/**
 * CheckpointPanel - Dedicated panel for checkpoint/resume/fork operations
 * 
 * This panel allows users to:
 * - View previous runs in the checkpoint database
 * - Select a run and checkpoint to resume from
 * - Resume execution (same run_id) or Fork (new run_id)
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  RefreshCw, 
  Play, 
  GitBranch, 
  Database, 
  AlertCircle,
  Clock,
  CheckCircle2,
  X,
  Trash2,
} from 'lucide-react';
import { checkpointApi } from '../../services/api';
import { useProjectStore } from '../../stores/projectStore';
import { useConfigStore } from '../../stores/configStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { graphApi, executionApi } from '../../services/api';
import type { RunInfo, CheckpointInfo, ReconciliationMode } from '../../types/execution';

interface CheckpointPanelProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function CheckpointPanel({ isOpen, onToggle }: CheckpointPanelProps) {
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [checkpoints, setCheckpoints] = useState<CheckpointInfo[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<number | null>(null);
  const [reconciliationMode, setReconciliationMode] = useState<ReconciliationMode>('PATCH');
  const [customRunId, setCustomRunId] = useState<string>(''); // Custom run_id for Fork
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dbExists, setDbExists] = useState<boolean | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null); // Track which run is pending delete confirmation
  
  const { currentProject, projectPath, setIsLoaded } = useProjectStore();
  const { maxCycles, dbPath } = useConfigStore();
  const { setGraphData } = useGraphStore();
  const { setProgress, setNodeStatuses, setRunId } = useExecutionStore();
  
  // Compute the full database path relative to project root
  const getFullDbPath = useCallback(() => {
    if (!projectPath) return null;
    
    const relativePath = currentProject?.execution?.db_path || dbPath || 'orchestration.db';
    
    // Check if relativePath is already absolute (Windows or Unix style)
    const isAbsolute = /^[A-Za-z]:/.test(relativePath) || relativePath.startsWith('/');
    if (isAbsolute) {
      return relativePath.replace(/\\/g, '/');
    }
    
    // Use forward slashes for consistency
    const fullPath = `${projectPath}/${relativePath}`.replace(/\\/g, '/');
    return fullPath;
  }, [projectPath, currentProject, dbPath]);
  
  const fullDbPath = getFullDbPath();
  
  // Check if database exists when panel opens
  useEffect(() => {
    if (isOpen && fullDbPath) {
      checkDbAndLoadRuns();
    }
  }, [isOpen, fullDbPath]);
  
  // Load checkpoints when run is selected
  useEffect(() => {
    if (selectedRun && fullDbPath) {
      loadCheckpoints(selectedRun);
    }
  }, [selectedRun, fullDbPath]);
  
  const checkDbAndLoadRuns = async () => {
    if (!fullDbPath) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Check if database exists
      const dbCheck = await checkpointApi.checkDbExists(fullDbPath);
      setDbExists(dbCheck.exists);
      
      if (dbCheck.exists) {
        await loadRuns();
      } else {
        setRuns([]);
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to check database';
      setError(message);
      setDbExists(false);
    } finally {
      setLoading(false);
    }
  };
  
  const loadRuns = async () => {
    if (!fullDbPath) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const runList = await checkpointApi.listRuns(fullDbPath);
      setRuns(runList);
      
      // Auto-select the first run if none selected
      if (runList.length > 0 && !selectedRun) {
        setSelectedRun(runList[0].run_id);
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to load runs';
      setError(message);
    } finally {
      setLoading(false);
    }
  };
  
  const loadCheckpoints = async (runId: string) => {
    if (!fullDbPath) return;
    
    try {
      const cpList = await checkpointApi.listCheckpoints(runId, fullDbPath);
      setCheckpoints(cpList);
      
      // Auto-select the latest checkpoint
      if (cpList.length > 0) {
        setSelectedCheckpoint(cpList[0].cycle);
      }
    } catch (e: unknown) {
      console.error('Failed to load checkpoints:', e);
      setCheckpoints([]);
    }
  };

  const handleDeleteRun = async (runId: string) => {
    if (!fullDbPath) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await checkpointApi.deleteRun(runId, fullDbPath);
      if (result.success) {
        // Clear selection if deleted run was selected
        if (selectedRun === runId) {
          setSelectedRun(null);
          setCheckpoints([]);
          setSelectedCheckpoint(null);
        }
        // Reload runs
        await loadRuns();
      } else {
        setError(result.message || 'Failed to delete run');
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to delete run';
      setError(message);
    } finally {
      setLoading(false);
      setDeleteConfirmId(null);
    }
  };

  // Helper to resolve path - handles both relative and absolute paths
  const resolvePath = (relativePath: string) => {
    // Check if it's already an absolute path (Windows or Unix style)
    const isAbsolute = /^[A-Za-z]:/.test(relativePath) || relativePath.startsWith('/');
    if (isAbsolute) {
      return relativePath.replace(/\\/g, '/');
    }
    return `${projectPath}/${relativePath}`.replace(/\\/g, '/');
  };

  const handleResume = async () => {
    if (!selectedRun || !fullDbPath || !currentProject || !projectPath) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await checkpointApi.resume({
        concepts_path: resolvePath(currentProject.repositories.concepts),
        inferences_path: resolvePath(currentProject.repositories.inferences),
        inputs_path: currentProject.repositories.inputs 
          ? resolvePath(currentProject.repositories.inputs)
          : undefined,
        db_path: fullDbPath,
        run_id: selectedRun,
        cycle: selectedCheckpoint ?? undefined,
        mode: reconciliationMode,
        base_dir: projectPath,
        max_cycles: maxCycles,
      });
      
      if (result.success) {
        // Set the run_id in the store
        setRunId(result.run_id);
        // Load graph data to sync the UI
        await syncGraphAndExecution();
        setIsLoaded(true);
        onToggle(); // Close the panel on success
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to resume';
      setError(message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFork = async () => {
    if (!selectedRun || !fullDbPath || !currentProject || !projectPath) return;

    setLoading(true);
    setError(null);

    try {
      const result = await checkpointApi.fork({
        concepts_path: resolvePath(currentProject.repositories.concepts),
        inferences_path: resolvePath(currentProject.repositories.inferences),
        inputs_path: currentProject.repositories.inputs
          ? resolvePath(currentProject.repositories.inputs)
          : undefined,
        db_path: fullDbPath,
        source_run_id: selectedRun,
        new_run_id: customRunId.trim() || undefined, // Use custom or auto-generate
        cycle: selectedCheckpoint ?? undefined,
        mode: reconciliationMode,
        base_dir: projectPath,
        max_cycles: maxCycles,
      });

      if (result.success) {
        // Set the new run_id in the store
        setRunId(result.run_id);
        // Clear custom run_id input
        setCustomRunId('');
        // Reload runs to show the new fork
        await loadRuns();
        // Load graph data to sync the UI
        await syncGraphAndExecution();
        setIsLoaded(true);
        onToggle(); // Close the panel on success
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to fork';
      setError(message);
    } finally {
      setLoading(false);
    }
  };
  
  const syncGraphAndExecution = async () => {
    try {
      // Fetch graph data
      const graphData = await graphApi.get();
      setGraphData(graphData);
      
      // Get execution state to sync node statuses
      const execState = await executionApi.getState();
      setProgress(execState.completed_count, execState.total_count);
      
      // Convert node_statuses to the expected format
      const statusMap: Record<string, 'pending' | 'running' | 'completed' | 'failed' | 'skipped'> = {};
      for (const [flowIndex, status] of Object.entries(execState.node_statuses)) {
        statusMap[flowIndex] = status as 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
      }
      setNodeStatuses(statusMap);
      
    } catch (e) {
      console.error('Failed to sync graph and execution state:', e);
    }
  };
  
  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Unknown';
    const date = new Date(isoString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = new Date(now.setDate(now.getDate() - 1)).toDateString() === date.toDateString();
    
    if (isToday) {
      return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (isYesterday) {
      return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const getRunStatusIcon = (run: RunInfo) => {
    if (run.execution_count > 0) {
      return <CheckCircle2 className="w-3 h-3 text-green-500" />;
    }
    return <Clock className="w-3 h-3 text-gray-400" />;
  };
  
  // Don't render if closed or no project
  if (!isOpen || !currentProject) {
    return null;
  }
  
  return (
    <div className="border-b border-slate-200 bg-white relative z-20">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Database size={14} className="text-indigo-600" />
          <span>Checkpoints</span>
          {runs.length > 0 && (
            <span className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
              {runs.length} run{runs.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={checkDbAndLoadRuns}
            disabled={loading}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Refresh runs"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={onToggle}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Close"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Error display */}
        {error && (
          <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}
        
        {/* DB info */}
        <div className="text-xs text-slate-500">
          DB: {currentProject?.execution?.db_path || dbPath || 'orchestration.db'}
        </div>
        
        {/* No database found */}
        {dbExists === false && !loading && (
          <div className="text-center py-4 text-slate-500">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="font-medium text-sm">No checkpoint database found</p>
            <p className="text-xs mt-1">Run an execution first to create checkpoints.</p>
          </div>
        )}
        
        {/* No runs */}
        {dbExists === true && runs.length === 0 && !loading && (
          <div className="text-center py-4 text-slate-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="font-medium text-sm">No previous runs found</p>
            <p className="text-xs mt-1">Start a fresh execution first.</p>
          </div>
        )}
        
        {/* Run list */}
        {runs.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-700">Previous Runs</label>
            <div className="border rounded-lg max-h-32 overflow-y-auto divide-y divide-slate-100">
              {runs.map((run) => (
                <div
                  key={run.run_id}
                  className={`flex items-start gap-2 p-2 hover:bg-slate-50 transition-colors ${
                    selectedRun === run.run_id ? 'bg-indigo-50 hover:bg-indigo-50' : ''
                  }`}
                >
                  <label className="flex items-start gap-2 flex-1 min-w-0 cursor-pointer">
                    <input
                      type="radio"
                      name="run"
                      checked={selectedRun === run.run_id}
                      onChange={() => setSelectedRun(run.run_id)}
                      className="mt-1 text-indigo-600 focus:ring-indigo-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {getRunStatusIcon(run)}
                        <span className="font-mono text-xs truncate" title={run.run_id}>
                          {run.run_id.length > 20 ? `${run.run_id.slice(0, 20)}...` : run.run_id}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5 flex items-center gap-1.5">
                        <span>{formatDate(run.last_execution)}</span>
                        <span className="text-slate-300">•</span>
                        <span>Cycle {run.max_cycle}</span>
                      </div>
                    </div>
                  </label>
                  {/* Delete button */}
                  {deleteConfirmId === run.run_id ? (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleDeleteRun(run.run_id)}
                        disabled={loading}
                        className="px-1.5 py-0.5 text-[10px] bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                        title="Confirm delete"
                      >
                        Yes
                      </button>
                      <button
                        onClick={() => setDeleteConfirmId(null)}
                        className="px-1.5 py-0.5 text-[10px] bg-slate-200 text-slate-700 rounded hover:bg-slate-300"
                        title="Cancel"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirmId(run.run_id);
                      }}
                      className="p-1 text-slate-300 hover:text-red-500 transition-colors"
                      title="Delete run"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Checkpoint selector */}
        {selectedRun && checkpoints.length > 0 && (
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">Checkpoint</label>
            <select
              value={selectedCheckpoint ?? ''}
              onChange={(e) => setSelectedCheckpoint(e.target.value ? Number(e.target.value) : null)}
              className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {checkpoints.map((cp) => (
                <option key={`${cp.cycle}-${cp.inference_count}`} value={cp.cycle}>
                  Cycle {cp.cycle} ({cp.inference_count} inferences)
                </option>
              ))}
            </select>
          </div>
        )}
        
        {/* Reconciliation mode */}
        {selectedRun && (
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">Reconciliation Mode</label>
            <select
              value={reconciliationMode}
              onChange={(e) => setReconciliationMode(e.target.value as ReconciliationMode)}
              className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="PATCH">PATCH - Smart merge</option>
              <option value="OVERWRITE">OVERWRITE - Trust checkpoint</option>
              <option value="FILL_GAPS">FILL_GAPS - Only missing</option>
            </select>
            <p className="text-[10px] text-slate-500">
              {reconciliationMode === 'PATCH' && 'Re-runs nodes with changed logic.'}
              {reconciliationMode === 'OVERWRITE' && "Uses checkpoint as-is."}
              {reconciliationMode === 'FILL_GAPS' && 'Only fills missing values.'}
            </p>
          </div>
        )}
        
        {/* Custom run_id for Fork */}
        {selectedRun && (
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">New Run ID (for Fork)</label>
            <input
              type="text"
              value={customRunId}
              onChange={(e) => setCustomRunId(e.target.value)}
              placeholder="Auto-generate if empty"
              className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="text-[10px] text-slate-500">
              Custom name for Fork. Leave empty to auto-generate.
            </p>
          </div>
        )}

        {/* Action buttons */}
        {selectedRun && (
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleResume}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              <Play className="w-3.5 h-3.5" />
              Resume
            </button>
            <button
              onClick={handleFork}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-white text-slate-700 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              <GitBranch className="w-3.5 h-3.5" />
              Fork
            </button>
          </div>
        )}
        
        {/* Help text */}
        {selectedRun && (
          <p className="text-[10px] text-slate-500 text-center">
            <strong>Resume</strong> continues same run. <strong>Fork</strong> creates new run.
          </p>
        )}
      </div>
    </div>
  );
}
