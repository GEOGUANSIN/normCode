/**
 * Custom React Flow node for Value concepts
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

interface ValueNodeData {
  label: string;
  category: NodeCategory;
  flowIndex: string | null;
  isGround?: boolean;
  isFinal?: boolean;
  axes?: string[];
  naturalName?: string;  // Human-readable name from concept repo
}

const categoryStyles: Record<NodeCategory, { bg: string; border: string; text: string }> = {
  'semantic-value': {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    text: 'text-blue-900',
  },
  'semantic-function': {
    bg: 'bg-purple-50',
    border: 'border-purple-400',
    text: 'text-purple-900',
  },
  'syntactic-function': {
    bg: 'bg-slate-100',
    border: 'border-slate-400',
    text: 'text-slate-900',
  },
  'proposition': {
    bg: 'bg-slate-100',
    border: 'border-teal-700',
    text: 'text-slate-700',
  },
};

const statusIndicators = {
  pending: 'bg-gray-400',
  running: 'bg-blue-500 animate-pulse',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  skipped: 'bg-yellow-400',
};

export const ValueNode = memo(({ data, id, selected }: NodeProps<ValueNodeData>) => {
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
  
  const style = categoryStyles[data.category] || categoryStyles['semantic-value'];

  // Use natural_name if available, otherwise fall back to label (concept_name)
  const primaryLabel = data.naturalName || data.label;
  
  // Truncate long labels
  const displayLabel = primaryLabel.length > 30 
    ? primaryLabel.substring(0, 27) + '...' 
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
      'relative px-3 py-2 rounded-lg border-2 min-w-[100px] max-w-[200px] shadow-sm',
      style.bg, style.border, style.text,
    ];
    if (selected) classes.push('ring-2 ring-offset-2 ring-indigo-500 shadow-md');
    if (data.isGround) classes.push('border-double border-4');
    if (data.isFinal) classes.push('ring-2 ring-red-400');
    if (status === 'running') classes.push('ring-2 ring-blue-400 animate-pulse');
    else if (status === 'completed') classes.push('ring-1 ring-green-400');
    else if (status === 'failed') classes.push('ring-2 ring-red-500');
    else if (status === 'skipped') classes.push('opacity-50');
    if (isSameConcept && !selected) classes.push('ring-2 ring-amber-400 ring-offset-1 shadow-amber-200 shadow-md');
    if (opacity) classes.push(opacity);
    return classes.join(' ');
  }, [style, selected, data.isGround, data.isFinal, status, isSameConcept, opacity]);

  return (
    <div className={nodeClassName}>
      {/* Input handle (left) - receives data from children on the left */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2 h-2 !bg-slate-400"
      />

      {/* Collapse/Expand button - only show for nodes with children */}
      {hasChildren && (
        <button
          onClick={handleCollapseClick}
          className={`
            absolute -left-3 top-1/2 -translate-y-1/2 
            w-5 h-5 rounded-full 
            bg-white border border-slate-300 shadow-sm
            flex items-center justify-center
            hover:bg-slate-100 hover:border-slate-400
            transition-colors z-10
          `}
          title={isCollapsed ? 'Expand branch' : 'Collapse branch'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-3 h-3 text-slate-600" />
          ) : (
            <ChevronDown className="w-3 h-3 text-slate-600" />
          )}
        </button>
      )}

      {/* Collapsed indicator - shows count of hidden descendants */}
      {isCollapsed && (
        <div className="absolute -left-1 -bottom-1 text-[8px] bg-slate-600 text-white px-1 rounded">
          ⋯
        </div>
      )}

      {/* Node content */}
      <div className="text-center">
        <div 
          className={`text-xs leading-tight break-words ${data.naturalName ? '' : 'font-mono'}`}
          title={data.naturalName ? `${data.naturalName}\n(${data.label})` : data.label}
        >
          {displayLabel}
        </div>
        
        {/* Show concept name as secondary label when natural_name is used */}
        {data.naturalName && (
          <div className="font-mono text-[9px] opacity-50 mt-0.5 truncate" title={data.label}>
            {data.label.length > 25 ? data.label.substring(0, 22) + '...' : data.label}
          </div>
        )}
        
        {/* Axes indicator */}
        {data.axes && data.axes.length > 0 && (
          <div className="text-[10px] opacity-60 mt-1 truncate">
            [{data.axes.join(', ')}]
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

      {/* Ground concept indicator */}
      {data.isGround && (
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[8px] bg-slate-600 text-white px-1 rounded">
          ground
        </div>
      )}

      {/* Final concept indicator */}
      {data.isFinal && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[8px] bg-red-500 text-white px-1 rounded">
          output
        </div>
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
        className="w-2 h-2 !bg-slate-400"
      />
    </div>
  );
});

ValueNode.displayName = 'ValueNode';
