/**
 * Selection state management with Zustand
 */

import { create } from 'zustand';

interface SelectionState {
  // Selected items
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  hoveredNodeId: string | null;

  // Actions
  setSelectedNode: (nodeId: string | null) => void;
  setSelectedEdge: (edgeId: string | null) => void;
  setHoveredNode: (nodeId: string | null) => void;
  clearSelection: () => void;
}

export const useSelectionStore = create<SelectionState>((set) => ({
  selectedNodeId: null,
  selectedEdgeId: null,
  hoveredNodeId: null,

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId, selectedEdgeId: null }),
  setSelectedEdge: (edgeId) => set({ selectedEdgeId: edgeId, selectedNodeId: null }),
  setHoveredNode: (nodeId) => set({ hoveredNodeId: nodeId }),
  clearSelection: () => set({ selectedNodeId: null, selectedEdgeId: null }),
}));
