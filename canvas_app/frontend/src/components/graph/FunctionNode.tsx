/**
 * Custom React Flow node for Function concepts
 * Supports collapse/expand and branch highlighting
 * 
 * PERFORMANCE OPTIMIZED:
 * - Single selector for execution state (status + breakpoint)
 * - Single selector for graph state (collapsed, highlight, etc.)
 * - Shallow comparison via Zustand's built-in equality check
 */

import { memo, useCallback, useMemo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { useGraphStore, useNodeGraphState } from '../../stores/graphStore';
import type { NodeCategory } from '../../types/graph';
import { shallow } from 'zustand/shallow';

interface FunctionNodeData {
  label: string;
  category: NodeCategory;
  flowIndex: string | null;
  sequence?: string;
  naturalName?: string;  // Human-readable name from concept repo
}

const categoryStyles: Record<NodeCategory, { bg: string; border: string; text: string }> = {
  'semantic-function': {
    bg: 'bg-purple-50',
    border: 'border-purple-400',
    text: 'text-purple-900',
  },
  'syntactic-function': {
    bg: 'bg-slate-100',
    border: 'border-slate-400',
    text: 'text-slate-700',
  },
  'semantic-value': {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    text: 'text-blue-900',
  },
  'proposition': {
    bg: 'bg-slate-100',
    border: 'border-teal-700',
    text: 'text-slate-700',
  },
};

const sequenceBadgeColors: Record<string, string> = {
  imperative: 'bg-purple-200 text-purple-800',
  judgement: 'bg-orange-200 text-orange-800',
  assigning: 'bg-slate-200 text-slate-700',
  grouping: 'bg-green-200 text-green-800',
  timing: 'bg-blue-200 text-blue-800',
  looping: 'bg-yellow-200 text-yellow-800',
};

const statusIndicators = {
  pending: 'bg-gray-400',
  running: 'bg-blue-500 animate-pulse',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  skipped: 'bg-yellow-400',
};

export const FunctionNode = memo(({ data, id, selected }: NodeProps<FunctionNodeData>) => {
  // OPTIMIZED: Single selector for execution state - only re-renders when THIS node's status changes
  const { status, hasBreakpoint } = useExecutionStore(
    useCallback((s) => ({
      status: data.flowIndex ? s.nodeStatuses[data.flowIndex] || 'pending' : 'pending',
      hasBreakpoint: data.flowIndex ? s.breakpoints.has(data.flowIndex) : false,
    }), [data.flowIndex]),
    shallow
  );
  
  // Check if this concept has data - query blackboard directly (source of truth)
  // This is cleaner than trying to infer from node statuses, and allows
  // the infra layer to remain independent of canvas-app state tracking
  const conceptStatuses = useExecutionStore((s) => s.conceptStatuses);
  
  const conceptHasData = useMemo(() => {
    if (!data.label) return false;
    // If this node itself is completed, obviously has data
    if (status === 'completed') return true;
    // Check blackboard's concept status (source of truth from infra layer)
    const conceptStatus = conceptStatuses[data.label];
    return conceptStatus === 'complete';
  }, [data.label, status, conceptStatuses]);
  
  // OPTIMIZED: Use custom hook that batches all graph state for this node
  const { 
    isCollapsed, 
    hasChildren, 
    isHighlighted, 
    hasHighlight, 
    isSameConcept,
    hasMultipleOccurrences,
    occurrenceCount 
  } = useNodeGraphState(id);
  
  const toggleCollapse = useGraphStore((s) => s.toggleCollapse);
  
  const style = categoryStyles[data.category] || categoryStyles['syntactic-function'];

  // Extract sequence type for badge
  const sequenceType = data.sequence?.split('_')[0] || data.sequence;
  const badgeColor = sequenceBadgeColors[sequenceType || ''] || 'bg-gray-200 text-gray-700';

  // Use natural_name if available, otherwise fall back to label (concept_name)
  const primaryLabel = data.naturalName || data.label;
  
  // Truncate long labels
  const displayLabel = primaryLabel.length > 35 
    ? primaryLabel.substring(0, 32) + '...' 
    : primaryLabel;

  // Handle collapse button click
  const handleCollapseClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent node selection
    toggleCollapse(id);
  }, [id, toggleCollapse]);

  // Determine opacity based on highlighting
  // Don't dim nodes that are highlighted as "same concept"
  const opacity = hasHighlight && !isHighlighted && !isSameConcept ? 'opacity-30' : '';

  // Memoize className to avoid recalculation during pan/zoom
  const nodeClassName = useMemo(() => {
    const classes = [
      'relative px-3 py-2 min-w-[120px] max-w-[220px] shadow-sm border-2 rounded-md',
      style.bg, style.border, style.text,
    ];
    if (selected) classes.push('ring-2 ring-offset-2 ring-indigo-500 shadow-md');
    if (status === 'running') classes.push('ring-2 ring-blue-400 animate-pulse');
    else if (status === 'completed') classes.push('ring-1 ring-green-400');
    else if (status === 'failed') classes.push('ring-2 ring-red-500');
    else if (status === 'skipped') classes.push('opacity-50');
    if (isSameConcept && !selected) classes.push('ring-2 ring-amber-400 ring-offset-1 shadow-amber-200 shadow-md');
    if (opacity) classes.push(opacity);
    return classes.join(' ');
  }, [style, selected, status, isSameConcept, opacity]);

  // Memoize the clip-path style object
  const clipPathStyle = useMemo(() => ({
    clipPath: 'polygon(8px 0, calc(100% - 8px) 0, 100% 50%, calc(100% - 8px) 100%, 8px 100%, 0 50%)',
  }), []);

  return (
    <div className={nodeClassName} style={clipPathStyle}>
      {/* Input handle (left) - receives data from children on the left */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2 h-2 !bg-purple-400"
        style={{ left: -4 }}
      />

      {/* Collapse/Expand button - only show for nodes with children */}
      {hasChildren && (
        <button
          onClick={handleCollapseClick}
          className={`
            absolute -left-3 top-1/2 -translate-y-1/2 
            w-5 h-5 rounded-full 
            bg-white border border-purple-300 shadow-sm
            flex items-center justify-center
            hover:bg-purple-50 hover:border-purple-400
            transition-colors z-10
          `}
          title={isCollapsed ? 'Expand branch' : 'Collapse branch'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-3 h-3 text-purple-600" />
          ) : (
            <ChevronDown className="w-3 h-3 text-purple-600" />
          )}
        </button>
      )}

      {/* Collapsed indicator */}
      {isCollapsed && (
        <div className="absolute -left-1 -bottom-1 text-[8px] bg-purple-600 text-white px-1 rounded">
          ⋯
        </div>
      )}

      {/* Node content */}
      <div className="text-center px-2">
        <div 
          className={`text-xs leading-tight break-words ${data.naturalName ? '' : 'font-mono'}`}
          title={data.naturalName ? `${data.naturalName}\n(${data.label})` : data.label}
        >
          {displayLabel}
        </div>
        
        {/* Show concept name as secondary label when natural_name is used */}
        {data.naturalName && (
          <div className="font-mono text-[8px] opacity-50 mt-0.5 truncate" title={data.label}>
            {data.label.length > 28 ? data.label.substring(0, 25) + '...' : data.label}
          </div>
        )}
        
        {/* Sequence type badge */}
        {sequenceType && (
          <div className={`inline-block text-[9px] px-1.5 py-0.5 rounded mt-1 ${badgeColor}`}>
            {sequenceType}
          </div>
        )}
      </div>

      {/* Status indicator dot */}
      <div
        className={`
          absolute -top-1 -right-1 w-3 h-3 rounded-full border border-white
          ${statusIndicators[status] || statusIndicators.pending}
        `}
        title={status}
      />
      
      {/* "Concept has data" indicator - shows when this concept has data from an alias
          but THIS node's inference hasn't run yet. Helps distinguish "data available" 
          from "inference not yet executed" */}
      {conceptHasData && status === 'pending' && (
        <div
          className="absolute -top-1 right-2 w-2 h-2 rounded-full bg-green-400 border border-white opacity-70"
          title="Concept has data (from another inference)"
        />
      )}

      {/* Breakpoint indicator - position adjusted based on whether node has children (collapse button) */}
      {hasBreakpoint && (
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-red-500 border-2 border-white z-20 ${
            hasChildren ? '-left-5' : '-left-1'
          }`}
          title="Breakpoint"
        />
      )}

      {/* Same concept indicator - shows when node is part of highlighted same-concept group */}
      {isSameConcept && !selected && (
        <div className="absolute -top-2 -left-2 text-[8px] bg-amber-500 text-white px-1 rounded-full w-4 h-4 flex items-center justify-center font-bold z-20" title="Same concept - highlighted">
          ≡
        </div>
      )}

      {/* Multiple occurrences badge - always visible when concept appears multiple times */}
      {hasMultipleOccurrences && !isSameConcept && !selected && (
        <div 
          className="absolute -top-2 -right-4 text-[9px] bg-slate-500 text-white px-1.5 py-0.5 rounded-full font-medium z-20 border border-white shadow-sm"
          title={`This concept appears ${occurrenceCount} times in the visible graph`}
        >
          ×{occurrenceCount}
        </div>
      )}

      {/* Output handle (right) - sends data to parent on the right */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-2 h-2 !bg-purple-400"
        style={{ right: -4 }}
      />
    </div>
  );
});

FunctionNode.displayName = 'FunctionNode';
