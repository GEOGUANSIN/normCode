/**
 * Graph state management with Zustand
 * Includes collapse/expand and branch highlighting features
 * 
 * PERFORMANCE NOTES:
 * - Use useNodeGraphState() hook for node components to batch subscriptions
 * - Memoized selectors prevent unnecessary re-renders
 */

import { createWithEqualityFn } from 'zustand/traditional';
import { shallow } from 'zustand/shallow';
import { useCallback } from 'react';
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
  sameConceptNodes: Set<string>; // Set of node IDs with the same concept name as selected
  selectedConceptLabel: string | null; // The label of the currently selected concept

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
  getSameConceptNodeIds: (nodeId: string) => Set<string>; // Get all visible nodes with same label
  getConceptOccurrenceCount: (nodeId: string) => number; // Get count of visible nodes with same label
  hasChildren: (nodeId: string) => boolean;
  isCollapsed: (nodeId: string) => boolean;
  isHidden: (nodeId: string) => boolean;
  isHighlighted: (nodeId: string) => boolean;
  isSameConcept: (nodeId: string) => boolean; // Check if node has same concept as selected
  hasMultipleOccurrences: (nodeId: string) => boolean; // Check if concept has multiple visible occurrences
}

export const useGraphStore = createWithEqualityFn<GraphState>((set, get) => ({
  graphData: null,
  isLoading: false,
  error: null,
  collapsedNodes: new Set<string>(),
  highlightedBranch: new Set<string>(),
  sameConceptNodes: new Set<string>(),
  selectedConceptLabel: null,
  layoutMode: 'hierarchical',

  setGraphData: (data) => set({ 
    graphData: data, 
    error: null,
    collapsedNodes: new Set<string>(),
    highlightedBranch: new Set<string>(),
    sameConceptNodes: new Set<string>(),
    selectedConceptLabel: null,
  }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ 
    graphData: null, 
    isLoading: false, 
    error: null,
    collapsedNodes: new Set<string>(),
    highlightedBranch: new Set<string>(),
    sameConceptNodes: new Set<string>(),
    selectedConceptLabel: null,
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
    const { getBranch, getSameConceptNodeIds, getNode } = get();
    const branch = getBranch(nodeId);
    branch.add(nodeId); // Include the selected node itself
    
    // Also find all visible nodes with the same concept name
    const sameConceptNodes = getSameConceptNodeIds(nodeId);
    const node = getNode(nodeId);
    const selectedConceptLabel = node?.label || null;
    
    set({ 
      highlightedBranch: branch,
      sameConceptNodes,
      selectedConceptLabel,
    });
  },

  clearHighlight: () => {
    set({ 
      highlightedBranch: new Set<string>(),
      sameConceptNodes: new Set<string>(),
      selectedConceptLabel: null,
    });
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
  // IMPORTANT: Excludes alias edges to prevent cross-occurrence traversal
  getDescendants: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return new Set<string>();

    const descendants = new Set<string>();
    const queue = [nodeId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      // Find edges where this node is the target (children are sources)
      // In our graph, edges go from child → parent, so children are sources of edges targeting this node
      // EXCLUDE alias edges - they connect different occurrences of the same concept
      // and should not be traversed for collapse/expand operations
      const childEdges = graphData.edges.filter(
        (e) => e.target === currentId && e.edge_type !== 'alias'
      );
      
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
  // IMPORTANT: Excludes alias edges to prevent cross-occurrence traversal
  getAncestors: (nodeId) => {
    const { graphData } = get();
    if (!graphData) return new Set<string>();

    const ancestors = new Set<string>();
    const queue = [nodeId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      // Find edges where this node is the source (parents are targets)
      // EXCLUDE alias edges - they connect different occurrences of the same concept
      const parentEdges = graphData.edges.filter(
        (e) => e.source === currentId && e.edge_type !== 'alias'
      );
      
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

  // Get all visible node IDs that have the same label (concept name) as the given node
  getSameConceptNodeIds: (nodeId) => {
    const { getVisibleNodes, getNode } = get();
    const node = getNode(nodeId);
    if (!node) return new Set<string>();
    
    const conceptLabel = node.label;
    const visibleNodes = getVisibleNodes();
    
    // Find all visible nodes with the same label (including the original node)
    const sameConceptIds = new Set<string>();
    for (const n of visibleNodes) {
      if (n.label === conceptLabel) {
        sameConceptIds.add(n.id);
      }
    }
    
    return sameConceptIds;
  },

  // Get count of visible nodes with the same label as the given node
  getConceptOccurrenceCount: (nodeId) => {
    const { getSameConceptNodeIds } = get();
    return getSameConceptNodeIds(nodeId).size;
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

  // Check if a node has the same concept name as the currently selected node
  // Returns true only if there are multiple occurrences (more than 1 node with same label)
  isSameConcept: (nodeId) => {
    const { sameConceptNodes } = get();
    // Only highlight as "same concept" if there are multiple occurrences
    return sameConceptNodes.size > 1 && sameConceptNodes.has(nodeId);
  },

  // Check if a concept has multiple visible occurrences (for persistent badge display)
  hasMultipleOccurrences: (nodeId) => {
    const { getConceptOccurrenceCount } = get();
    return getConceptOccurrenceCount(nodeId) > 1;
  },
}));

/**
 * PERFORMANCE OPTIMIZED: Custom hook for node components
 * Batches all graph-related state for a single node into one subscription
 * Uses shallow comparison to prevent unnecessary re-renders
 */
export function useNodeGraphState(nodeId: string) {
  // Create a memoized selector that computes all node state at once
  const selector = useCallback((state: GraphState) => {
    const { 
      collapsedNodes, 
      highlightedBranch, 
      sameConceptNodes,
      graphData 
    } = state;
    
    // Check if node is collapsed
    const isCollapsed = collapsedNodes.has(nodeId);
    
    // Check if node has children (cached check)
    const hasChildren = graphData 
      ? graphData.edges.some((e) => e.target === nodeId && e.edge_type !== 'alias')
      : false;
    
    // Highlight state
    const hasHighlight = highlightedBranch.size > 0;
    const isHighlighted = !hasHighlight || highlightedBranch.has(nodeId);
    
    // Same concept state
    const isSameConcept = sameConceptNodes.size > 1 && sameConceptNodes.has(nodeId);
    
    // Multiple occurrences (need to compute from visible nodes)
    let occurrenceCount = 0;
    let hasMultipleOccurrences = false;
    if (graphData) {
      const node = graphData.nodes.find(n => n.id === nodeId);
      if (node) {
        const conceptLabel = node.label;
        // Count visible nodes with same label
        // Note: Using a simpler check here for performance
        for (const n of graphData.nodes) {
          if (n.label === conceptLabel) {
            occurrenceCount++;
            if (occurrenceCount > 1) {
              hasMultipleOccurrences = true;
              // Don't break - we need the full count for the badge
            }
          }
        }
      }
    }
    
    return {
      isCollapsed,
      hasChildren,
      isHighlighted,
      hasHighlight,
      isSameConcept,
      hasMultipleOccurrences,
      occurrenceCount,
    };
  }, [nodeId]);
  
  return useGraphStore(selector, shallow);
}
