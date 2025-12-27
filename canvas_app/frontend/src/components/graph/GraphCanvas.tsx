/**
 * Main Graph Canvas component using React Flow
 * Supports collapse/expand and branch highlighting
 * 
 * PERFORMANCE OPTIMIZED:
 * - Uses shallow comparison for store subscriptions
 * - Memoized node/edge transformations
 * - Batched store selectors
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
  useReactFlow,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  Maximize2, 
  Minimize2,
  Focus,
  X,
  Rows3,
  Network,
  PanelLeftClose,
  PanelLeft,
  Map,
} from 'lucide-react';
import { shallow } from 'zustand/shallow';

import { ValueNode } from './ValueNode';
import { FunctionNode } from './FunctionNode';
import { CustomEdge } from './CustomEdge';
import { useGraphStore } from '../../stores/graphStore';
import { useSelectionStore } from '../../stores/selectionStore';
import { useCanvasCommandStore } from '../../stores/canvasCommandStore';
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

// Inner component that uses useReactFlow (must be inside ReactFlowProvider)
function GraphCanvasInner() {
  const [showControlsPanel, setShowControlsPanel] = useState(true);
  const [showMinimap, setShowMinimap] = useState(true);
  const { setCenter, getViewport, zoomIn, zoomOut, fitView } = useReactFlow();
  
  // Canvas command store for handling backend-driven canvas operations
  const { pendingCommands, popCommand } = useCanvasCommandStore();
  
  // Process pending canvas commands
  useEffect(() => {
    if (pendingCommands.length === 0) return;
    
    const command = popCommand();
    if (!command) return;
    
    console.log('[GraphCanvas] Executing command:', command);
    
    switch (command.type) {
      case 'zoom_in':
        zoomIn({ duration: 300 });
        break;
      case 'zoom_out':
        zoomOut({ duration: 300 });
        break;
      case 'fit_view':
        fitView({ padding: 0.2, duration: 300 });
        break;
      case 'center_on':
        const { x, y, zoom } = command.params as { x?: number; y?: number; zoom?: number };
        if (x !== undefined && y !== undefined) {
          setCenter(x, y, { zoom: zoom ?? getViewport().zoom, duration: 300 });
        }
        break;
      default:
        console.log('[GraphCanvas] Unknown command type:', command.type);
    }
  }, [pendingCommands, popCommand, zoomIn, zoomOut, fitView, setCenter, getViewport]);
  
  // OPTIMIZED: Batch related state into single subscriptions with shallow comparison
  const { graphData, collapsedNodes, layoutMode, isLoading } = useGraphStore(
    (s) => ({
      graphData: s.graphData,
      collapsedNodes: s.collapsedNodes,
      layoutMode: s.layoutMode,
      isLoading: s.isLoading,
    }),
    shallow
  );
  
  // Separate subscription for highlight state (changes frequently)
  const { highlightedBranch, sameConceptNodes } = useGraphStore(
    (s) => ({
      highlightedBranch: s.highlightedBranch,
      sameConceptNodes: s.sameConceptNodes,
    }),
    shallow
  );
  
  // Actions (these don't cause re-renders, just grab the function references once)
  const storeActions = useGraphStore(
    (s) => ({
      getVisibleNodes: s.getVisibleNodes,
      getVisibleEdges: s.getVisibleEdges,
      collapseAll: s.collapseAll,
      expandAll: s.expandAll,
      collapseToLevel: s.collapseToLevel,
      highlightBranch: s.highlightBranch,
      clearHighlight: s.clearHighlight,
      setLayoutMode: s.setLayoutMode,
    }),
    shallow
  );
  
  const setSelectedNode = useSelectionStore((s) => s.setSelectedNode);

  // OPTIMIZED: Compute visible nodes/edges with proper dependencies
  // The key insight is that we need graphData and collapsedNodes, but not the function itself
  const visibleNodes = useMemo(() => {
    if (!graphData) return [];
    return storeActions.getVisibleNodes();
  }, [graphData, collapsedNodes, storeActions]);
  
  const visibleEdges = useMemo(() => {
    if (!graphData) return [];
    return storeActions.getVisibleEdges();
  }, [graphData, collapsedNodes, storeActions]);

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
      storeActions.highlightBranch(node.id);
    },
    [setSelectedNode, storeActions]
  );

  // Handle pane click (deselect and clear highlight)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    storeActions.clearHighlight();
  }, [setSelectedNode, storeActions]);

  // Calculate max level for collapse controls
  const maxLevel = useMemo(() => {
    if (!graphData) return 0;
    return Math.max(...graphData.nodes.map((n) => n.level));
  }, [graphData]);

  // Handle minimap click to teleport view
  const handleMinimapClick = useCallback(
    (event: React.MouseEvent, position: { x: number; y: number }) => {
      // setCenter moves the viewport to center on the clicked position
      const { zoom } = getViewport();
      setCenter(position.x, position.y, { zoom, duration: 300 });
    },
    [setCenter, getViewport]
  );

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
        // PERFORMANCE: Disable node extent during drag for smoother performance
        nodesDraggable={false}
        // PERFORMANCE: Don't re-calculate on every change
        elementsSelectable={true}
        // PERFORMANCE: Reduce event overhead
        panOnDrag={true}
        zoomOnScroll={true}
        zoomOnPinch={true}
        // PERFORMANCE: Disable selection box
        selectionOnDrag={false}
      >
        <Background color="#e2e8f0" gap={16} variant={BackgroundVariant.Dots} />
        <Controls className="bg-white rounded-lg shadow-md" />
        
        {/* Minimap with click-to-teleport and integrated toggle */}
        <Panel position="bottom-right" className="!p-0">
          {showMinimap ? (
            <div className="relative bg-white rounded-lg shadow-md">
              <MiniMap
                nodeColor={getMiniMapNodeColor}
                maskColor="rgba(0, 0, 0, 0.1)"
                className="!relative !m-0 cursor-crosshair"
                pannable={true}
                zoomable={false}
                onClick={handleMinimapClick}
                style={{ position: 'relative', margin: 0 }}
              />
              {/* Close button overlaid on minimap corner */}
              <button
                onClick={() => setShowMinimap(false)}
                className="absolute top-1.5 right-1.5 p-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-700 border border-slate-200 shadow z-10 transition-colors"
                title="Hide minimap"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowMinimap(true)}
              className="p-2 rounded-lg shadow-md bg-white text-slate-600 hover:bg-slate-100"
              title="Show minimap"
            >
              <Map className="w-4 h-4" />
            </button>
          )}
        </Panel>
        
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
                      storeActions.setLayoutMode('hierarchical');
                    }}
                    disabled={isLoading || layoutMode === 'hierarchical'}
                    className={`flex items-center gap-1 px-2 py-1 ${
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
                      storeActions.setLayoutMode('flow_aligned');
                    }}
                    disabled={isLoading || layoutMode === 'flow_aligned'}
                    className={`flex items-center gap-1 px-2 py-1 ${
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
                  onClick={storeActions.expandAll}
                  className="flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
                  title="Expand all nodes"
                >
                  <Maximize2 className="w-3 h-3" />
                  <span>Expand All</span>
                </button>
                <button
                  onClick={storeActions.collapseAll}
                  className="flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
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
                    onClick={() => storeActions.collapseToLevel(i)}
                    className="w-6 h-6 flex items-center justify-center bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
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
                  onClick={storeActions.clearHighlight}
                  className="p-1 hover:bg-slate-100 rounded"
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

// Wrapper component that provides ReactFlowProvider for useReactFlow hook
export function GraphCanvas() {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner />
    </ReactFlowProvider>
  );
}
