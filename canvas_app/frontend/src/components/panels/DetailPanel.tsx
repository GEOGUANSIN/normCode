/**
 * Detail Panel for selected node inspection
 * Enhanced with tensor data visualization and reference fetching
 */

import { useEffect, useState } from 'react';
import { X, Circle, Layers, GitBranch, FileJson, RefreshCw, Database, Play, Workflow } from 'lucide-react';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi, ReferenceData } from '../../services/api';
import { TensorInspector } from './TensorInspector';
import { StepPipeline } from './StepPipeline';

export function DetailPanel() {
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

  if (!selectedNodeId) {
    return (
      <div className="w-80 bg-white border-l border-slate-200 p-4 flex items-center justify-center text-slate-500 text-sm">
        Select a node to view details
      </div>
    );
  }

  const node = getNode(selectedNodeId);
  if (!node) {
    return (
      <div className="w-80 bg-white border-l border-slate-200 p-4">
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
    <div className="w-80 bg-white border-l border-slate-200 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200">
        <h3 className="font-semibold text-slate-800">Node Details</h3>
        <button
          onClick={clearSelection}
          className="p-1 rounded hover:bg-slate-100 text-slate-500"
        >
          <X size={18} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Identity Section */}
        <section>
          <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Identity</h4>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-slate-500">Name</label>
              <p className="font-mono text-sm text-slate-800 break-words">{node.label}</p>
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
        <section>
          <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Status</h4>
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
          <section>
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
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
          <section>
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Debugging</h4>
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

        {/* Reference Data Section (for value nodes) */}
        {node.node_type === 'value' && (
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

        {/* Data Section - Value Nodes */}
        {node.node_type === 'value' && (
          <section>
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
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
          <section>
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
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
                            <span className="font-mono text-blue-700 truncate max-w-[180px]" title={key}>{key}</span>
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
                        <details className="bg-slate-50 p-2 rounded border border-slate-200">
                          <summary className="text-xs text-slate-600 font-medium cursor-pointer">
                            Other Properties ({otherFields.length})
                          </summary>
                          <pre className="text-xs text-slate-700 mt-2 overflow-x-auto">
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
        <section>
          <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
            <GitBranch size={12} /> Connections
          </h4>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-slate-500">
                Incoming ({edges.incoming.length})
              </label>
              {edges.incoming.length > 0 ? (
                <ul className="text-sm text-slate-700 space-y-1">
                  {edges.incoming.map((e) => (
                    <li key={e.id} className="font-mono text-xs truncate">
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
                    <li key={e.id} className="font-mono text-xs truncate">
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
    </div>
  );
}
