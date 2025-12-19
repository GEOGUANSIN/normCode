/**
 * Detail Panel for selected node inspection
 * Enhanced with tensor data visualization and reference fetching
 */

import { useEffect, useState } from 'react';
import { X, Circle, Layers, GitBranch, FileJson, RefreshCw, Database, Play } from 'lucide-react';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi, ReferenceData } from '../../services/api';
import { TensorInspector } from './TensorInspector';

export function DetailPanel() {
  const selectedNodeId = useSelectionStore((s) => s.selectedNodeId);
  const clearSelection = useSelectionStore((s) => s.clearSelection);
  const getNode = useGraphStore((s) => s.getNode);
  const getEdgesForNode = useGraphStore((s) => s.getEdgesForNode);
  const nodeStatuses = useExecutionStore((s) => s.nodeStatuses);
  const breakpoints = useExecutionStore((s) => s.breakpoints);
  const toggleBreakpoint = useExecutionStore((s) => s.toggleBreakpoint);
  const status = useExecutionStore((s) => s.status);

  // Reference data state
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [isLoadingRef, setIsLoadingRef] = useState(false);
  const [refError, setRefError] = useState<string | null>(null);

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
        setReferenceData(data);
      } catch (e) {
        // 404 is expected for concepts without references
        if ((e as { status?: number }).status !== 404) {
          setRefError('Failed to load reference data');
        }
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
    try {
      const data = await executionApi.getReference(conceptName);
      setReferenceData(data);
      setRefError(null);
    } catch (e) {
      if ((e as { status?: number }).status !== 404) {
        setRefError('Failed to load reference data');
      }
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
    if (!node.flow_index) return;
    
    try {
      if (hasBreakpoint) {
        await executionApi.clearBreakpoint(node.flow_index);
      } else {
        await executionApi.setBreakpoint(node.flow_index, true);
      }
      toggleBreakpoint(node.flow_index);
    } catch (e) {
      console.error('Failed to toggle breakpoint:', e);
    }
  };

  const handleRunTo = async () => {
    if (!node.flow_index) return;
    // TODO: Implement run-to functionality
    console.log('Run to:', node.flow_index);
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
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                >
                  <Play size={10} />
                  Run To
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

        {/* Data Section */}
        <section>
          <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
            <Layers size={12} /> Metadata
          </h4>
          <div className="space-y-2">
            {node.data.axes && node.data.axes.length > 0 && (
              <div>
                <label className="text-xs text-slate-500">Axes</label>
                <p className="font-mono text-sm text-slate-800">[{node.data.axes.join(', ')}]</p>
              </div>
            )}
            {node.data.sequence && (
              <div>
                <label className="text-xs text-slate-500">Sequence</label>
                <p className="text-sm text-slate-800">{node.data.sequence}</p>
              </div>
            )}
            {node.data.working_interpretation && (
              <div>
                <label className="text-xs text-slate-500">Working Interpretation</label>
                <pre className="text-xs bg-slate-50 p-2 rounded overflow-x-auto max-h-32">
                  {JSON.stringify(node.data.working_interpretation, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </section>

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
