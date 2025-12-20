/**
 * Main Graph Canvas component using React Flow
 * Supports collapse/expand and branch highlighting
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
  type NodeTypes,
  type EdgeTypes,
  BackgroundVariant,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  ChevronDown, 
  ChevronRight, 
  Maximize2, 
  Minimize2,
  Focus,
  X,
  Rows3,
  Network,
  PanelLeftClose,
  PanelLeft
} from 'lucide-react';

import { ValueNode } from './ValueNode';
import { FunctionNode } from './FunctionNode';
import { CustomEdge } from './CustomEdge';
import { useGraphStore } from '../../stores/graphStore';
import { useSelectionStore } from '../../stores/selectionStore';
import type { GraphNode as GraphNodeType, GraphEdge as GraphEdgeType } from '../../types/graph';

// Define custom node types
const nodeTypes: NodeTypes = {
  value: ValueNode,
  function: FunctionNode,
};

// Define custom edge types
const edgeTypes: EdgeTypes = {
  custom: CustomEdge,
};

// Transform backend graph data to React Flow format
function transformToReactFlowNodes(nodes: GraphNodeType[]): Node[] {
  return nodes.map((n) => ({
    id: n.id,
    type: n.node_type === 'value' ? 'value' : 'function',
    position: n.position,
    data: {
      label: n.label,
      category: n.category,
      flowIndex: n.flow_index,
      isGround: n.data.is_ground,
      isFinal: n.data.is_final,
      axes: n.data.axes,
      sequence: n.data.sequence,
      naturalName: n.data.natural_name,
    },
  }));
}

function transformToReactFlowEdges(edges: GraphEdgeType[]): Edge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'custom',
    data: {
      edgeType: e.edge_type,
      label: e.label,
    },
    animated: false,
  }));
}

// MiniMap node color function
function getMiniMapNodeColor(node: Node): string {
  const category = node.data?.category;
  switch (category) {
    case 'semantic-function':
      return '#c084fc'; // Purple
    case 'semantic-value':
      return '#60a5fa'; // Blue
    case 'syntactic-function':
      return '#94a3b8'; // Gray
    default:
      return '#94a3b8';
  }
}

export function GraphCanvas() {
  const [showControlsPanel, setShowControlsPanel] = useState(true);
  
  const graphData = useGraphStore((s) => s.graphData);
  const getVisibleNodes = useGraphStore((s) => s.getVisibleNodes);
  const getVisibleEdges = useGraphStore((s) => s.getVisibleEdges);
  const collapsedNodes = useGraphStore((s) => s.collapsedNodes);
  const collapseAll = useGraphStore((s) => s.collapseAll);
  const expandAll = useGraphStore((s) => s.expandAll);
  const collapseToLevel = useGraphStore((s) => s.collapseToLevel);
  const highlightBranch = useGraphStore((s) => s.highlightBranch);
  const clearHighlight = useGraphStore((s) => s.clearHighlight);
  const highlightedBranch = useGraphStore((s) => s.highlightedBranch);
  const sameConceptNodes = useGraphStore((s) => s.sameConceptNodes);
  const selectedConceptLabel = useGraphStore((s) => s.selectedConceptLabel);
  const layoutMode = useGraphStore((s) => s.layoutMode);
  const setLayoutMode = useGraphStore((s) => s.setLayoutMode);
  const isLoading = useGraphStore((s) => s.isLoading);
  
  const setSelectedNode = useSelectionStore((s) => s.setSelectedNode);
  const selectedNodeId = useSelectionStore((s) => s.selectedNodeId);

  // Get visible nodes and edges (filtered by collapse state)
  const visibleNodes = useMemo(() => getVisibleNodes(), [getVisibleNodes, collapsedNodes, graphData]);
  const visibleEdges = useMemo(() => getVisibleEdges(), [getVisibleEdges, collapsedNodes, graphData]);

  // Transform to React Flow format
  const flowNodes = useMemo(() => {
    return transformToReactFlowNodes(visibleNodes);
  }, [visibleNodes]);

  const flowEdges = useMemo(() => {
    return transformToReactFlowEdges(visibleEdges);
  }, [visibleEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  // Update nodes/edges when visible data changes
  useEffect(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  // Handle node selection with branch highlighting
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
      highlightBranch(node.id);
    },
    [setSelectedNode, highlightBranch]
  );

  // Handle pane click (deselect and clear highlight)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    clearHighlight();
  }, [setSelectedNode, clearHighlight]);

  // Calculate max level for collapse controls
  const maxLevel = useMemo(() => {
    if (!graphData) return 0;
    return Math.max(...graphData.nodes.map((n) => n.level));
  }, [graphData]);

  // Show empty state if no graph
  if (!graphData) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="text-center text-slate-500">
          <p className="text-lg font-medium">No graph loaded</p>
          <p className="text-sm mt-1">Load a repository to visualize the inference graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'custom',
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e2e8f0" gap={16} variant={BackgroundVariant.Dots} />
        <Controls className="bg-white rounded-lg shadow-md" />
        <MiniMap
          nodeColor={getMiniMapNodeColor}
          maskColor="rgba(0, 0, 0, 0.1)"
          className="bg-white rounded-lg shadow-md"
        />
        
        {/* Stats and Controls panel */}
        <Panel position="top-left" className="bg-white rounded-lg shadow-md text-xs" style={{ zIndex: 10 }}>
          {/* Header with toggle */}
          <div className="flex items-center justify-between p-2 border-b border-slate-100">
            <span className="text-slate-600 font-medium">
              {visibleNodes.length}/{graphData.nodes.length} nodes • {visibleEdges.length}/{graphData.edges.length} edges
            </span>
            <button
              onClick={() => setShowControlsPanel(!showControlsPanel)}
              className="p-1 hover:bg-slate-100 rounded transition-colors text-slate-500"
              title={showControlsPanel ? 'Collapse controls' : 'Expand controls'}
            >
              {showControlsPanel ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
            </button>
          </div>
          
          {/* Collapsible content */}
          {showControlsPanel && (
            <div className="p-2 space-y-2">
              {/* Layout mode toggle - two buttons */}
              <div className="flex gap-1 items-center">
                <span className="text-slate-500">Layout:</span>
                <div className="flex rounded overflow-hidden border border-slate-200">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('[GraphCanvas] Compact button clicked, current mode:', layoutMode, 'isLoading:', isLoading);
                      setLayoutMode('hierarchical');
                    }}
                    disabled={isLoading || layoutMode === 'hierarchical'}
                    className={`flex items-center gap-1 px-2 py-1 transition-colors ${
                      layoutMode === 'hierarchical' 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-white text-slate-600 hover:bg-slate-100'
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title="Compact layout - nodes grouped by level"
                  >
                    <Network className="w-3 h-3" />
                    <span>Compact</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('[GraphCanvas] Flow Aligned button clicked, current mode:', layoutMode, 'isLoading:', isLoading);
                      setLayoutMode('flow_aligned');
                    }}
                    disabled={isLoading || layoutMode === 'flow_aligned'}
                    className={`flex items-center gap-1 px-2 py-1 transition-colors ${
                      layoutMode === 'flow_aligned' 
                        ? 'bg-purple-500 text-white' 
                        : 'bg-white text-slate-600 hover:bg-slate-100'
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title="Flow-aligned layout - one concept per row based on flow index"
                  >
                    <Rows3 className="w-3 h-3" />
                    <span>Flow Aligned</span>
                  </button>
                </div>
              </div>
              
              {/* Collapse/Expand controls */}
              <div className="flex gap-1 flex-wrap">
                <button
                  onClick={expandAll}
                  className="flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700 transition-colors"
                  title="Expand all nodes"
                >
                  <Maximize2 className="w-3 h-3" />
                  <span>Expand All</span>
                </button>
                <button
                  onClick={collapseAll}
                  className="flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700 transition-colors"
                  title="Collapse all nodes"
                >
                  <Minimize2 className="w-3 h-3" />
                  <span>Collapse All</span>
                </button>
              </div>
              
              {/* Collapse to level controls */}
              <div className="flex gap-1 items-center">
                <span className="text-slate-500">Collapse to level:</span>
                {Array.from({ length: Math.min(maxLevel + 1, 5) }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => collapseToLevel(i)}
                    className="w-6 h-6 flex items-center justify-center bg-slate-100 hover:bg-slate-200 rounded text-slate-700 transition-colors"
                    title={`Collapse nodes at level ${i} and deeper`}
                  >
                    {i}
                  </button>
                ))}
              </div>
              
              {/* Collapsed count indicator */}
              {collapsedNodes.size > 0 && (
                <div className="text-slate-500">
                  <span className="font-medium">{collapsedNodes.size}</span> nodes collapsed
                </div>
              )}
            </div>
          )}
        </Panel>
        
        {/* Highlight indicator panel */}
        {highlightedBranch.size > 0 && (
          <Panel position="top-right" className="bg-white rounded-lg shadow-md p-2 text-xs">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Focus className="w-3 h-3 text-indigo-500" />
                <span className="text-slate-600">
                  Highlighting <span className="font-medium">{highlightedBranch.size + 1}</span> nodes in branch
                </span>
                <button
                  onClick={clearHighlight}
                  className="p-1 hover:bg-slate-100 rounded transition-colors"
                  title="Clear highlight"
                >
                  <X className="w-3 h-3 text-slate-500" />
                </button>
              </div>
              {/* Same concept indicator */}
              {sameConceptNodes.size > 1 && (
                <div className="flex items-center gap-2 text-amber-600 border-t border-slate-100 pt-1 mt-1">
                  <span className="w-3 h-3 bg-amber-500 text-white rounded-full text-[8px] flex items-center justify-center font-bold">≡</span>
                  <span>
                    <span className="font-medium">{sameConceptNodes.size}</span> occurrences of same concept
                  </span>
                </div>
              )}
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
}
