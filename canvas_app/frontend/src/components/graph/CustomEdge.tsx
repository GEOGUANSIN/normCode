/**
 * Custom React Flow edge with styling based on edge type
 */

import { memo } from 'react';
import { 
  BaseEdge, 
  getSmoothStepPath, 
  type EdgeProps,
  EdgeLabelRenderer,
} from 'reactflow';

interface CustomEdgeData {
  edgeType: 'function' | 'value' | 'context' | 'alias';
  label?: string;
}

const edgeColors = {
  function: '#7b68ee', // Purple for function edges
  value: '#3b82f6',    // Blue for value edges
  context: '#10b981',  // Green for context edges
  alias: '#9ca3af',    // Gray for alias edges (same concept at different positions)
};

export const CustomEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps<CustomEdgeData>) => {
  const edgeType = data?.edgeType || 'value';
  const color = edgeColors[edgeType];

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 8,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: color,
          strokeWidth: selected ? 3 : (edgeType === 'alias' ? 1.5 : 2),
          opacity: selected ? 1 : (edgeType === 'alias' ? 0.5 : 0.7),
          strokeDasharray: edgeType === 'alias' ? '5,5' : undefined,
        }}
      />
      
      {/* Edge label */}
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: 'none',
            }}
            className={`
              text-[9px] px-1 py-0.5 rounded
              bg-white border shadow-sm
              ${edgeType === 'function' ? 'border-purple-300 text-purple-700' : ''}
              ${edgeType === 'value' ? 'border-blue-300 text-blue-700' : ''}
              ${edgeType === 'context' ? 'border-green-300 text-green-700' : ''}
              ${edgeType === 'alias' ? 'border-gray-300 text-gray-500 italic' : ''}
            `}
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

CustomEdge.displayName = 'CustomEdge';
