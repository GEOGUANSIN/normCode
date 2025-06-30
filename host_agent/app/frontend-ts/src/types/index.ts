export interface NodeData {
  label: string;
  type: string;
}

export interface EdgeData {
  styleType: 'solid' | 'dashed';
}

// Define Node type locally
export interface Node<T = any> {
  id: string;
  type?: string;
  position: { x: number; y: number };
  data: T;
  selected?: boolean;
  dragging?: boolean;
  positionAbsolute?: { x: number; y: number };
  width?: number;
  height?: number;
  zIndex?: number;
  hidden?: boolean;
  parentNode?: string;
  extent?: 'parent' | [number, number, number, number];
  expandParent?: boolean;
  focusable?: boolean;
  deletable?: boolean;
  dragHandle?: string;
  ariaLabel?: string;
  style?: React.CSSProperties;
  className?: string;
  targetPosition?: any;
  sourcePosition?: any;
}

// Define Edge type locally
export interface Edge<T = any> {
  id: string;
  source: string;
  target: string;
  type?: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  label?: string | React.ReactNode;
  labelStyle?: React.CSSProperties;
  labelShowBg?: boolean;
  labelBgStyle?: React.CSSProperties;
  labelBgPadding?: [number, number];
  labelBgBorderRadius?: number;
  style?: React.CSSProperties;
  animated?: boolean;
  hidden?: boolean;
  data?: T;
  className?: string;
  selected?: boolean;
  updatable?: boolean;
  deletable?: boolean;
  focusable?: boolean;
  ariaLabel?: string;
  zIndex?: number;
  interactionWidth?: number;
}

export interface CustomNode extends Node<NodeData> {
  type: string;
}

export interface CustomEdge extends Edge<EdgeData> {
  type: 'custom';
}

export interface NodeContextType {
  nodes: CustomNode[];
  setNodes: React.Dispatch<React.SetStateAction<CustomNode[]>>;
  setEdges: React.Dispatch<React.SetStateAction<CustomEdge[]>>;
}

export interface ControlPanelProps {
  newNodeType: string;
  setNewNodeType: (type: string) => void;
  newNodeLabel: string;
  setNewNodeLabel: (label: string) => void;
  addNewNode: () => void;
  saveGraph: () => Promise<void>;
  loadGraph: () => Promise<void>;
  hasUnsavedChanges: boolean;
  autoSave: boolean;
  setAutoSave: (autoSave: boolean) => void;
  edgeStyleType: 'solid' | 'dashed';
  setEdgeStyleType: (style: 'solid' | 'dashed') => void;
  isSaving: boolean;
}

export interface CustomNodeProps {
  data: NodeData;
  color: string;
  id: string;
}

export interface CustomEdgeProps {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition?: any;
  targetPosition?: any;
  style?: React.CSSProperties;
  markerEnd?: string;
  data?: EdgeData;
}

export type NodeType = 'red' | 'pink' | 'purple' | 'blue' | 'teal' | 'green' | 'yellow' | 'orange' | 'brown' | 'grey';

export interface EdgeStyleConfig {
  stroke: string;
  strokeWidth: number;
  strokeDasharray: string;
  transition: string;
}

// Define connection type locally since it's not exported from ReactFlow
export interface Connection {
  source: string | null;
  target: string | null;
  sourceHandle?: string | null;
  targetHandle?: string | null;
}

// Define edge change type locally
export interface EdgeChange {
  id: string;
  type: 'remove' | 'select' | 'unselect';
} 