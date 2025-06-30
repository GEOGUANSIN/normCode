import React, { useCallback, useState, useEffect, useRef } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  EdgeChange as ReactFlowEdgeChange,
  Connection as ReactFlowConnection,
  PanOnScrollMode,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import styled, { createGlobalStyle } from 'styled-components';
import { NodeContext } from './context/NodeContext';
import { API_BASE_URL, nodeColors } from './config';
import { calculateHierarchicalLayout } from './utils/layout';
import CustomNode from './components/nodes/CustomNode';
import CustomEdge from './components/edges/CustomEdge';
import ControlPanel from './components/ControlPanel';
import { NodeData, EdgeData, NodeType, EdgeStyleConfig } from './types';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: #f5f6fa;
  }

  .react-flow__node {
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    text-align: center;
    border: none;
    padding: 0;
    width: auto;
    background: transparent;
  }

  .react-flow__handle {
    width: 24px;
    height: 24px;
    background: #34495e;
    border: 2px solid #2c3e50;
    border-radius: 50%;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .react-flow__handle:hover {
    background: #2c3e50;
    box-shadow: 0 0 8px rgba(44, 62, 80, 0.3);
  }

  .react-flow__controls {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    overflow: hidden;
  }

  .react-flow__controls-button {
    border: none;
    background: white;
    padding: 8px;
    transition: all 0.3s ease;
  }

  .react-flow__controls-button:hover {
    background: #f5f6fa;
  }

  .react-flow__minimap {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
`;

const Container = styled.div`
  width: 100vw;
  height: 100vh;
  background: #f5f6fa;
`;

const VALID_NODE_TYPES: NodeType[] = ['red', 'pink', 'purple', 'blue', 'teal', 'green', 'yellow', 'orange', 'brown', 'grey'];

// Create a stable reference for node types
const createNodeType = (type: NodeType, color: string) => {
  const NodeComponent = React.memo((props: any) => {
    const memoizedProps = React.useMemo(() => ({
      ...props,
      color
    }), [props]);
    return <CustomNode {...memoizedProps} />;
  });
  NodeComponent.displayName = `NodeType-${type}`;
  return NodeComponent;
};

// Create node types outside component with stable references
const nodeTypes = Object.freeze(
  Object.fromEntries(
    VALID_NODE_TYPES.map((type, index) => [
      type,
      createNodeType(type, nodeColors[type])
    ])
  )
);

// Create edge types outside component with stable reference
const CustomEdgeMemo = React.memo(CustomEdge);
CustomEdgeMemo.displayName = 'CustomEdge';

const edgeTypes = Object.freeze({
  custom: CustomEdgeMemo
});

// Helper function to convert numeric type to string type - moved outside component
const getNodeTypeString = (type: string | number): NodeType => {
  // If type is already a valid string type, return it
  if (VALID_NODE_TYPES.includes(type as NodeType)) {
    return type as NodeType;
  }

  // Handle numeric types
  const typeValue = typeof type === 'string' ? parseInt(type, 10) : type;
  const typeMap: Record<number, NodeType> = {
    0: 'red',
    1: 'pink',
    2: 'purple',
    3: 'blue',
    4: 'teal',
    5: 'green',
    6: 'yellow',
    7: 'orange',
    8: 'brown',
    9: 'grey'
  };
  
  // If type is invalid, default to 'red'
  if (typeValue < 0 || typeValue > 9 || isNaN(typeValue)) {
    console.warn(`Invalid node type: ${type}. Defaulting to 'red'`);
    return 'red';
  }
  
  return typeMap[typeValue] || 'red';
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<EdgeData>([]);
  const [newNodeType, setNewNodeType] = useState<NodeType>('red');
  const [newNodeLabel, setNewNodeLabel] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [autoSave, setAutoSave] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Edge style configurations
  const edgeStyles: Record<'solid' | 'dashed', EdgeStyleConfig> = React.useMemo(() => ({
    solid: {
      stroke: '#34495e',
      strokeWidth: 10,
      strokeDasharray: 'none',
      transition: 'all 0.3s ease'
    },
    dashed: {
      stroke: '#34495e',
      strokeWidth: 10,
      strokeDasharray: '10,5',
      transition: 'all 0.3s ease'
    }
  }), []);

  const [edgeStyleType, setEdgeStyleType] = useState<'solid' | 'dashed'>('solid');

  // Add a ref to track if changes are from a save operation
  const isFromSave = useRef(false);

  const saveGraph = useCallback(async () => {
    try {
      console.log('Starting save operation...');
      setError(null);
      setIsSaving(true);
      isFromSave.current = true;  // Mark that changes are from save
      
      const response = await fetch(`${API_BASE_URL}/save`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save graph');
      }
      
      const data = await response.json();
      console.log('Save response:', data);
      
      if (data.message === 'Graph saved successfully') {
        console.log('Save successful, fetching updated state...');
        const [nodesResponse, edgesResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/nodes`),
          fetch(`${API_BASE_URL}/edges`)
        ]);
        
        if (!nodesResponse.ok || !edgesResponse.ok) {
          throw new Error('Failed to fetch updated state');
        }
        
        const nodesData = await nodesResponse.json();
        const edgesData = await edgesResponse.json();
        console.log('Fetched updated state:', { nodes: nodesData.length, edges: edgesData.length });
        
        const nodesWithTypes = nodesData.map((node: any) => ({
          ...node,
          type: getNodeTypeString(node.type),
          data: {
            ...node.data,
            type: getNodeTypeString(node.type)
          }
        }));
        const nodesWithPositions = calculateHierarchicalLayout(nodesWithTypes, edgesData);

        // Update nodes and edges in a single batch
        setNodes(nodesWithPositions);
        setEdges(edgesData);
        
        // Set hasUnsavedChanges to false only after loading is complete
        setHasUnsavedChanges(false);
        
        if (!autoSave) {
          alert('Graph saved and loaded successfully!');
        }
      } else {
        throw new Error('Failed to save graph');
      }
    } catch (error) {
      console.error('Error saving graph:', error);
      setError('Failed to save graph. Please try again.');
      setHasUnsavedChanges(true);  // Restore unsaved changes state on error
    } finally {
      // Use a small delay to ensure all state updates are complete
      setTimeout(() => {
        setIsSaving(false);
        isFromSave.current = false;  // Reset the save flag
      }, 100);
    }
  }, [setNodes, setEdges, setError, setHasUnsavedChanges, autoSave]);

  const handleEdgesChange = useCallback(async (changes: ReactFlowEdgeChange[]) => {
    // Handle edge deletions
    const deletedEdges = changes.filter(change => change.type === 'remove');
    if (deletedEdges.length > 0) {
      for (const change of deletedEdges) {
        try {
          await fetch(`${API_BASE_URL}/edges/${change.id}`, {
            method: 'DELETE',
          });
        } catch (error) {
          console.error(`Error deleting edge ${change.id}:`, error);
        }
      }
      // Trigger auto-save after edge deletion
      if (autoSave) {
        saveGraph();
      }
    }
    onEdgesChange(changes);
  }, [onEdgesChange, autoSave, saveGraph]);

  const onConnect = useCallback(
    async (params: ReactFlowConnection) => {
      try {
        const sourceNode = nodes.find(n => n.id === params.source);
        const targetNode = nodes.find(n => n.id === params.target);
        
        if (!sourceNode || !targetNode) {
          throw new Error('Source or target node does not exist');
        }

        const newEdge: Edge<EdgeData> = {
          id: `e${params.source}-${params.target}`,
          source: params.source!,
          target: params.target!,
          type: 'custom',
          style: {
            strokeDasharray: edgeStyleType === 'dashed' ? '10,5' : 'none',
          },
          data: { styleType: edgeStyleType }
        };
        
        const response = await fetch(`${API_BASE_URL}/edges`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newEdge),
        });
        
        if (response.ok) {
          setEdges((eds) => addEdge(newEdge, eds));
          // Trigger auto-save after edge addition
          if (autoSave) {
            saveGraph();
          }
        } else {
          const responseData = await response.json();
          if (responseData.detail === "Edge already exists") {
            const sourceLabel = sourceNode.data?.label;
            const targetLabel = targetNode.data?.label;
            alert(`A connection already exists between "${sourceLabel}" and "${targetLabel}"`);
          } else {
            throw new Error(responseData.detail || 'Failed to create edge');
          }
        }
      } catch (error) {
        console.error('Error creating edge:', error);
        alert(`Failed to create edge: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    },
    [nodes, setEdges, autoSave, saveGraph, edgeStyleType]
  );

  const onKeyDown = useCallback(async (event: React.KeyboardEvent) => {
    if (event.key === 'Delete') {
      const selectedNodes = nodes.filter((node) => node.selected);
      
      for (const node of selectedNodes) {
        try {
          await fetch(`${API_BASE_URL}/nodes/${node.id}`, {
            method: 'DELETE',
          });
        } catch (error) {
          console.error(`Error deleting node ${node.id}:`, error);
        }
      }
      
      setNodes((nds) => nds.filter((node) => !node.selected));
      setEdges((eds) => eds.filter(
        (edge) => !selectedNodes.some(node => node.id === edge.source || node.id === edge.target)
      ));

      // Trigger auto-save after deletion
      if (autoSave) {
        saveGraph();
      }
    }
  }, [nodes, setNodes, setEdges, autoSave, saveGraph]);

  // Update hasUnsavedChanges when nodes or edges change
  useEffect(() => {
    console.log('Nodes or edges changed:', { 
      isLoading, 
      autoSave, 
      isSaving,
      isFromSave: isFromSave.current,
      nodesCount: nodes.length, 
      edgesCount: edges.length 
    });
    
    // Only set hasUnsavedChanges to true if:
    // 1. Not loading initial data
    // 2. Not in auto-save mode
    // 3. Not already marked as unsaved
    // 4. Not currently saving
    // 5. Changes are not from a save operation
    if (!isLoading && !autoSave && !hasUnsavedChanges && !isSaving && !isFromSave.current) {
      console.log('Setting hasUnsavedChanges to true');
      setHasUnsavedChanges(true);
    }
  }, [nodes, edges, isLoading, autoSave, hasUnsavedChanges, isSaving]);

  // Add effect to handle node changes and auto-save
  useEffect(() => {
    if (autoSave && hasUnsavedChanges) {
      console.log('Auto-save triggered');
      const saveTimeout = setTimeout(() => {
        saveGraph();
      }, 1000); // Debounce for 1 second

      return () => clearTimeout(saveTimeout);
    }
  }, [nodes, edges, autoSave, hasUnsavedChanges, saveGraph]);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [nodesResponse, edgesResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/nodes`),
          fetch(`${API_BASE_URL}/edges`)
        ]);
        
        if (!nodesResponse.ok || !edgesResponse.ok) {
          throw new Error('Failed to fetch data');
        }
        
        const nodesData = await nodesResponse.json();
        const edgesData = await edgesResponse.json();
        
        // Ensure each node has the correct type string
        const nodesWithTypes = nodesData.map((node: any) => {
          // Convert the type to string format and validate
          const typeString = getNodeTypeString(node.type || node.data?.type);
          return {
            ...node,
            type: typeString,
            data: {
              ...node.data,
              type: typeString
            }
          };
        });
        
        // Apply hierarchical layout to initial nodes
        const nodesWithPositions = calculateHierarchicalLayout(nodesWithTypes, edgesData);
        setNodes(nodesWithPositions);
        
        const processedEdges = edgesData.map((edge: any) => ({
          ...edge,
          type: 'custom',
          style: edgeStyles[(edge.data?.styleType || 'solid') as 'solid' | 'dashed'],
          data: { 
            ...edge.data,
            styleType: (edge.data?.styleType || 'solid') as 'solid' | 'dashed'
          }
        }));
        
        setEdges(processedEdges);
        setHasUnsavedChanges(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to load graph data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [setNodes, setEdges, edgeStyles]);

  const addNewNode = async () => {
    if (!newNodeLabel.trim()) return;

    // Find the highest existing ID and increment it
    const highestId = nodes.reduce((max, node) => {
      const currentId = parseInt(node.id);
      return isNaN(currentId) ? max : Math.max(max, currentId);
    }, 0);
    const newNodeId = (highestId + 1).toString();
    
    const validatedType = getNodeTypeString(newNodeType);
    const newNode: Node<NodeData> = {
      id: newNodeId,
      type: validatedType,
      data: { 
        label: newNodeLabel,
        type: validatedType
      },
      position: { x: 0, y: 0 },
    };

    console.log("Sending new node:", newNode);
    try {
      const response = await fetch(`${API_BASE_URL}/nodes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newNode),
      });
      
      if (response.ok) {
        const createdNode = await response.json();
        // Ensure the type is a valid string
        const typeString = getNodeTypeString(createdNode.type);
        const nodeWithType = {
          ...createdNode,
          type: typeString,
          data: {
            ...createdNode.data,
            type: typeString
          }
        };
        // Add the new node to the existing nodes
        const updatedNodes = [...nodes, nodeWithType];
        // Recalculate layout for all nodes including the new one
        const nodesWithPositions = calculateHierarchicalLayout(updatedNodes, edges);
        setNodes(nodesWithPositions);
        setNewNodeLabel('');
      } else {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        alert(`Failed to create node: ${errorData.detail?.[0]?.msg || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating node:', error);
      alert('Failed to create node. Please try again.');
    }
  };

  const loadGraph = async () => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load graph');
      }
      
      const data = await response.json();
      console.log('Load response:', data);
      
      // Process the loaded data
      const nodesWithTypes = data.nodes.map((node: any) => ({
        ...node,
        type: getNodeTypeString(node.type),
        data: {
          ...node.data,
          type: getNodeTypeString(node.type)
        }
      }));
      const nodesWithPositions = calculateHierarchicalLayout(nodesWithTypes, data.edges);
      setNodes(nodesWithPositions);
      setEdges(data.edges);
      setHasUnsavedChanges(false);
      alert('Graph loaded successfully!');
    } catch (error) {
      console.error('Error loading graph:', error);
      setError('Failed to load graph. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Add this useEffect near the other useEffect hooks
  useEffect(() => {
    const handleResizeObserverError = (e: ErrorEvent) => {
      if (e.message === 'ResizeObserver loop completed with undelivered notifications.') {
        e.stopPropagation();
        e.preventDefault();
      }
    };

    window.addEventListener('error', handleResizeObserverError);
    return () => {
      window.removeEventListener('error', handleResizeObserverError);
    };
  }, []);

  if (isLoading) {
    return (
      <Container>
        <div style={{ 
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          fontSize: '18px',
          color: '#2c3e50',
          fontWeight: 600
        }}>
          Loading...
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <div style={{ 
          color: '#e74c3c', 
          textAlign: 'center',
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          padding: '24px'
        }}>
          <p style={{ marginBottom: '16px', fontSize: '16px' }}>{error}</p>
          <button 
            onClick={loadGraph}
            style={{
              background: '#3498db',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
              transition: 'all 0.3s ease'
            }}
          >
            Retry
          </button>
        </div>
      </Container>
    );
  }

  return (
    <NodeContext.Provider value={{ nodes, setNodes, setEdges }}>
      <GlobalStyle />
      <Container onKeyDown={onKeyDown} tabIndex={0}>
        <svg style={{ position: 'absolute', width: 0, height: 0 }}>
          <defs>
            <marker
              id="arrowhead"
              markerWidth="15"
              markerHeight="12"
              refX="12"
              refY="6"
              orient="auto"
              markerUnits="userSpaceOnUse"
            >
              <polygon
                points="0 0, 15 6, 0 12"
                fill="#34495e"
              />
            </marker>
          </defs>
        </svg>
        <ControlPanel
          newNodeType={newNodeType}
          setNewNodeType={setNewNodeType}
          newNodeLabel={newNodeLabel}
          setNewNodeLabel={setNewNodeLabel}
          addNewNode={addNewNode}
          saveGraph={saveGraph}
          loadGraph={loadGraph}
          autoSave={autoSave}
          setAutoSave={setAutoSave}
          edgeStyleType={edgeStyleType}
          setEdgeStyleType={setEdgeStyleType}
          hasUnsavedChanges={hasUnsavedChanges}
          isSaving={isSaving}
        />
        <div style={{ width: '100%', height: '100%' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            defaultEdgeOptions={{
              type: 'custom',
              style: edgeStyles[edgeStyleType],
              markerEnd: "url(#arrowhead)",
              data: { styleType: edgeStyleType }
            }}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            style={{ background: '#f5f6fa' }}
            elementsSelectable={true}
            nodesConnectable={true}
            nodesDraggable={true}
            zoomOnScroll={true}
            panOnScroll={true}
            panOnScrollMode={PanOnScrollMode.Vertical}
            zoomOnDoubleClick={true}
            minZoom={0.1}
            maxZoom={4}
            defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          >
            <Controls />
            <MiniMap 
              nodeColor={(n: any) => {
                const type = n.type || n.data?.type;
                const typeIndex = Object.keys(nodeTypes).indexOf(type);
                return typeIndex >= 0 ? nodeColors[VALID_NODE_TYPES[typeIndex]] : '#95a5a6';
              }}
              style={{ background: 'white' }}
            />
            <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#e0e0e0" />
          </ReactFlow>
        </div>
      </Container>
    </NodeContext.Provider>
  );
}

export default App; 