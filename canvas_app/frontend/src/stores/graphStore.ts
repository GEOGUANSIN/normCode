/**
 * Graph state management with Zustand
 * Includes collapse/expand and branch highlighting features
 */

import { create } from 'zustand';
import type { GraphData, GraphNode, GraphEdge } from '../types/graph';

type LayoutMode = 'hierarchical' | 'flow_aligned';

interface GraphState {
  // Data
  graphData: GraphData | null;
  isLoading: boolean;
  error: string | null;

  // Collapse/Expand state
  collapsedNodes: Set<string>; // Set of node IDs that are collapsed
  
  // Highlighting state
  highlightedBranch: Set<string>; // Set of node IDs in the highlighted branch

  // Layout state
  layoutMode: LayoutMode;

  // Actions
  setGraphData: (data: GraphData | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;

  // Collapse/Expand actions
  toggleCollapse: (nodeId: string) => void;
  collapseNode: (nodeId: string) => void;
  expandNode: (nodeId: string) => void;
  collapseAll: () => void;
  expandAll: () => void;
  collapseToLevel: (level: number) => void;

  // Highlight actions
  highlightBranch: (nodeId: string) => void;
  clearHighlight: () => void;

  // Layout actions
  setLayoutMode: (mode: LayoutMode) => Promise<void>;
  toggleLayoutMode: () => Promise<void>;

  // Helpers
  getNode: (id: string) => GraphNode | undefined;
  getEdgesForNode: (nodeId: string) => { incoming: GraphEdge[]; outgoing: GraphEdge[] };
  getDescendants: (nodeId: string) => Set<string>;
  getAncestors: (nodeId: string) => Set<string>;
  getBranch: (nodeId: string) => Set<string>; // Both ancestors and descendants
  getVisibleNodes: () => GraphNode[];
  getVisibleEdges: () => GraphEdge[];
  hasChildren: (nodeId: string) => boolean;
  isCollapsed: (nodeId: string) => boolean;
  isHidden: (nodeId: string) => boolean;
  isHighlighted: (nodeId: string) => boolean;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  graphData: null,
  isLoading: false,
  error: null,
  collapsedNodes: new Set<string>(),
  highlightedBranch: new Set<string>(),
  layoutMode: 'hierarchical',

  setGraphData: (data) => set({ 
    graphData: data, 
    error: null,
    collapsedNodes: new Set<string>(),
    highlightedBranch: new Set<string>(),
  }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ 
    graphData: null, 
    isLoading: false, 
    error: null,
    collapsedNodes: new Set<string>(),
    highlightedBranch: new Set<string>(),
    layoutMode: 'hierarchical',
  }),

  // Collapse/Expand actions
  toggleCollapse: (nodeId) => {
    const { collapsedNodes } = get();
    const newCollapsed = new Set(collapsedNodes);
    if (newCollapsed.has(nodeId)) {
      newCollapsed.delete(nodeId);
    } else {
      newCollapsed.add(nodeId);
    }
    set({ collapsedNodes: newCollapsed });
  },

  collapseNode: (nodeId) => {
    const { collapsedNodes } = get();
    const newCollapsed = new Set(collapsedNodes);
    newCollapsed.add(nodeId);
    set({ collapsedNodes: newCollapsed });
  },

  expandNode: (nodeId) => {
    const { collapsedNodes } = get();
    const newCollapsed = new Set(collapsedNodes);
    newCollapsed.delete(nodeId);
    set({ collapsedNodes: newCollapsed });
  },

  collapseAll: () => {
    const { graphData, hasChildren } = get();
    if (!graphData) return;
    const newCollapsed = new Set<string>();
    graphData.nodes.forEach((node) => {
      if (hasChildren(node.id)) {
        newCollapsed.add(node.id);
      }
    });
    set({ collapsedNodes: newCollapsed });
  },

  expandAll: () => {
    set({ collapsedNodes: new Set<string>() });
  },

  collapseToLevel: (level: number) => {
    const { graphData, hasChildren } = get();
    if (!graphData) return;
    const newCollapsed = new Set<string>();
    graphData.nodes.forEach((node) => {
      // Collapse nodes at or below the specified level that have children
      if (node.level >= level && hasChildren(node.id)) {
        newCollapsed.add(node.id);
      }
    });
    set({ collapsedNodes: newCollapsed });
  },

  // Highlight actions
  highlightBranch: (nodeId) => {
    const { getBranch } = get();
    const branch = getBranch(nodeId);
    branch.add(nodeId); // Include the selected node itself
    set({ highlightedBranch: branch });
  },

  clearHighlight: () => {
    set({ highlightedBranch: new Set<string>() });
  },

  // Layout actions
  setLayoutMode: async (mode) => {
    console.log('[GraphStore] setLayoutMode called with:', mode);
    const { graphData } = get();
    if (!graphData) {
      console.log('[GraphStore] No graphData, returning early');
      return;
    }

    console.log('[GraphStore] Setting isLoading=true, making API call...');
    set({ isLoading: true });
    try {
      const url = `/api/graph/layout/${mode}`;
      console.log('[GraphStore] Fetching:', url);
      const response = await fetch(url, { method: 'POST' });
      console.log('[GraphStore] Response status:', response.status, response.statusText);
      if (!response.ok) {
        throw new Error(`Failed to set layout mode: ${response.statusText}`);
      }
      const newGraphData = await response.json();
      console.log('[GraphStore] Got new graph data with', newGraphData.nodes?.length, 'nodes');
      set({ 
        graphData: newGraphData, 
        layoutMode: mode,
        isLoading: false,
      });
      console.log('[GraphStore] Layout mode changed to:', mode);
    } catch (error) {
      console.error('[GraphStore] Error changing layout:', error);
      set({ 
        error: error instanceof Error ? error.message : 'Failed to change layout',
        isLoading: false,
      });
    }
  },

  toggleLayoutMode: async () => {
    const { layoutMode, setLayoutMode } = get();
    const newMode = layoutMode === 'hierarchical' ? 'flow_aligned' : 'hierarchical';
    await setLayoutMode(newMode);
  },

  // Helpers
  getNode: (id) => {
    const { graphData } = get();
    return graphData?.nodes.find((n) => n.id === id);
  },

  getEdgesForNode: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return { incoming: [], outgoing: [] };

    return {
      incoming: graphData.edges.filter((e) => e.target === nodeId),
      outgoing: graphData.edges.filter((e) => e.source === nodeId),
    };
  },

  // Get all descendants (children, grandchildren, etc.) of a node
  getDescendants: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return new Set<string>();

    const descendants = new Set<string>();
    const queue = [nodeId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      // Find edges where this node is the target (children are sources)
      // In our graph, edges go from child → parent, so children are sources of edges targeting this node
      const childEdges = graphData.edges.filter((e) => e.target === currentId);
      
      for (const edge of childEdges) {
        if (!descendants.has(edge.source) && edge.source !== nodeId) {
          descendants.add(edge.source);
          queue.push(edge.source);
        }
      }
    }

    return descendants;
  },

  // Get all ancestors (parents, grandparents, etc.) of a node
  getAncestors: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return new Set<string>();

    const ancestors = new Set<string>();
    const queue = [nodeId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      // Find edges where this node is the source (parents are targets)
      const parentEdges = graphData.edges.filter((e) => e.source === currentId);
      
      for (const edge of parentEdges) {
        if (!ancestors.has(edge.target) && edge.target !== nodeId) {
          ancestors.add(edge.target);
          queue.push(edge.target);
        }
      }
    }

    return ancestors;
  },

  // Get entire branch (ancestors + descendants)
  getBranch: (nodeId) => {
    const { getAncestors, getDescendants } = get();
    const ancestors = getAncestors(nodeId);
    const descendants = getDescendants(nodeId);
    return new Set([...ancestors, ...descendants]);
  },

  // Get nodes that should be visible (not hidden by collapsed parents)
  getVisibleNodes: () => {
    const { graphData, collapsedNodes, getDescendants } = get();
    if (!graphData) return [];

    // Collect all hidden node IDs (descendants of collapsed nodes)
    const hiddenNodes = new Set<string>();
    collapsedNodes.forEach((collapsedId) => {
      const descendants = getDescendants(collapsedId);
      descendants.forEach((d) => hiddenNodes.add(d));
    });

    return graphData.nodes.filter((node) => !hiddenNodes.has(node.id));
  },

  // Get edges that should be visible
  getVisibleEdges: () => {
    const { graphData, getVisibleNodes } = get();
    if (!graphData) return [];

    const visibleNodeIds = new Set(getVisibleNodes().map((n) => n.id));
    
    return graphData.edges.filter(
      (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );
  },

  // Check if a node has children (is a parent of other nodes)
  hasChildren: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return false;
    // In our graph, edges go from child → parent
    // So a node has children if there are edges targeting it
    return graphData.edges.some((e) => e.target === nodeId && e.edge_type !== 'alias');
  },

  isCollapsed: (nodeId) => {
    const { collapsedNodes } = get();
    return collapsedNodes.has(nodeId);
  },

  isHidden: (nodeId) => {
    const { graphData, collapsedNodes, getDescendants } = get();
    if (!graphData) return false;

    // Check if this node is a descendant of any collapsed node
    for (const collapsedId of collapsedNodes) {
      const descendants = getDescendants(collapsedId);
      if (descendants.has(nodeId)) return true;
    }
    return false;
  },

  isHighlighted: (nodeId) => {
    const { highlightedBranch } = get();
    return highlightedBranch.size === 0 || highlightedBranch.has(nodeId);
  },
}));
