/**
 * Plans in Work Panel - Shows all running NormCode plans
 * 
 * Similar to Agent Panel, displays on the left side of the graph.
 * Shows all active plans with their status and panel bindings.
 */

import { useState, useEffect } from 'react';
import { 
  Workflow, RefreshCw, ChevronRight, ChevronDown,
  Play, Pause, Square, Eye, EyeOff, Link2, Unlink,
  Loader2, Check, X, Clock, AlertCircle, Zap,
  Monitor, MessageSquare, Layout, Bug, Layers
} from 'lucide-react';
import { 
  useWorkerStore, 
  WorkerState, 
  WorkerStatus, 
  WorkerCategory,
  WorkerVisibility,
  PanelType,
  RegisteredWorker,
} from '../../stores/workerStore';

// ============================================================================
// Helper Functions
// ============================================================================

function getStatusIcon(status: WorkerStatus) {
  switch (status) {
    case 'running':
      return <Play size={12} className="text-green-500 fill-green-500" />;
    case 'paused':
      return <Pause size={12} className="text-yellow-500" />;
    case 'stepping':
      return <Zap size={12} className="text-blue-500" />;
    case 'completed':
      return <Check size={12} className="text-green-600" />;
    case 'failed':
      return <X size={12} className="text-red-500" />;
    case 'stopped':
      return <Square size={12} className="text-slate-500" />;
    case 'loading':
      return <Loader2 size={12} className="text-blue-500 animate-spin" />;
    case 'ready':
      return <Check size={12} className="text-blue-500" />;
    default:
      return <Clock size={12} className="text-slate-400" />;
  }
}

function getStatusColor(status: WorkerStatus): string {
  switch (status) {
    case 'running': return 'bg-green-100 text-green-700 border-green-200';
    case 'paused': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    case 'stepping': return 'bg-blue-100 text-blue-700 border-blue-200';
    case 'completed': return 'bg-green-50 text-green-600 border-green-200';
    case 'failed': return 'bg-red-100 text-red-700 border-red-200';
    case 'stopped': return 'bg-slate-100 text-slate-600 border-slate-200';
    case 'loading': return 'bg-blue-50 text-blue-600 border-blue-200';
    case 'ready': return 'bg-blue-50 text-blue-600 border-blue-200';
    default: return 'bg-slate-50 text-slate-500 border-slate-200';
  }
}

function getCategoryIcon(category: WorkerCategory) {
  switch (category) {
    case 'project':
      return <Workflow size={12} className="text-blue-500" />;
    case 'assistant':
      return <MessageSquare size={12} className="text-purple-500" />;
    case 'background':
      return <Layers size={12} className="text-slate-500" />;
    case 'ephemeral':
      return <Zap size={12} className="text-amber-500" />;
    default:
      return <Workflow size={12} className="text-slate-400" />;
  }
}

function getCategoryLabel(category: WorkerCategory): string {
  switch (category) {
    case 'project': return 'Project';
    case 'assistant': return 'Assistant';
    case 'background': return 'Background';
    case 'ephemeral': return 'Ephemeral';
    default: return category;
  }
}

function getPanelTypeIcon(panelType: PanelType) {
  switch (panelType) {
    case 'main':
      return <Monitor size={10} className="text-blue-500" />;
    case 'chat':
      return <MessageSquare size={10} className="text-purple-500" />;
    case 'secondary':
      return <Layout size={10} className="text-green-500" />;
    case 'floating':
      return <Layers size={10} className="text-amber-500" />;
    case 'debug':
      return <Bug size={10} className="text-red-500" />;
    default:
      return <Monitor size={10} className="text-slate-400" />;
  }
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return '-';
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  } catch {
    return timestamp;
  }
}

// ============================================================================
// Plan Card Component
// ============================================================================

interface PlanCardProps {
  worker: RegisteredWorker;
  isSelected: boolean;
  onSelect: () => void;
  onBindPanel: (panelType: PanelType) => void;
}

function PlanCard({ worker, isSelected, onSelect, onBindPanel }: PlanCardProps) {
  const { state, bindings } = worker;
  const [expanded, setExpanded] = useState(false);
  const { panelBindings } = useWorkerStore();
  
  // Get bound panels for this worker
  const boundPanels = Object.values(panelBindings).filter(b => b.worker_id === state.worker_id);
  
  const progress = state.total_count > 0 
    ? Math.round((state.completed_count / state.total_count) * 100)
    : 0;
  
  return (
    <div 
      className={`
        border rounded-lg overflow-hidden transition-all
        ${isSelected ? 'border-indigo-300 bg-indigo-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'}
      `}
    >
      {/* Header */}
      <div 
        className="p-2 cursor-pointer"
        onClick={onSelect}
      >
        <div className="flex items-start gap-2">
          {/* Expand toggle */}
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="p-0.5 hover:bg-slate-100 rounded mt-0.5"
          >
            {expanded ? (
              <ChevronDown size={12} className="text-slate-400" />
            ) : (
              <ChevronRight size={12} className="text-slate-400" />
            )}
          </button>
          
          {/* Category icon */}
          <div className="pt-0.5">
            {getCategoryIcon(state.category)}
          </div>
          
          {/* Worker info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-sm text-slate-800 truncate">
                {state.name || state.worker_id}
              </span>
              
              {/* Status badge */}
              <span className={`
                px-1.5 py-0.5 text-[10px] rounded border flex items-center gap-1
                ${getStatusColor(state.status)}
              `}>
                {getStatusIcon(state.status)}
                {state.status}
              </span>
              
              {/* Visibility indicator */}
              {state.visibility === 'hidden' && (
                <span className="text-slate-400" title="Hidden plan (no panels viewing)">
                  <EyeOff size={10} />
                </span>
              )}
            </div>
            
            {/* Progress bar */}
            {state.total_count > 0 && (
              <div className="mt-1 flex items-center gap-2">
                <div className="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all ${
                      state.status === 'completed' ? 'bg-green-500' :
                      state.status === 'failed' ? 'bg-red-500' :
                      'bg-blue-500'
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-[10px] text-slate-500">
                  {state.completed_count}/{state.total_count}
                </span>
              </div>
            )}
            
            {/* Current inference */}
            {state.current_inference && (
              <div className="mt-1 text-[10px] text-slate-500 font-mono truncate">
                → {state.current_inference}
              </div>
            )}
            
            {/* Panel bindings badges */}
            {boundPanels.length > 0 && (
              <div className="mt-1 flex items-center gap-1 flex-wrap">
                {boundPanels.map(b => (
                  <span 
                    key={b.panel_id}
                    className="inline-flex items-center gap-0.5 px-1 py-0.5 bg-slate-100 rounded text-[9px] text-slate-600"
                    title={`Bound to ${b.panel_id}`}
                  >
                    {getPanelTypeIcon(b.panel_type)}
                    {b.panel_type}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-2 pt-1 border-t border-slate-100 bg-slate-50 text-[10px]">
          {/* Details grid */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-600">
            <div>
              <span className="text-slate-400">Category:</span>{' '}
              {getCategoryLabel(state.category)}
            </div>
            <div>
              <span className="text-slate-400">Plan ID:</span>{' '}
              <span className="font-mono">{state.worker_id}</span>
            </div>
            {state.project_id && (
              <div className="col-span-2">
                <span className="text-slate-400">Project:</span>{' '}
                {state.project_id}
              </div>
            )}
            {state.run_id && (
              <div className="col-span-2">
                <span className="text-slate-400">Run ID:</span>{' '}
                <span className="font-mono">{state.run_id}</span>
              </div>
            )}
            <div>
              <span className="text-slate-400">Cycles:</span>{' '}
              {state.cycle_count}
            </div>
            <div>
              <span className="text-slate-400">Started:</span>{' '}
              {formatTimestamp(state.started_at)}
            </div>
          </div>
          
          {/* Panel binding actions */}
          <div className="mt-2 pt-2 border-t border-slate-200">
            <div className="text-slate-500 mb-1 flex items-center gap-1">
              <Link2 size={10} />
              Bind to panel:
            </div>
            <div className="flex flex-wrap gap-1">
              {(['main', 'chat', 'secondary', 'debug'] as PanelType[]).map(pt => (
                <button
                  key={pt}
                  onClick={() => onBindPanel(pt)}
                  className="px-1.5 py-0.5 bg-white border border-slate-200 rounded hover:bg-slate-100 hover:border-slate-300 flex items-center gap-1 transition-colors"
                >
                  {getPanelTypeIcon(pt)}
                  {pt}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Plans List by Category
// ============================================================================

interface PlansByCategoryProps {
  category: WorkerCategory;
  workers: RegisteredWorker[];
  selectedWorkerId: string | null;
  onSelectWorker: (workerId: string) => void;
  onBindPanel: (workerId: string, panelType: PanelType) => void;
}

function PlansByCategory({ 
  category, 
  workers, 
  selectedWorkerId,
  onSelectWorker,
  onBindPanel,
}: PlansByCategoryProps) {
  const [collapsed, setCollapsed] = useState(false);
  
  if (workers.length === 0) return null;
  
  const runningCount = workers.filter(w => w.state.status === 'running').length;
  
  return (
    <div className="mb-3">
      {/* Category header */}
      <div 
        className="flex items-center gap-2 mb-1.5 cursor-pointer hover:bg-slate-50 rounded px-1 py-0.5"
        onClick={() => setCollapsed(!collapsed)}
      >
        {collapsed ? (
          <ChevronRight size={12} className="text-slate-400" />
        ) : (
          <ChevronDown size={12} className="text-slate-400" />
        )}
        {getCategoryIcon(category)}
        <span className="text-xs font-semibold text-slate-600">
          {getCategoryLabel(category)}
        </span>
        <span className="text-[10px] text-slate-400">
          ({workers.length})
        </span>
        {runningCount > 0 && (
          <span className="text-[10px] bg-green-100 text-green-700 px-1 rounded">
            {runningCount} running
          </span>
        )}
      </div>
      
      {/* Plans list */}
      {!collapsed && (
        <div className="space-y-1.5 ml-4">
          {workers.map(worker => (
            <PlanCard
              key={worker.state.worker_id}
              worker={worker}
              isSelected={selectedWorkerId === worker.state.worker_id}
              onSelect={() => onSelectWorker(worker.state.worker_id)}
              onBindPanel={(pt) => onBindPanel(worker.state.worker_id, pt)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Plans in Work Panel
// ============================================================================

export function WorkersPanel() {
  const { 
    workers, 
    panelBindings,
    selectedWorkerId,
    isLoading,
    lastError,
    fetchWorkers,
    setSelectedWorkerId,
    bindPanel,
  } = useWorkerStore();
  
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // Initial fetch
  useEffect(() => {
    fetchWorkers();
  }, [fetchWorkers]);
  
  // Auto-refresh every 5 seconds when enabled
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchWorkers();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, fetchWorkers]);
  
  // Filter out "empty shell" workers that have an active chat counterpart
  // A user-{projectId} worker is an empty shell if:
  // 1. It's idle with no completed inferences
  // 2. There's a corresponding chat-{projectId} worker that has activity
  const workerList = Object.values(workers);
  
  const filteredWorkerList = workerList.filter(w => {
    const workerId = w.state.worker_id;
    
    // If this is a user-* worker, check if there's an active chat-* counterpart
    if (workerId.startsWith('user-')) {
      const projectId = workerId.replace('user-', '');
      const chatWorkerId = `chat-${projectId}`;
      const chatWorker = workers[chatWorkerId];
      
      // Hide the user worker if:
      // - It's idle/completed with no activity
      // - There's a chat worker that has activity (running/paused/has completed some work)
      const isEmptyShell = (
        (w.state.status === 'idle' || w.state.status === 'completed') &&
        w.state.completed_count === 0
      );
      const chatHasActivity = chatWorker && (
        chatWorker.state.status === 'running' ||
        chatWorker.state.status === 'paused' ||
        chatWorker.state.completed_count > 0 ||
        chatWorker.bindings.length > 0
      );
      
      if (isEmptyShell && chatHasActivity) {
        return false; // Filter out this empty shell
      }
    }
    
    return true;
  });
  
  // Group workers by category
  const projectWorkers = filteredWorkerList.filter(w => w.state.category === 'project');
  const assistantWorkers = filteredWorkerList.filter(w => w.state.category === 'assistant');
  const backgroundWorkers = filteredWorkerList.filter(w => w.state.category === 'background');
  const ephemeralWorkers = filteredWorkerList.filter(w => w.state.category === 'ephemeral');
  
  const runningCount = filteredWorkerList.filter(w => w.state.status === 'running').length;
  // Count hidden workers that are actually meaningful (not filtered out empty shells)
  const hiddenCount = filteredWorkerList.filter(w => w.state.visibility === 'hidden').length;
  
  // Count how many workers were filtered out
  const filteredOutCount = workerList.length - filteredWorkerList.length;
  
  const handleBindPanel = async (workerId: string, panelType: PanelType) => {
    const panelId = `${panelType}_panel`;
    await bindPanel(panelId, panelType, workerId);
  };
  
  return (
    <div className="h-full flex flex-col bg-slate-50 border-r w-72">
      {/* Header */}
      <div className="p-2 border-b bg-white flex items-center justify-between">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <Workflow size={14} className="text-indigo-500" />
          Plans in Work
          <span className="text-xs text-slate-400">
            ({filteredWorkerList.length})
          </span>
          {runningCount > 0 && (
            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              {runningCount}
            </span>
          )}
        </h3>
        
        <div className="flex items-center gap-1">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1 rounded transition-colors ${
              autoRefresh 
                ? 'text-green-600 hover:bg-green-50' 
                : 'text-slate-400 hover:bg-slate-100'
            }`}
            title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          >
            <RefreshCw size={12} className={autoRefresh ? 'animate-spin-slow' : ''} />
          </button>
          
          {/* Manual refresh */}
          <button
            onClick={() => fetchWorkers()}
            disabled={isLoading}
            className="p-1 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Error message */}
        {lastError && (
          <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600 flex items-start gap-2">
            <AlertCircle size={12} className="shrink-0 mt-0.5" />
            {lastError}
          </div>
        )}
        
        {/* Empty state */}
        {filteredWorkerList.length === 0 && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm p-4 text-center">
            <Workflow size={32} className="mb-2 text-slate-300" />
            <p>No plans active</p>
            <p className="text-xs mt-1">
              Plans appear when you load and execute a project
            </p>
          </div>
        )}
        
        {/* Loading state */}
        {isLoading && filteredWorkerList.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <Loader2 size={20} className="animate-spin text-slate-400" />
          </div>
        )}
        
        {/* Plans by category */}
        {projectWorkers.length > 0 && (
          <PlansByCategory
            category="project"
            workers={projectWorkers}
            selectedWorkerId={selectedWorkerId}
            onSelectWorker={setSelectedWorkerId}
            onBindPanel={handleBindPanel}
          />
        )}
        
        {assistantWorkers.length > 0 && (
          <PlansByCategory
            category="assistant"
            workers={assistantWorkers}
            selectedWorkerId={selectedWorkerId}
            onSelectWorker={setSelectedWorkerId}
            onBindPanel={handleBindPanel}
          />
        )}
        
        {backgroundWorkers.length > 0 && (
          <PlansByCategory
            category="background"
            workers={backgroundWorkers}
            selectedWorkerId={selectedWorkerId}
            onSelectWorker={setSelectedWorkerId}
            onBindPanel={handleBindPanel}
          />
        )}
        
        {ephemeralWorkers.length > 0 && (
          <PlansByCategory
            category="ephemeral"
            workers={ephemeralWorkers}
            selectedWorkerId={selectedWorkerId}
            onSelectWorker={setSelectedWorkerId}
            onBindPanel={handleBindPanel}
          />
        )}
        
        {/* Hidden/filtered plans note */}
        {(hiddenCount > 0 || filteredOutCount > 0) && (
          <div className="mt-2 pt-2 border-t border-slate-200 text-[10px] text-slate-400 space-y-0.5">
            {hiddenCount > 0 && (
              <div className="flex items-center gap-1">
                <EyeOff size={10} />
                {hiddenCount} hidden plan{hiddenCount > 1 ? 's' : ''} (no panel bindings)
              </div>
            )}
            {filteredOutCount > 0 && (
              <div className="flex items-center gap-1 text-slate-300">
                <span className="text-[8px]">✓</span>
                {filteredOutCount} duplicate{filteredOutCount > 1 ? 's' : ''} merged with assistant
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Footer - Panel bindings summary */}
      <div className="border-t bg-white p-2">
        <div className="text-[10px] text-slate-500 mb-1 flex items-center gap-1">
          <Link2 size={10} />
          Panel Bindings
        </div>
        <div className="flex flex-wrap gap-1">
          {Object.values(panelBindings).length === 0 ? (
            <span className="text-[10px] text-slate-400 italic">No bindings</span>
          ) : (
            Object.values(panelBindings).map(b => {
              const worker = workers[b.worker_id];
              return (
                <span 
                  key={b.panel_id}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 rounded text-[9px] text-slate-600"
                  title={`${b.panel_id} → ${b.worker_id}`}
                >
                  {getPanelTypeIcon(b.panel_type)}
                  {b.panel_type} → {worker?.state.name || b.worker_id}
                </span>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

