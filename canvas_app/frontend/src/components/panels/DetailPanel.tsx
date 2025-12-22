/**
 * Detail Panel for selected node inspection
 * Enhanced with tensor data visualization and reference fetching
 * Supports fullscreen expansion for detailed inspection
 */

import { useEffect, useState } from 'react';
import { X, Circle, Layers, GitBranch, FileJson, RefreshCw, Database, Play, Workflow, Maximize2, Minimize2, Edit3, RotateCcw, Settings } from 'lucide-react';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi, ReferenceData } from '../../services/api';
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

  // Reference data state
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [isLoadingRef, setIsLoadingRef] = useState(false);
  const [refError, setRefError] = useState<string | null>(null);
  
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

    // Fetch reference data
    const fetchReference = async () => {
      setIsLoadingRef(true);
      setRefError(null);
      try {
        const data = await executionApi.getReference(conceptName);
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
  }, [selectedNodeId, getNode]);

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
      const data = await executionApi.getReference(conceptName);
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
                  {node.node_type === 'value' && status !== 'running' && (
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
                  {node.node_type === 'function' && status !== 'running' && (
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
                  {status !== 'running' && nodeStatus === 'completed' && (
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
            <div className="space-y-4 overflow-y-auto">
              {/* Reference Data Section (for value nodes) - Expanded in fullscreen */}
              {node.node_type === 'value' && (
                <section className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 h-full flex flex-col">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-slate-600 uppercase flex items-center gap-2">
                      <Database size={14} /> Reference Data
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
