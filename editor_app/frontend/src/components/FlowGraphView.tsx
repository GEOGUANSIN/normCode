import React, { useMemo, useRef, useState } from 'react';
import { ConceptEntry, InferenceEntry } from '../types';
import './FlowGraphView.css';

interface FlowGraphViewProps {
  concepts: ConceptEntry[];
  inferences: InferenceEntry[];
  graphData: any | null;
}

interface GraphNode {
  id: string;
  label: string;
  type: 'concept';
  x: number;
  y: number;
  level: number;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  type: 'function' | 'value';
  inferenceSequence: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const truncateLabel = (label: string, maxLength: number = 15): string => {
  if (label.length > maxLength) {
    return label.substring(0, maxLength) + '...';
  }
  return label;
};

const getNodeCategory = (label: string): 'semantic-function' | 'semantic-value' | 'syntactic-function' => {
  // Semantic functions: ::({}) and <{}>
  if (label.includes(':(') || label.includes(':<')) {
    return 'semantic-function';
  }
  
  // Semantic values: {}, <>, []
  // Check for these patterns at the start and end of the label
  if ((label.startsWith('{') && label.endsWith('}')) || 
      (label.startsWith('<') && label.endsWith('>')) || 
      (label.startsWith('[') && label.endsWith(']'))) {
    return 'semantic-value';
  }
  
  // Syntactic functions: everything else
  return 'syntactic-function';
};

const FlowGraphView: React.FC<FlowGraphViewProps> = ({ 
  concepts: _concepts,
  inferences: _inferences,
  graphData: graphDataProp
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);

  const graphData = useMemo((): GraphData => {
    if (!graphDataProp || !graphDataProp.nodes || graphDataProp.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    // Convert backend graph data to frontend format
    const nodes: GraphNode[] = graphDataProp.nodes.map((node: any) => ({
      id: node.id,
      label: node.label,
      type: node.type,
      x: node.x,
      y: node.y,
      level: node.level
    }));

    const edges: GraphEdge[] = graphDataProp.edges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: edge.type,
      inferenceSequence: edge.inferenceSequence
    }));

    return { nodes, edges };
  }, [graphDataProp]);

  // Calculate SVG viewBox based on node positions
  const viewBox = useMemo(() => {
    if (graphData.nodes.length === 0) {
      return '0 0 800 600';
    }

    const padding = 100;
    const minX = Math.min(...graphData.nodes.map(n => n.x)) - padding;
    const maxX = Math.max(...graphData.nodes.map(n => n.x)) + padding;
    const minY = Math.min(...graphData.nodes.map(n => n.y)) - padding;
    const maxY = Math.max(...graphData.nodes.map(n => n.y)) + padding;

    const width = Math.max(800, maxX - minX);
    const height = Math.max(600, maxY - minY);

    return `${minX} ${minY} ${width} ${height}`;
  }, [graphData.nodes]);

  const getEdgePath = (edge: GraphEdge): string => {
    const sourceNode = graphData.nodes.find(n => n.id === edge.source);
    const targetNode = graphData.nodes.find(n => n.id === edge.target);

    if (!sourceNode || !targetNode) return '';

    const nodeWidth = 150;
    const arrowWidth = 10; // Leave space for the arrowhead
    const x1 = sourceNode.x - nodeWidth / 2;
    const y1 = sourceNode.y;
    const x2 = targetNode.x + nodeWidth / 2 + arrowWidth;
    const y2 = targetNode.y;

    // Create a curved path
    const midX = (x1 + x2) / 2;
    
    return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
  };

  if (!graphDataProp || graphData.nodes.length === 0) {
    return (
      <div className="flow-graph-empty">
        <div className="flow-empty-state">
          <p>No flow data to visualize.</p>
          <p className="flow-hint">
            Build your flow in the Flow Editor tab first, then come back here to see the graph visualization.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flow-graph-container">
      <div className="flow-graph-header">
        <h3>Flow Graph View</h3>
        <div className="flow-graph-legend">
          <div className="legend-item">
            <div className="legend-box semantic-function"></div>
            <span>Semantic Functions (::&#40;&#123;&#125;&#41;, &lt;&#123;&#125;&gt;)</span>
          </div>
          <div className="legend-item">
            <div className="legend-box semantic-value"></div>
            <span>Semantic Values (&#123;&#125;, &lt;&gt;, [ ])</span>
          </div>
          <div className="legend-item">
            <div className="legend-box syntactic-function"></div>
            <span>Syntactic Functions</span>
          </div>
          <div className="legend-divider"></div>
          <div className="legend-item">
            <div className="legend-line function-edge"></div>
            <span>Function (&lt;=)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line value-edge"></div>
            <span>Value (&lt;-)</span>
          </div>
        </div>
      </div>

      <div className="flow-graph-canvas">
        <svg 
          ref={svgRef} 
          className="flow-graph-svg"
          viewBox={viewBox}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <marker
              id="arrowhead-function"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,6 L9,3 z" fill="#4a90e2" />
            </marker>
            <marker
              id="arrowhead-value"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,6 L9,3 z" fill="#7b68ee" />
            </marker>
          </defs>

          {/* Render edges first (so they appear behind nodes) */}
          {graphData.edges.map(edge => {
            const path = getEdgePath(edge);
            const isSelected = selectedEdge === edge.id;
            const isRelated = selectedNode && (edge.source === selectedNode || edge.target === selectedNode);
            const isDimmed = selectedNode && !isRelated;
            
            return (
              <g key={edge.id}>
                <path
                  d={path}
                  className={`graph-edge ${edge.type}-edge ${isSelected ? 'selected' : ''} ${isDimmed ? 'dimmed' : ''}`}
                  markerEnd={`url(#arrowhead-${edge.type})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedEdge(edge.id);
                    setSelectedNode(null);
                  }}
                />
                {isSelected && (
                  <text
                    x={(graphData.nodes.find(n => n.id === edge.source)!.x + graphData.nodes.find(n => n.id === edge.target)!.x) / 2}
                    y={(graphData.nodes.find(n => n.id === edge.source)!.y + graphData.nodes.find(n => n.id === edge.target)!.y) / 2 - 10}
                    className="edge-label"
                    textAnchor="middle"
                  >
                    {edge.inferenceSequence}
                  </text>
                )}
              </g>
            );
          })}

          {/* Render nodes */}
          {graphData.nodes.map(node => {
            const isSelected = selectedNode === node.id;
            const isDimmed = selectedNode && !isSelected;
            const category = getNodeCategory(node.label);

            return (
              <g 
                key={node.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNode(node.id);
                  setSelectedEdge(null);
                }}
              >
                <title>{node.label}</title>
                <rect
                  x={node.x - 75}
                  y={node.y - 30}
                  width="150"
                  height="60"
                  className={`graph-node ${category} ${isSelected ? 'selected' : ''} ${isDimmed ? 'dimmed' : ''}`}
                  rx="8"
                />
                <text
                  x={node.x}
                  y={node.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="node-label"
                >
                  {truncateLabel(node.label)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Info panel */}
      <div className="flow-graph-info">
        {selectedNode && (
          <div className="info-panel">
            <h4>Concept: {selectedNode}</h4>
            <div className="info-section">
              <strong>Incoming connections:</strong>
              <ul>
                {graphData.edges
                  .filter(e => e.target === selectedNode)
                  .map(e => (
                    <li key={e.id}>
                      {e.source} 
                      <span className={`edge-type-badge ${e.type}`}>
                        {e.type === 'function' ? '<=' : '<-'}
                      </span>
                      {e.inferenceSequence}
                    </li>
                  ))}
              </ul>
            </div>
            <div className="info-section">
              <strong>Outgoing connections:</strong>
              <ul>
                {graphData.edges
                  .filter(e => e.source === selectedNode)
                  .map(e => (
                    <li key={e.id}>
                      → {e.target}
                      <span className={`edge-type-badge ${e.type}`}>
                        {e.type === 'function' ? '<=' : '<-'}
                      </span>
                      {e.inferenceSequence}
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        )}
        {selectedEdge && (
          <div className="info-panel">
            <h4>Connection Details</h4>
            {(() => {
              const edge = graphData.edges.find(e => e.id === selectedEdge);
              if (!edge) return null;
              return (
                <>
                  <p><strong>From:</strong> {edge.source}</p>
                  <p><strong>To:</strong> {edge.target}</p>
                  <p><strong>Type:</strong> {edge.type === 'function' ? 'Function (<=)' : 'Value (<-)'}</p>
                  <p><strong>Inference:</strong> {edge.inferenceSequence}</p>
                </>
              );
            })()}
          </div>
        )}
        {!selectedNode && !selectedEdge && (
          <div className="info-panel info-hint">
            <p>Click on nodes or edges to see details</p>
            <div className="stats">
              <div className="stat">
                <strong>{graphData.nodes.length}</strong>
                <span>Concepts</span>
              </div>
              <div className="stat">
                <strong>{graphData.edges.length}</strong>
                <span>Connections</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FlowGraphView;

