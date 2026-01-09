/**
 * Detail Panel for selected node inspection
 * Enhanced with tensor data visualization and reference fetching
 * Supports fullscreen expansion for detailed inspection
 */

import { useEffect, useState } from 'react';
import { X, Circle, Layers, GitBranch, FileJson, RefreshCw, Database, Play, Workflow, Maximize2, Minimize2, Edit3, RotateCcw, Settings, History, ChevronDown, ChevronUp } from 'lucide-react';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { useProjectStore } from '../../stores/projectStore';
import { useWorkerStore } from '../../stores/workerStore';
import { executionApi, ReferenceData, IterationHistoryEntry } from '../../services/api';
import { TensorInspector } from './TensorInspector';
import { StepPipeline } from './StepPipeline';
import { ValueOverrideModal } from './ValueOverrideModal';
import { FunctionModifyModal } from './FunctionModifyModal';
import { RerunConfirmModal } from './RerunConfirmModal';

interface DetailPanelProps {
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export function DetailPanel({ isFullscreen = false, onToggleFullscreen }: DetailPanelProps) {
  const selectedNodeId = useSelectionStore((s) => s.selectedNodeId);
  const clearSelection = useSelectionStore((s) => s.clearSelection);
  const setSelectedNode = useSelectionStore((s) => s.setSelectedNode);
  const getNode = useGraphStore((s) => s.getNode);
  const getEdgesForNode = useGraphStore((s) => s.getEdgesForNode);
  const highlightBranch = useGraphStore((s) => s.highlightBranch);
  const nodeStatuses = useExecutionStore((s) => s.nodeStatuses);
  const breakpoints = useExecutionStore((s) => s.breakpoints);
  const addBreakpoint = useExecutionStore((s) => s.addBreakpoint);
  const removeBreakpoint = useExecutionStore((s) => s.removeBreakpoint);
  const status = useExecutionStore((s) => s.status);
  const stepProgress = useExecutionStore((s) => s.stepProgress);
  
  // Check if current project is read-only (e.g., compiler project)
  const openTabs = useProjectStore((s) => s.openTabs);
  const activeTabId = useProjectStore((s) => s.activeTabId);
  const isReadOnly = openTabs.find(t => t.id === activeTabId)?.is_read_only ?? false;
  
  // Worker store for fetching references from bound workers
  const getActiveWorkerId = useWorkerStore((s) => s.getActiveWorkerId);
  const fetchWorkerReference = useWorkerStore((s) => s.fetchWorkerReference);

  // Reference data state
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [isLoadingRef, setIsLoadingRef] = useState(false);
  const [refError, setRefError] = useState<string | null>(null);
  
  // Iteration history state - for viewing past loop iteration values
  const [iterationHistory, setIterationHistory] = useState<IterationHistoryEntry[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [expandedHistoryIndex, setExpandedHistoryIndex] = useState<number | null>(null);
  
  // Run-to state
  const [isRunningTo, setIsRunningTo] = useState(false);
  
  // Phase 4: Modification modal states
  const [showValueOverride, setShowValueOverride] = useState(false);
  const [showFunctionModify, setShowFunctionModify] = useState(false);
  const [showRerunConfirm, setShowRerunConfirm] = useState(false);

  // Navigate to a node - selects it and highlights its branch
  const navigateToNode = (nodeId: string) => {
    setSelectedNode(nodeId);
    highlightBranch(nodeId);
  };

  // Fetch reference data when node changes
  useEffect(() => {
    if (!selectedNodeId) {
      setReferenceData(null);
      setRefError(null);
      return;
    }

    const node = getNode(selectedNodeId);
    if (!node) return;

    // Get concept name from node
    const conceptName = node.data.concept_name || node.label;
    if (!conceptName) return;

    // Fetch reference data - use worker-specific endpoint if a worker is bound
    const fetchReference = async () => {
      setIsLoadingRef(true);
      setRefError(null);
      try {
        let data: ReferenceData | null = null;
        // Use getActiveWorkerId to check both main_panel and chat_panel bindings
        const activeWorkerId = getActiveWorkerId();
        
        if (activeWorkerId) {
          // Use worker-specific endpoint for bound workers (e.g., assistant, chat controller)
          const workerData = await fetchWorkerReference(activeWorkerId, conceptName);
          if (workerData && workerData.has_reference) {
            data = workerData as ReferenceData;
          }
        } else {
          // Use default endpoint for regular projects
          data = await executionApi.getReference(conceptName);
        }
        
        // Check if reference data exists (has_reference: true)
        if (data && data.has_reference) {
          setReferenceData(data);
        } else {
          setReferenceData(null);
        }
      } catch (e) {
        setRefError('Failed to load reference data');
        setReferenceData(null);
      } finally {
        setIsLoadingRef(false);
      }
    };

    fetchReference();
  }, [selectedNodeId, getNode, getActiveWorkerId, fetchWorkerReference]);

  // Fetch iteration history when node changes
  useEffect(() => {
    if (!selectedNodeId) {
      setIterationHistory([]);
      setShowHistory(false);
      return;
    }

    const node = getNode(selectedNodeId);
    if (!node) return;

    const conceptName = node.data.concept_name || node.label;
    if (!conceptName) return;

    // Fetch iteration history - use worker-specific endpoint if a worker is bound
    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        // Use getActiveWorkerId to check both main_panel and chat_panel bindings
        const activeWorkerId = getActiveWorkerId();
        let response;
        
        if (activeWorkerId) {
          // Use worker-specific endpoint for bound workers (e.g., chat controller)
          response = await executionApi.getWorkerReferenceHistory(activeWorkerId, conceptName, 20);
        } else {
          // Use default endpoint for regular projects
          response = await executionApi.getReferenceHistory(conceptName, 20);
        }
        
        setIterationHistory(response.history || []);
      } catch (e) {
        console.error('Failed to load iteration history:', e);
        setIterationHistory([]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [selectedNodeId, getNode, getActiveWorkerId]);

  // Refresh reference data
  const refreshReference = async () => {
    if (!selectedNodeId) return;
    const node = getNode(selectedNodeId);
    if (!node) return;

    const conceptName = node.data.concept_name || node.label;
    if (!conceptName) return;

    setIsLoadingRef(true);
    setRefError(null);
    try {
      let data: ReferenceData | null = null;
      const activeWorkerId = getActiveWorkerId();
      
      if (activeWorkerId) {
        // Use worker-specific endpoint for bound workers
        const workerData = await fetchWorkerReference(activeWorkerId, conceptName);
        if (workerData && workerData.has_reference) {
          data = workerData as ReferenceData;
        }
      } else {
        // Use default endpoint for regular projects
        data = await executionApi.getReference(conceptName);
      }
      
      // Check if reference data exists (has_reference: true)
      if (data && data.has_reference) {
        setReferenceData(data);
      } else {
        setReferenceData(null);
      }
    } catch (e) {
      setRefError('Failed to load reference data');
      setReferenceData(null);
    } finally {
      setIsLoadingRef(false);
    }
  };

  // Base panel classes - changes based on fullscreen state
  const panelBaseClasses = isFullscreen
    ? 'fixed inset-0 z-50 bg-white flex flex-col'
    : 'w-80 bg-white border-l border-slate-200 flex flex-col h-full overflow-hidden';

  if (!selectedNodeId) {
    return (
      <div className={isFullscreen 
        ? 'fixed inset-0 z-50 bg-white p-4 flex items-center justify-center text-slate-500 text-sm'
        : 'w-80 bg-white border-l border-slate-200 p-4 flex items-center justify-center text-slate-500 text-sm'
      }>
        {isFullscreen && (
          <button
            onClick={onToggleFullscreen}
            className="absolute top-4 right-4 p-2 rounded hover:bg-slate-100 text-slate-500"
          >
            <Minimize2 size={18} />
          </button>
        )}
        Select a node to view details
      </div>
    );
  }

  const node = getNode(selectedNodeId);
  if (!node) {
    return (
      <div className={isFullscreen 
        ? 'fixed inset-0 z-50 bg-white p-4'
        : 'w-80 bg-white border-l border-slate-200 p-4'
      }>
        {isFullscreen && (
          <button
            onClick={onToggleFullscreen}
            className="absolute top-4 right-4 p-2 rounded hover:bg-slate-100 text-slate-500"
          >
            <Minimize2 size={18} />
          </button>
        )}
        <p className="text-red-500">Node not found</p>
      </div>
    );
  }

  const edges = getEdgesForNode(selectedNodeId);
  const nodeStatus = node.flow_index ? nodeStatuses[node.flow_index] || 'pending' : 'pending';
  const hasBreakpoint = node.flow_index ? breakpoints.has(node.flow_index) : false;

  const handleToggleBreakpoint = async () => {
    if (!node.flow_index) {
      console.warn('Cannot set breakpoint: node has no flow_index');
      return;
    }
    
    // Capture the current state BEFORE the async call
    const shouldRemove = hasBreakpoint;
    
    try {
      if (shouldRemove) {
        // Optimistically update local store first for responsive UI
        removeBreakpoint(node.flow_index);
        await executionApi.clearBreakpoint(node.flow_index);
      } else {
        // Optimistically update local store first for responsive UI
        addBreakpoint(node.flow_index);
        await executionApi.setBreakpoint(node.flow_index, true);
      }
      // WebSocket event will also update but that's okay (idempotent)
    } catch (e) {
      console.error('Failed to toggle breakpoint:', e);
      // Revert on error
      if (shouldRemove) {
        addBreakpoint(node.flow_index);
      } else {
        removeBreakpoint(node.flow_index);
      }
    }
  };

  const handleRunTo = async () => {
    if (!node.flow_index) return;
    setIsRunningTo(true);
    try {
      await executionApi.runTo(node.flow_index);
    } catch (e) {
      console.error('Failed to run to node:', e);
    } finally {
      setIsRunningTo(false);
    }
  };

  // Phase 4: Value Override handler
  const handleValueOverrideApply = (success: boolean) => {
    if (success) {
      // Refresh reference data after override
      refreshReference();
    }
  };

  // Phase 4: Function Modify handler
  const handleFunctionModifyApply = (success: boolean) => {
    if (success) {
      // Could trigger a graph refresh if needed
    }
  };

  // Phase 4: Rerun handler
  const handleRerunConfirm = (success: boolean) => {
    if (success) {
      // Nodes will be updated via WebSocket events
    }
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    skipped: 'bg-yellow-100 text-yellow-700',
  };

  return (
    <div className={panelBaseClasses}>
      {/* Fullscreen backdrop overlay */}
      {isFullscreen && (
        <div 
          className="fixed inset-0 bg-black/20 -z-10" 
          onClick={onToggleFullscreen}
        />
      )}
      
      {/* Header */}
      <div className={`flex items-center justify-between p-4 border-b border-slate-200 ${isFullscreen ? 'bg-slate-50' : ''}`}>
        <div className="flex items-center gap-3">
          <h3 className={`font-semibold text-slate-800 ${isFullscreen ? 'text-lg' : ''}`}>
            Node Details
          </h3>
          {isFullscreen && node && (
            <span className="text-sm text-slate-500 font-mono">
              {node.label}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {/* Fullscreen toggle button */}
          <button
            onClick={onToggleFullscreen}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Expand to fullscreen'}
          >
            {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button
            onClick={() => {
              if (isFullscreen && onToggleFullscreen) {
                onToggleFullscreen();
              }
              clearSelection();
            }}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500 transition-colors"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className={`flex-1 overflow-y-auto ${isFullscreen ? 'p-6' : 'p-4'}`}>
        {/* Fullscreen: Two-column layout, Normal: Single column */}
        <div className={isFullscreen ? 'grid grid-cols-2 gap-6 h-full' : 'space-y-4'}>
          
          {/* Left Column (in fullscreen) / All content (in normal mode) */}
          <div className={isFullscreen ? 'space-y-4 overflow-y-auto' : 'contents'}>
            
            {/* Compact Header: Name + Status Badges */}
            <div className={`${isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : 'pb-3 border-b border-slate-100'}`}>
              {/* Name */}
              <div className="mb-2">
                {node.data.natural_name ? (
                  <>
                    <p className={`text-slate-800 font-medium ${isFullscreen ? 'text-base' : 'text-sm'} leading-relaxed`}>{node.data.natural_name}</p>
                    <p className="font-mono text-xs text-slate-500 truncate mt-0.5" title={node.label}>{node.label}</p>
                  </>
                ) : (
                  <p className={`font-mono text-slate-800 break-words leading-relaxed ${isFullscreen ? 'text-sm' : 'text-sm'}`}>{node.label}</p>
                )}
              </div>
              
              {/* Status Badges Row */}
              <div className="flex items-center gap-2 flex-wrap mt-2.5">
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusColors[nodeStatus]}`}>
                  {nodeStatus}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 capitalize">
                  {node.node_type}
                </span>
                {node.flow_index && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600">
                    {node.flow_index}
                  </span>
                )}
                {node.data.is_ground && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">Ground</span>
                )}
                {node.data.is_final && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-100 text-red-700">Output</span>
                )}
                {node.data.is_context && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-100 text-purple-700">Context</span>
                )}
              </div>
              
              {/* Debugging Buttons - inline */}
              {node.flow_index && (
                <div className="flex gap-2 mt-3 flex-wrap">
                  <button
                    onClick={handleToggleBreakpoint}
                    className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] transition-colors ${
                      hasBreakpoint
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    <Circle size={8} className={hasBreakpoint ? 'fill-red-500 text-red-500' : ''} />
                    {hasBreakpoint ? 'BP' : '+BP'}
                  </button>
                  {status !== 'running' && nodeStatus === 'pending' && (
                    <button
                      onClick={handleRunTo}
                      disabled={isRunningTo}
                      className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors disabled:opacity-50"
                    >
                      <Play size={8} className={isRunningTo ? 'animate-pulse' : ''} />
                      {isRunningTo ? '...' : 'Run To'}
                    </button>
                  )}
                  
                  {/* Phase 4: Value Override button (for value nodes with reference) */}
                  {/* Hidden for read-only projects */}
                  {!isReadOnly && node.node_type === 'value' && status !== 'running' && (
                    <button
                      onClick={() => setShowValueOverride(true)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                      title="Override this node's value"
                    >
                      <Edit3 size={8} />
                      Override
                    </button>
                  )}
                  
                  {/* Phase 4: Function Modify button (for function nodes) */}
                  {/* Hidden for read-only projects */}
                  {!isReadOnly && node.node_type === 'function' && status !== 'running' && (
                    <button
                      onClick={() => setShowFunctionModify(true)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
                      title="Modify function parameters"
                    >
                      <Settings size={8} />
                      Modify
                    </button>
                  )}
                  
                  {/* Phase 4: Re-run From button (for completed nodes) */}
                  {/* Hidden for read-only projects */}
                  {!isReadOnly && status !== 'running' && nodeStatus === 'completed' && (
                    <button
                      onClick={() => setShowRerunConfirm(true)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-orange-100 text-orange-700 hover:bg-orange-200 transition-colors"
                      title="Reset and re-run from this node"
                    >
                      <RotateCcw size={8} />
                      Re-run
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Step Progress Section - Collapsible */}
            {node.flow_index && stepProgress[node.flow_index] && (
              <details className={`group ${isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : 'pt-2'}`} open>
                <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                  <Workflow size={12} /> 
                  <span>Pipeline</span>
                  <span className="text-[10px] font-normal text-slate-400 ml-1">
                    ({stepProgress[node.flow_index]?.current_step || 'ready'})
                  </span>
                </summary>
                <div className="mt-3">
                  <StepPipeline 
                    progress={stepProgress[node.flow_index]} 
                    compact={!isFullscreen}
                  />
                </div>
              </details>
            )}

            {/* Value Details - Collapsible */}
            {node.node_type === 'value' && node.data.axes && node.data.axes.length > 0 && (
              <details className={`group ${isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : 'pt-2'}`}>
                <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                  <Layers size={12} /> 
                  <span>Axes</span>
                  <span className="text-[10px] font-normal text-slate-400 ml-1">
                    ({node.data.axes.length})
                  </span>
                </summary>
                <div className="mt-2">
                  <p className="font-mono text-xs text-slate-700">[{node.data.axes.join(', ')}]</p>
                </div>
              </details>
            )}

            {/* Function Details Section - Collapsible */}
            {node.node_type === 'function' && (node.data.sequence || node.data.working_interpretation) && (
              <details className={`group ${isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : 'pt-2'}`} open={isFullscreen}>
                <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                  <FileJson size={12} /> 
                  <span>Function</span>
                  {node.data.sequence && (
                    <span className="text-[10px] font-normal text-slate-400 ml-1">({node.data.sequence})</span>
                  )}
                </summary>
                <div className="mt-3 space-y-2.5">
                  {/* Working Interpretation - Compact View */}
                  {node.data.working_interpretation && (
                    <>
                      {/* Paradigm */}
                      {node.data.working_interpretation.paradigm && (
                        <div className="bg-purple-50 px-2 py-1.5 rounded text-xs">
                          <span className="text-purple-600 font-medium">Paradigm: </span>
                          <span className="font-mono text-purple-800 break-all">
                            {String(node.data.working_interpretation.paradigm)}
                          </span>
                        </div>
                      )}
                      
                      {/* Value Order - Compact */}
                      {node.data.working_interpretation.value_order && (
                        <details className="bg-blue-50 px-2 py-1.5 rounded text-xs">
                          <summary className="text-blue-600 font-medium cursor-pointer">
                            Value Order ({Object.keys(node.data.working_interpretation.value_order).length})
                          </summary>
                          <div className="mt-1 space-y-0.5">
                            {Object.entries(node.data.working_interpretation.value_order).map(([key, val]) => (
                              <div key={key} className="flex justify-between">
                                <span className="font-mono text-blue-700 truncate max-w-[160px]" title={key}>{key}</span>
                                <span className="text-blue-900 font-medium">:{String(val)}</span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      
                      {/* Prompt + Output in one line */}
                      <div className="flex flex-wrap gap-1 text-[10px]">
                        {!!node.data.working_interpretation.prompt_location && (
                          <span className="bg-green-50 text-green-700 px-1.5 py-0.5 rounded font-mono truncate max-w-full" title={String(node.data.working_interpretation.prompt_location)}>
                            📄 {String(node.data.working_interpretation.prompt_location).split('/').pop()}
                          </span>
                        )}
                        {!!node.data.working_interpretation.output_type && (
                          <span className="bg-orange-50 text-orange-700 px-1.5 py-0.5 rounded font-mono">
                            → {String(node.data.working_interpretation.output_type)}
                          </span>
                        )}
                      </div>

                      {/* Other fields */}
                      {(() => {
                        const knownKeys = ['paradigm', 'value_order', 'prompt_location', 'output_type'];
                        const otherFields = Object.entries(node.data.working_interpretation)
                          .filter(([key]) => !knownKeys.includes(key));
                        
                        if (otherFields.length > 0) {
                          return (
                            <details className="bg-slate-100 px-2 py-1 rounded text-[10px]">
                              <summary className="text-slate-600 cursor-pointer">
                                +{otherFields.length} more
                              </summary>
                              <pre className="text-slate-600 mt-1 overflow-x-auto text-[10px]">
                                {JSON.stringify(Object.fromEntries(otherFields), null, 2)}
                              </pre>
                            </details>
                          );
                        }
                        return null;
                      })()}
                    </>
                  )}
                </div>
              </details>
            )}

            {/* Vertical Input Section for Function Nodes - Collapsible (Normal mode only) */}
            {!isFullscreen && node.node_type === 'function' && referenceData && (
              <details className="group pt-2" open>
                <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                  <Database size={12} /> 
                  <span>Vertical Input</span>
                  <span className="text-[10px] font-normal text-slate-400 ml-1">
                    ({Array.isArray(referenceData.data) ? referenceData.data.length + ' items' : 'loaded'})
                  </span>
                  <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); refreshReference(); }}
                    disabled={isLoadingRef}
                    className="ml-auto p-1 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50"
                    title="Refresh"
                  >
                    <RefreshCw size={10} className={isLoadingRef ? 'animate-spin' : ''} />
                  </button>
                </summary>
                <div className="mt-2">
                  <TensorInspector
                    data={referenceData.data}
                    axes={referenceData.axes}
                    shape={referenceData.shape}
                    conceptName={referenceData.concept_name}
                    isGround={false}
                    isCompact={true}
                  />
                </div>
              </details>
            )}

            {/* Connections Section - Collapsible */}
            <details className={`group ${isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : 'pt-2'}`} open>
              <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                <GitBranch size={12} /> 
                <span>Connections</span>
                <span className="text-[10px] font-normal text-slate-400 ml-1">
                  ({edges.incoming.length} in, {edges.outgoing.length} out)
                </span>
              </summary>
              <div className={`mt-3 ${isFullscreen ? 'grid grid-cols-2 gap-4' : 'space-y-3'}`}>
                <div>
                  <label className="text-xs text-slate-500 font-medium">Incoming</label>
                  {edges.incoming.length > 0 ? (
                    <ul className="text-sm text-slate-700 space-y-1.5 mt-1.5">
                      {edges.incoming.map((e) => {
                        const sourceNode = getNode(e.source);
                        const displayName = sourceNode?.data?.natural_name || e.source.split('@')[0];
                        const edgeTypeColors: Record<string, string> = {
                          function: 'bg-blue-100 text-blue-700',
                          value: 'bg-purple-100 text-purple-700',
                          context: 'bg-orange-100 text-orange-700',
                          alias: 'bg-gray-100 text-gray-600',
                        };
                        const edgeColor = edgeTypeColors[e.edge_type] || 'bg-slate-100 text-slate-600';
                        
                        return (
                          <li key={e.id} className="flex items-center gap-1.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${edgeColor}`}>
                              {e.edge_type === 'function' ? 'fn' : e.edge_type === 'value' ? 'val' : e.edge_type === 'context' ? 'ctx' : e.edge_type}
                            </span>
                            <button
                              onClick={() => navigateToNode(e.source)}
                              className={`font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline text-left ${isFullscreen ? '' : 'truncate max-w-[180px]'}`}
                              title={`Click to select: ${e.source}\n${sourceNode?.label || ''}`}
                            >
                              ← {displayName}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400 mt-1">None</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-slate-500 font-medium">Outgoing</label>
                  {edges.outgoing.length > 0 ? (
                    <ul className="text-sm text-slate-700 space-y-1.5 mt-1.5">
                      {edges.outgoing.map((e) => {
                        const targetNode = getNode(e.target);
                        const displayName = targetNode?.data?.natural_name || e.target.split('@')[0];
                        const edgeTypeColors: Record<string, string> = {
                          function: 'bg-blue-100 text-blue-700',
                          value: 'bg-purple-100 text-purple-700',
                          context: 'bg-orange-100 text-orange-700',
                          alias: 'bg-gray-100 text-gray-600',
                        };
                        const edgeColor = edgeTypeColors[e.edge_type] || 'bg-slate-100 text-slate-600';
                        
                        return (
                          <li key={e.id} className="flex items-center gap-1.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${edgeColor}`}>
                              {e.edge_type === 'function' ? 'fn' : e.edge_type === 'value' ? 'val' : e.edge_type === 'context' ? 'ctx' : e.edge_type}
                            </span>
                            <button
                              onClick={() => navigateToNode(e.target)}
                              className={`font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline text-left ${isFullscreen ? '' : 'truncate max-w-[180px]'}`}
                              title={`Click to select: ${e.target}\n${targetNode?.label || ''}`}
                            >
                              → {displayName}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400 mt-1">None</p>
                  )}
                </div>
              </div>
            </details>
          </div>

          {/* Right Column (only in fullscreen mode) - Reference Data */}
          {isFullscreen && (
            <div className="flex flex-col gap-4 h-full overflow-hidden">
              {/* Reference Data Section (for value nodes) - Expanded in fullscreen */}
              {node.node_type === 'value' && (
                <section className={`bg-blue-50/50 p-4 rounded-lg border border-blue-100 flex flex-col min-h-0 overflow-hidden ${iterationHistory.length > 0 ? 'flex-1' : 'flex-[2]'}`}>
                  <div className="flex items-center justify-between mb-3 flex-shrink-0">
                    <h4 className="text-sm font-semibold text-slate-600 uppercase flex items-center gap-2">
                      <Database size={14} /> Current Reference Data
                    </h4>
                    <button
                      onClick={refreshReference}
                      disabled={isLoadingRef}
                      className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50 hover:bg-white rounded"
                      title="Refresh reference data"
                    >
                      <RefreshCw size={14} className={isLoadingRef ? 'animate-spin' : ''} />
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-auto min-h-0">
                    {isLoadingRef ? (
                      <div className="text-sm text-slate-400 flex items-center gap-2">
                        <RefreshCw size={14} className="animate-spin" />
                        Loading reference data...
                      </div>
                    ) : refError ? (
                      <div className="text-sm text-red-500">{refError}</div>
                    ) : referenceData ? (
                      <TensorInspector
                        data={referenceData.data}
                        axes={referenceData.axes}
                        shape={referenceData.shape}
                        conceptName={referenceData.concept_name}
                        isGround={node.data.is_ground}
                        isCompact={false}
                      />
                    ) : (
                      <div className="text-sm text-slate-400 bg-white p-4 rounded">
                        {node.data.is_ground 
                          ? 'Ground concept - load repositories to see data'
                          : 'No reference data yet - execute to compute'}
                      </div>
                    )}
                  </div>
                </section>
              )}
              
              {/* Iteration History Section (fullscreen mode) - shares space with current data */}
              {iterationHistory.length > 0 && (
                <section className={`bg-amber-50/50 p-4 rounded-lg border border-amber-200 flex flex-col min-h-0 overflow-hidden ${node.node_type === 'value' && referenceData ? 'flex-1' : 'flex-[2]'}`}>
                  <div className="flex items-center justify-between mb-3 flex-shrink-0">
                    <h4 className="text-sm font-semibold text-amber-700 uppercase flex items-center gap-2">
                      <History size={14} /> Iteration History
                      <span className="text-xs font-normal text-amber-500">
                        ({iterationHistory.length} past iterations)
                      </span>
                    </h4>
                  </div>
                  
                  <div className="flex-1 overflow-auto space-y-2 min-h-0">
                    {isLoadingHistory ? (
                      <div className="text-sm text-slate-400 flex items-center gap-2">
                        <RefreshCw size={14} className="animate-spin" />
                        Loading history...
                      </div>
                    ) : (
                      iterationHistory.map((entry, idx) => (
                        <details 
                          key={idx}
                          className="bg-white border border-amber-200 rounded overflow-hidden"
                          open={expandedHistoryIndex === idx}
                        >
                          <summary 
                            className="flex justify-between items-center text-xs text-amber-700 p-3 cursor-pointer hover:bg-amber-50 list-none"
                            onClick={(e) => { 
                              e.preventDefault(); 
                              setExpandedHistoryIndex(expandedHistoryIndex === idx ? null : idx); 
                            }}
                          >
                            <span className="font-medium flex items-center gap-2">
                              {expandedHistoryIndex === idx ? <ChevronDown size={12} /> : <ChevronUp size={12} className="rotate-180" />}
                              Iteration {entry.iteration_index}
                            </span>
                            <span className="text-amber-500">Cycle {entry.cycle_number}</span>
                            <span className="text-slate-500 font-mono text-xs">
                              {entry.has_data ? (
                                Array.isArray(entry.data) 
                                  ? `Shape: [${entry.data.length}]` 
                                  : typeof entry.data === 'string'
                                    ? `"${entry.data.slice(0, 20)}${entry.data.length > 20 ? '...' : ''}"`
                                    : typeof entry.data
                              ) : 'No data'}
                            </span>
                          </summary>
                          
                          {/* Show full data when expanded */}
                          {expandedHistoryIndex === idx && entry.has_data && (
                            <div className="p-3 pt-0 border-t border-amber-100">
                              <TensorInspector
                                data={entry.data}
                                axes={entry.axes}
                                shape={entry.shape}
                                isCompact={false}
                              />
                            </div>
                          )}
                          
                          {/* Quick preview when collapsed */}
                          {expandedHistoryIndex !== idx && entry.has_data && (
                            <div className="px-3 pb-3 text-xs font-mono text-slate-600 bg-slate-50 mx-3 mb-3 rounded border border-slate-200 p-2 max-h-20 overflow-hidden">
                              {typeof entry.data === 'string' ? (
                                <div className="whitespace-pre-wrap">{entry.data.slice(0, 200)}{entry.data.length > 200 ? '...' : ''}</div>
                              ) : Array.isArray(entry.data) && entry.data.length > 0 ? (
                                <div className="whitespace-pre-wrap">
                                  {typeof entry.data[0] === 'string' 
                                    ? entry.data[0].slice(0, 200)
                                    : JSON.stringify(entry.data[0], null, 2).slice(0, 200)}
                                  {(typeof entry.data[0] === 'string' ? entry.data[0].length : JSON.stringify(entry.data[0]).length) > 200 ? '...' : ''}
                                </div>
                              ) : (
                                <div className="whitespace-pre-wrap">{JSON.stringify(entry.data, null, 2).slice(0, 200)}</div>
                              )}
                            </div>
                          )}
                        </details>
                      ))
                    )}
                  </div>
                </section>
              )}
              
              {/* For function nodes in fullscreen, show working interpretation AND reference data */}
              {node.node_type === 'function' && (
                <>
                  {/* Working Interpretation */}
                  <section className="bg-purple-50/50 p-4 rounded-lg border border-purple-100 flex-1 flex flex-col">
                    <h4 className="text-sm font-semibold text-slate-600 uppercase flex items-center gap-2 mb-3">
                      <FileJson size={14} /> Full Working Interpretation
                    </h4>
                    <div className="flex-1 overflow-auto">
                      {node.data.working_interpretation ? (
                        <pre className="text-xs text-slate-700 bg-white p-4 rounded overflow-auto">
                          {JSON.stringify(node.data.working_interpretation, null, 2)}
                        </pre>
                      ) : (
                        <div className="text-sm text-slate-400 bg-white p-4 rounded">
                          No working interpretation available
                        </div>
                      )}
                    </div>
                  </section>
                  
                  {/* Vertical Input (Reference Data for function nodes) */}
                  {referenceData && (
                    <section className="bg-green-50/50 p-4 rounded-lg border border-green-100 flex-1 flex flex-col mt-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-slate-600 uppercase flex items-center gap-2">
                          <Database size={14} /> Vertical Input (Reference)
                        </h4>
                        <button
                          onClick={refreshReference}
                          disabled={isLoadingRef}
                          className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50 hover:bg-white rounded"
                          title="Refresh reference data"
                        >
                          <RefreshCw size={14} className={isLoadingRef ? 'animate-spin' : ''} />
                        </button>
                      </div>
                      <div className="flex-1 overflow-auto">
                        <TensorInspector
                          data={referenceData.data}
                          axes={referenceData.axes}
                          shape={referenceData.shape}
                          conceptName={referenceData.concept_name}
                          isGround={false}
                          isCompact={false}
                        />
                      </div>
                    </section>
                  )}
                </>
              )}
            </div>
          )}

          {/* Reference Data Section (for value nodes) - Normal mode only */}
          {!isFullscreen && node.node_type === 'value' && (
            <details className="group pt-2" open={!!referenceData}>
              <summary className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none">
                <Database size={12} /> 
                <span>Data</span>
                {referenceData && (
                  <span className="text-[10px] font-normal text-slate-400 ml-1">
                    ({Array.isArray(referenceData.data) ? referenceData.data.length + ' items' : 'loaded'})
                  </span>
                )}
                <button
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); refreshReference(); }}
                  disabled={isLoadingRef}
                  className="ml-auto p-1 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50"
                  title="Refresh"
                >
                  <RefreshCw size={10} className={isLoadingRef ? 'animate-spin' : ''} />
                </button>
              </summary>
              <div className="mt-2">
                {isLoadingRef ? (
                  <div className="text-[10px] text-slate-400 flex items-center gap-1">
                    <RefreshCw size={10} className="animate-spin" />
                    Loading...
                  </div>
                ) : refError ? (
                  <div className="text-[10px] text-red-500">{refError}</div>
                ) : referenceData ? (
                  <TensorInspector
                    data={referenceData.data}
                    axes={referenceData.axes}
                    shape={referenceData.shape}
                    conceptName={referenceData.concept_name}
                    isGround={node.data.is_ground}
                    isCompact={true}
                  />
                ) : (
                  <div className="text-[10px] text-slate-400 bg-slate-50 p-1.5 rounded">
                    {node.data.is_ground 
                      ? 'Ground - load repos to see'
                      : 'Run to compute'}
                  </div>
                )}
              </div>
            </details>
          )}
          
          {/* Iteration History Section - Shows past loop iteration values */}
          {!isFullscreen && iterationHistory.length > 0 && (
            <details className="group pt-2" open={showHistory}>
              <summary 
                className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 cursor-pointer hover:text-slate-700 list-none"
                onClick={(e) => { e.preventDefault(); setShowHistory(!showHistory); }}
              >
                <History size={12} className="text-amber-600" /> 
                <span>Iteration History</span>
                <span className="text-[10px] font-normal text-amber-600 ml-1">
                  ({iterationHistory.length} past)
                </span>
                {showHistory ? <ChevronUp size={12} className="ml-auto" /> : <ChevronDown size={12} className="ml-auto" />}
              </summary>
              {showHistory && (
                <div className="mt-2 space-y-2 max-h-80 overflow-y-auto">
                  {isLoadingHistory ? (
                    <div className="text-[10px] text-slate-400 flex items-center gap-1">
                      <RefreshCw size={10} className="animate-spin" />
                      Loading history...
                    </div>
                  ) : (
                    iterationHistory.map((entry, idx) => (
                      <details 
                        key={idx}
                        className="bg-amber-50 border border-amber-200 rounded overflow-hidden"
                        open={expandedHistoryIndex === idx}
                      >
                        <summary 
                          className="flex justify-between items-center text-[10px] text-amber-700 p-2 cursor-pointer hover:bg-amber-100 list-none"
                          onClick={(e) => { 
                            e.preventDefault(); 
                            setExpandedHistoryIndex(expandedHistoryIndex === idx ? null : idx); 
                          }}
                        >
                          <span className="font-medium flex items-center gap-1">
                            {expandedHistoryIndex === idx ? <ChevronDown size={10} /> : <ChevronUp size={10} className="rotate-180" />}
                            Iter {entry.iteration_index}
                          </span>
                          <span className="text-amber-500">Cycle {entry.cycle_number}</span>
                          <span className="text-slate-500 font-mono">
                            {entry.has_data ? (
                              Array.isArray(entry.data) 
                                ? `[${entry.data.length}]` 
                                : typeof entry.data === 'string'
                                  ? `"${entry.data.slice(0, 15)}${entry.data.length > 15 ? '...' : ''}"`
                                  : 'obj'
                            ) : '∅'}
                          </span>
                        </summary>
                        
                        {/* Show data content when expanded */}
                        {expandedHistoryIndex === idx && entry.has_data && (
                          <div className="p-2 pt-0 border-t border-amber-200 bg-white">
                            <TensorInspector
                              data={entry.data}
                              axes={entry.axes}
                              shape={entry.shape}
                              isCompact={true}
                            />
                          </div>
                        )}
                        
                        {/* Quick preview when collapsed - show first item or value */}
                        {expandedHistoryIndex !== idx && entry.has_data && (
                          <div className="px-2 pb-2 text-[10px] font-mono text-slate-600 bg-white mx-2 mb-2 rounded border border-slate-200 max-h-16 overflow-hidden">
                            {typeof entry.data === 'string' ? (
                              <div className="truncate">{entry.data}</div>
                            ) : Array.isArray(entry.data) && entry.data.length > 0 ? (
                              <div className="truncate">
                                {typeof entry.data[0] === 'string' 
                                  ? entry.data[0].slice(0, 100)
                                  : JSON.stringify(entry.data[0]).slice(0, 100)}
                                {(typeof entry.data[0] === 'string' ? entry.data[0].length : JSON.stringify(entry.data[0]).length) > 100 ? '...' : ''}
                              </div>
                            ) : (
                              <div className="truncate">{JSON.stringify(entry.data).slice(0, 100)}</div>
                            )}
                          </div>
                        )}
                      </details>
                    ))
                  )}
                </div>
              )}
            </details>
          )}
        </div>
      </div>
      
      {/* Phase 4: Value Override Modal */}
      {showValueOverride && node && (
        <ValueOverrideModal
          conceptName={node.data.concept_name || node.label}
          currentValue={referenceData?.data}
          axes={referenceData?.axes || []}
          shape={referenceData?.shape || []}
          isGround={node.data.is_ground || false}
          onClose={() => setShowValueOverride(false)}
          onApply={handleValueOverrideApply}
        />
      )}
      
      {/* Phase 4: Function Modify Modal */}
      {showFunctionModify && node && node.node_type === 'function' && (
        <FunctionModifyModal
          flowIndex={node.flow_index || ''}
          conceptName={node.data.concept_name || node.label}
          currentWI={node.data.working_interpretation || null}
          onClose={() => setShowFunctionModify(false)}
          onApply={handleFunctionModifyApply}
        />
      )}
      
      {/* Phase 4: Rerun Confirm Modal */}
      {showRerunConfirm && node && (
        <RerunConfirmModal
          flowIndex={node.flow_index || ''}
          conceptName={node.data.concept_name || node.label}
          onClose={() => setShowRerunConfirm(false)}
          onConfirm={handleRerunConfirm}
        />
      )}
    </div>
  );
}
