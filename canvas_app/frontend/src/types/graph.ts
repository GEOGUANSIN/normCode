/**
 * Graph type definitions matching backend schemas
 */

export type NodeCategory = 'semantic-function' | 'semantic-value' | 'syntactic-function';
export type NodeType = 'value' | 'function';
export type EdgeType = 'function' | 'value' | 'context' | 'alias';

export interface GraphNode {
  id: string;
  label: string;
  category: NodeCategory;
  node_type: NodeType;
  flow_index: string | null;
  level: number;
  position: { x: number; y: number };
  data: {
    is_ground?: boolean;
    is_final?: boolean;
    is_context?: boolean;
    axes?: string[];
    sequence?: string;
    working_interpretation?: Record<string, unknown>;
    reference_data?: unknown;
    natural_name?: string;  // Human-readable name from concept repo
    concept_name?: string;  // Technical concept name
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: EdgeType;
  label: string | null;
  flow_index: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  category_counts: Record<string, number>;
  type_counts: Record<string, number>;
  ground_concepts: number;
  final_concepts: number;
  edge_type_counts: Record<string, number>;
}
