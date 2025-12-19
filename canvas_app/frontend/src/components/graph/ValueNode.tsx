/**
 * Custom React Flow node for Value concepts
 * Supports collapse/expand and branch highlighting
 */

import { memo, useCallback } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { useGraphStore } from '../../stores/graphStore';
import type { NodeCategory } from '../../types/graph';

interface ValueNodeData {
  label: string;
  category: NodeCategory;
  flowIndex: string | null;
  isGround?: boolean;
  isFinal?: boolean;
  axes?: string[];
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
};

const statusIndicators = {
  pending: 'bg-gray-400',
  running: 'bg-blue-500 animate-pulse',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  skipped: 'bg-yellow-400',
};

export const ValueNode = memo(({ data, id, selected }: NodeProps<ValueNodeData>) => {
  const nodeStatuses = useExecutionStore((s) => s.nodeStatuses);
  const breakpoints = useExecutionStore((s) => s.breakpoints);
  
  // Collapse/expand state
  const isCollapsed = useGraphStore((s) => s.isCollapsed(id));
  const hasChildren = useGraphStore((s) => s.hasChildren(id));
  const toggleCollapse = useGraphStore((s) => s.toggleCollapse);
  
  // Highlight state
  const isHighlighted = useGraphStore((s) => s.isHighlighted(id));
  const highlightedBranch = useGraphStore((s) => s.highlightedBranch);
  const hasHighlight = highlightedBranch.size > 0;
  
  // Get status from flow_index
  const status = data.flowIndex ? nodeStatuses[data.flowIndex] || 'pending' : 'pending';
  const hasBreakpoint = data.flowIndex ? breakpoints.has(data.flowIndex) : false;
  
  const style = categoryStyles[data.category] || categoryStyles['semantic-value'];

  // Truncate long labels
  const displayLabel = data.label.length > 30 
    ? data.label.substring(0, 27) + '...' 
    : data.label;

  // Handle collapse button click
  const handleCollapseClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent node selection
    toggleCollapse(id);
  }, [id, toggleCollapse]);

  // Determine opacity based on highlighting
  const opacity = hasHighlight && !isHighlighted ? 'opacity-30' : '';

  return (
    <div
      className={`
        relative px-3 py-2 rounded-lg border-2 min-w-[100px] max-w-[200px]
        shadow-sm transition-all duration-200
        ${style.bg} ${style.border} ${style.text}
        ${selected ? 'ring-2 ring-offset-2 ring-indigo-500 shadow-md' : ''}
        ${data.isGround ? 'border-double border-4' : ''}
        ${data.isFinal ? 'ring-2 ring-red-400' : ''}
        ${status === 'running' ? 'ring-2 ring-blue-400 animate-pulse' : ''}
        ${status === 'completed' ? 'ring-1 ring-green-400' : ''}
        ${status === 'failed' ? 'ring-2 ring-red-500' : ''}
        ${status === 'skipped' ? 'opacity-50' : ''}
        ${opacity}
        hover:shadow-md
      `}
    >
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
          className="font-mono text-xs leading-tight break-words"
          title={data.label}
        >
          {displayLabel}
        </div>
        
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

      {/* Breakpoint indicator */}
      {hasBreakpoint && (
        <div
          className="absolute -left-1 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-red-500 border-2 border-white"
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
