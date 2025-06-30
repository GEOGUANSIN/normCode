import { createContext } from 'react';
import { Node, Edge } from 'reactflow';
import { NodeData, EdgeData } from '../types';

export interface NodeContextType {
  nodes: Node<NodeData>[];
  setNodes: React.Dispatch<React.SetStateAction<Node<NodeData>[]>>;
  setEdges: React.Dispatch<React.SetStateAction<Edge<EdgeData>[]>>;
}

export const NodeContext = createContext<NodeContextType | null>(null); 