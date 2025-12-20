/**
 * Detail Panel for selected node inspection
 * Enhanced with tensor data visualization and reference fetching
 * Supports fullscreen expansion for detailed inspection
 */

import { useEffect, useState } from 'react';
import { X, Circle, Layers, GitBranch, FileJson, RefreshCw, Database, Play, Workflow, Maximize2, Minimize2 } from 'lucide-react';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi, ReferenceData } from '../../services/api';
import { TensorInspector } from './TensorInspector';
import { StepPipeline } from './StepPipeline';

interface DetailPanelProps {
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export function DetailPanel({ isFullscreen = false, onToggleFullscreen }: DetailPanelProps) {
  const selectedNodeId = useSelectionStore((s) => s.selectedNodeId);
  const clearSelection = useSelectionStore((s) => s.clearSelection);
  const getNode = useGraphStore((s) => s.getNode);
  const getEdgesForNode = useGraphStore((s) => s.getEdgesForNode);
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

  const categoryLabels: Record<string, string> = {
    'semantic-function': 'Semantic Function',
    'semantic-value': 'Semantic Value',
    'syntactic-function': 'Syntactic Function',
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
      <div className={`flex-1 overflow-y-auto p-4 ${isFullscreen ? 'p-6' : ''}`}>
        {/* Fullscreen: Two-column layout, Normal: Single column */}
        <div className={isFullscreen ? 'grid grid-cols-2 gap-6 h-full' : 'space-y-4'}>
          
          {/* Left Column (in fullscreen) / All content (in normal mode) */}
          <div className={isFullscreen ? 'space-y-4 overflow-y-auto' : 'contents'}>
            {/* Identity Section */}
            <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
              <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 ${isFullscreen ? 'text-sm' : ''}`}>Identity</h4>
              <div className="space-y-2">
                {/* Natural Name (human-readable) - prioritized display */}
                {node.data.natural_name && (
                  <div>
                    <label className="text-xs text-slate-500">Name</label>
                    <p className={`text-slate-800 break-words font-medium ${isFullscreen ? 'text-base' : 'text-sm'}`}>{node.data.natural_name}</p>
                  </div>
                )}
                {/* Concept Name (technical) */}
                <div>
                  <label className="text-xs text-slate-500">{node.data.natural_name ? 'Concept ID' : 'Name'}</label>
                  <p className={`font-mono text-slate-800 break-words ${isFullscreen ? 'text-sm' : 'text-sm'}`}>{node.label}</p>
                </div>
                <div className="flex gap-4">
                  <div>
                    <label className="text-xs text-slate-500">Type</label>
                    <p className="text-sm text-slate-800 capitalize">{node.node_type}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">Category</label>
                    <p className="text-sm text-slate-800">{categoryLabels[node.category]}</p>
                  </div>
                </div>
                {node.flow_index && (
                  <div>
                    <label className="text-xs text-slate-500">Flow Index</label>
                    <p className="font-mono text-sm text-slate-800">{node.flow_index}</p>
                  </div>
                )}
              </div>
            </section>

            {/* Status Section */}
            <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
              <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 ${isFullscreen ? 'text-sm' : ''}`}>Status</h4>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[nodeStatus]}`}>
                  {nodeStatus}
                </span>
                {node.data.is_ground && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
                    Ground
                  </span>
                )}
                {node.data.is_final && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700">
                    Output
                  </span>
                )}
                {node.data.is_context && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                    Context
                  </span>
                )}
              </div>
            </section>

            {/* Step Progress Section - Show for running/completed function nodes */}
            {node.flow_index && stepProgress[node.flow_index] && (
              <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
                <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1 ${isFullscreen ? 'text-sm' : ''}`}>
                  <Workflow size={12} /> Execution Pipeline
                </h4>
                <StepPipeline 
                  progress={stepProgress[node.flow_index]} 
                  compact={false}
                />
              </section>
            )}

            {/* Debugging Section */}
            {node.flow_index && (
              <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
                <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 ${isFullscreen ? 'text-sm' : ''}`}>Debugging</h4>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={handleToggleBreakpoint}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs transition-colors ${
                      hasBreakpoint
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <Circle size={10} className={hasBreakpoint ? 'fill-red-500 text-red-500' : ''} />
                    {hasBreakpoint ? 'Remove BP' : 'Add BP'}
                  </button>
                  {status !== 'running' && nodeStatus === 'pending' && (
                    <button
                      onClick={handleRunTo}
                      disabled={isRunningTo}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors disabled:opacity-50"
                    >
                      <Play size={10} className={isRunningTo ? 'animate-pulse' : ''} />
                      {isRunningTo ? 'Running...' : 'Run To'}
                    </button>
                  )}
                </div>
              </section>
            )}

            {/* Data Section - Value Nodes */}
            {node.node_type === 'value' && (
              <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
                <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1 ${isFullscreen ? 'text-sm' : ''}`}>
                  <Layers size={12} /> Value Details
                </h4>
                <div className="space-y-2">
                  {node.data.axes && node.data.axes.length > 0 && (
                    <div>
                      <label className="text-xs text-slate-500">Axes</label>
                      <p className="font-mono text-sm text-slate-800">[{node.data.axes.join(', ')}]</p>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Function Details Section - Function Nodes */}
            {node.node_type === 'function' && (
              <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
                <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1 ${isFullscreen ? 'text-sm' : ''}`}>
                  <FileJson size={12} /> Function Details
                </h4>
                <div className="space-y-3">
                  {/* Sequence Type */}
                  {node.data.sequence && (
                    <div>
                      <label className="text-xs text-slate-500">Sequence Type</label>
                      <p className="text-sm text-slate-800 font-medium">{node.data.sequence}</p>
                    </div>
                  )}

                  {/* Working Interpretation - Parsed View */}
                  {node.data.working_interpretation && (
                    <div className="space-y-2">
                      <label className="text-xs text-slate-500">Working Interpretation</label>
                      
                      {/* Paradigm */}
                      {node.data.working_interpretation.paradigm && (
                        <div className="bg-purple-50 p-2 rounded border border-purple-200">
                          <label className="text-xs text-purple-600 font-medium">Paradigm</label>
                          <p className="font-mono text-xs text-purple-800 break-all">
                            {node.data.working_interpretation.paradigm}
                          </p>
                        </div>
                      )}
                      
                      {/* Value Order */}
                      {node.data.working_interpretation.value_order && (
                        <div className="bg-blue-50 p-2 rounded border border-blue-200">
                          <label className="text-xs text-blue-600 font-medium">Value Order</label>
                          <div className="mt-1 space-y-1">
                            {Object.entries(node.data.working_interpretation.value_order).map(([key, val]) => (
                              <div key={key} className="flex justify-between text-xs">
                                <span className={`font-mono text-blue-700 truncate ${isFullscreen ? 'max-w-none' : 'max-w-[180px]'}`} title={key}>{key}</span>
                                <span className="text-blue-900 font-medium">:{String(val)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Prompt Location */}
                      {node.data.working_interpretation.prompt_location && (
                        <div className="bg-green-50 p-2 rounded border border-green-200">
                          <label className="text-xs text-green-600 font-medium">Prompt Location</label>
                          <p className="font-mono text-xs text-green-800 break-all">
                            {node.data.working_interpretation.prompt_location}
                          </p>
                        </div>
                      )}

                      {/* Output Type */}
                      {node.data.working_interpretation.output_type && (
                        <div className="bg-orange-50 p-2 rounded border border-orange-200">
                          <label className="text-xs text-orange-600 font-medium">Output Type</label>
                          <p className="font-mono text-xs text-orange-800">
                            {node.data.working_interpretation.output_type}
                          </p>
                        </div>
                      )}

                      {/* Other fields as collapsible JSON */}
                      {(() => {
                        const knownKeys = ['paradigm', 'value_order', 'prompt_location', 'output_type'];
                        const otherFields = Object.entries(node.data.working_interpretation)
                          .filter(([key]) => !knownKeys.includes(key));
                        
                        if (otherFields.length > 0) {
                          return (
                            <details className="bg-slate-50 p-2 rounded border border-slate-200" open={isFullscreen}>
                              <summary className="text-xs text-slate-600 font-medium cursor-pointer">
                                Other Properties ({otherFields.length})
                              </summary>
                              <pre className={`text-xs text-slate-700 mt-2 overflow-x-auto ${isFullscreen ? 'max-h-none' : ''}`}>
                                {JSON.stringify(Object.fromEntries(otherFields), null, 2)}
                              </pre>
                            </details>
                          );
                        }
                        return null;
                      })()}
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Connections Section */}
            <section className={isFullscreen ? 'bg-slate-50 p-4 rounded-lg' : ''}>
              <h4 className={`text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1 ${isFullscreen ? 'text-sm' : ''}`}>
                <GitBranch size={12} /> Connections
              </h4>
              <div className={isFullscreen ? 'grid grid-cols-2 gap-4' : 'space-y-2'}>
                <div>
                  <label className="text-xs text-slate-500">
                    Incoming ({edges.incoming.length})
                  </label>
                  {edges.incoming.length > 0 ? (
                    <ul className="text-sm text-slate-700 space-y-1">
                      {edges.incoming.map((e) => (
                        <li key={e.id} className={`font-mono text-xs ${isFullscreen ? '' : 'truncate'}`}>
                          ← {e.source.split('@')[0]}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400">None</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-slate-500">
                    Outgoing ({edges.outgoing.length})
                  </label>
                  {edges.outgoing.length > 0 ? (
                    <ul className="text-sm text-slate-700 space-y-1">
                      {edges.outgoing.map((e) => (
                        <li key={e.id} className={`font-mono text-xs ${isFullscreen ? '' : 'truncate'}`}>
                          → {e.target.split('@')[0]}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400">None</p>
                  )}
                </div>
              </div>
            </section>
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
              
              {/* For function nodes in fullscreen, show additional details */}
              {node.node_type === 'function' && (
                <section className="bg-purple-50/50 p-4 rounded-lg border border-purple-100 h-full flex flex-col">
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
              )}
            </div>
          )}

          {/* Reference Data Section (for value nodes) - Normal mode only */}
          {!isFullscreen && node.node_type === 'value' && (
            <section>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1">
                  <Database size={12} /> Reference Data
                </h4>
                <button
                  onClick={refreshReference}
                  disabled={isLoadingRef}
                  className="p-1 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50"
                  title="Refresh reference data"
                >
                  <RefreshCw size={12} className={isLoadingRef ? 'animate-spin' : ''} />
                </button>
              </div>
              
              {isLoadingRef ? (
                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <RefreshCw size={12} className="animate-spin" />
                  Loading...
                </div>
              ) : refError ? (
                <div className="text-xs text-red-500">{refError}</div>
              ) : referenceData ? (
                <TensorInspector
                  data={referenceData.data}
                  axes={referenceData.axes}
                  conceptName={referenceData.concept_name}
                  isGround={node.data.is_ground}
                  isCompact={true}
                />
              ) : (
                <div className="text-xs text-slate-400 bg-slate-50 p-2 rounded">
                  {node.data.is_ground 
                    ? 'Ground concept - load repositories to see data'
                    : 'No reference data yet - execute to compute'}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
