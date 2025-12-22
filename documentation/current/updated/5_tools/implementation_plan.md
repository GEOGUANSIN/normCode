# Canvas App Implementation Plan

**Remaining work and roadmap for the NormCode Graph Canvas App.**

---

## Current Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| **Phase 1**: Foundation (Graph Display) | ✅ Complete | 100% |
| **Phase 2**: Execution Integration | ✅ Complete | 100% |
| **Phase 3**: Debugging Features | ✅ Complete | 100% |
| **Phase 4**: Modification & Re-run | ✅ Complete | 100% |
| **Phase 5**: Polish & Advanced | ❌ Not Started | 0% |

### What's Complete

- ✅ Graph visualization with React Flow
- ✅ Real-time WebSocket execution events
- ✅ Breakpoints and step execution
- ✅ TensorInspector for N-D data viewing
- ✅ Log panel with per-node filtering
- ✅ Project management system (multi-project, registry)
- ✅ Editor panel with file browser
- ✅ Agent panel with tool monitoring
- ✅ "Run to" feature
- ✅ Fullscreen detail panel
- ✅ Natural name display
- ✅ Value override capability
- ✅ Function modification dialog
- ✅ Selective re-run from any node
- ✅ Checkpoint resume/fork

### What's Remaining

- ❌ Run comparison/diff view
- ❌ Keyboard shortcuts
- ❌ Export/import functionality
- ❌ Performance optimization for 500+ nodes
- ❌ Watch expressions
- ❌ Node search

---

## Phase 4: Modification & Re-run (Remaining)

**Goal**: Enable interactive modification and retry of plan execution.

### 4.1 Value Override Dialog

**Priority**: HIGH  
**Estimated Effort**: 2-3 days

Allow users to inject or modify values at any ground or computed node.

#### Requirements

1. **Override Dialog UI**
   - Modal for editing tensor values
   - Support scalar, 1D, 2D editing
   - JSON editor for complex structures
   - Validation before apply

2. **Backend Support**
   - `POST /api/execution/override/{concept_name}` endpoint
   - Update concept reference in orchestrator
   - Mark dependent nodes as stale
   - Optionally trigger re-run

3. **Visual Feedback**
   - Overridden nodes show special badge
   - "Modified" indicator in detail panel
   - Stale descendants highlighted

#### Implementation

**Backend** (`execution_service.py`):
```python
async def override_value(
    self,
    concept_name: str,
    new_value: Any,
    rerun_dependents: bool = False
) -> Dict[str, Any]:
    """Override a concept's reference value."""
    # Get concept from repo
    concept = self.concept_repo.get(concept_name)
    
    # Update reference
    concept.reference = Reference(new_value, axis_names=concept.reference.axis_names)
    
    # Find dependent inferences
    dependents = self._find_dependents(concept_name)
    
    # Mark dependents as stale
    for flow_index in dependents:
        self.node_statuses[flow_index] = 'pending'
    
    if rerun_dependents:
        await self.start()
    
    return {
        "success": True,
        "overridden": concept_name,
        "stale_nodes": dependents
    }
```

**Frontend** (`ValueOverrideModal.tsx`):
```tsx
interface ValueOverrideModalProps {
  conceptName: string;
  currentValue: any;
  axes: string[];
  onApply: (newValue: any, rerun: boolean) => void;
  onClose: () => void;
}

export function ValueOverrideModal({ ... }: ValueOverrideModalProps) {
  // Scalar editor for 0D
  // Table editor for 1D/2D
  // JSON editor for complex structures
  // Apply/Cancel buttons
  // "Re-run dependents" checkbox
}
```

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 4.1.1 | Create `ValueOverrideModal` component | `panels/ValueOverrideModal.tsx` | 4h |
| 4.1.2 | Add scalar/array editor components | `panels/ValueEditor.tsx` | 3h |
| 4.1.3 | Add `override_value()` to ExecutionController | `execution_service.py` | 2h |
| 4.1.4 | Add `POST /execution/override/{name}` endpoint | `execution_router.py` | 1h |
| 4.1.5 | Add `overrideValue()` to API client | `api.ts` | 30min |
| 4.1.6 | Wire up override button in DetailPanel | `DetailPanel.tsx` | 1h |
| 4.1.7 | Add "overridden" visual indicator to nodes | `ValueNode.tsx` | 1h |
| 4.1.8 | Test with various data types | — | 2h |

---

### 4.2 Function Modification Dialog

**Priority**: MEDIUM  
**Estimated Effort**: 2-3 days

Allow users to modify working interpretation and retry function nodes.

#### Requirements

1. **Modification Dialog UI**
   - Edit paradigm selection
   - Edit prompt template path
   - Edit output type
   - Preview changes before apply

2. **Backend Support**
   - `POST /api/execution/modify-function/{flow_index}` endpoint
   - Update inference's working interpretation
   - Reset node status to pending
   - Optionally retry immediately

3. **Paradigm Browser**
   - List available paradigms (custom + default)
   - Show paradigm details on hover
   - Filter/search paradigms

#### Implementation

**Backend**:
```python
async def modify_function(
    self,
    flow_index: str,
    modifications: Dict[str, Any],
    retry: bool = False
) -> Dict[str, Any]:
    """Modify a function node's working interpretation."""
    inference = self.inference_repo.get_by_flow_index(flow_index)
    
    # Update working interpretation
    wi = inference.working_interpretation
    if 'paradigm' in modifications:
        wi['paradigm'] = modifications['paradigm']
    if 'prompt_location' in modifications:
        wi['prompt_location'] = modifications['prompt_location']
    if 'output_type' in modifications:
        wi['output_type'] = modifications['output_type']
    
    # Reset node status
    self.node_statuses[flow_index] = 'pending'
    
    if retry:
        await self.run_to(flow_index)
    
    return {"success": True, "modified": flow_index}
```

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 4.2.1 | Create `FunctionModifyModal` component | `panels/FunctionModifyModal.tsx` | 4h |
| 4.2.2 | Create `ParadigmBrowser` component | `panels/ParadigmBrowser.tsx` | 3h |
| 4.2.3 | Add `modify_function()` to ExecutionController | `execution_service.py` | 2h |
| 4.2.4 | Add `POST /execution/modify-function/{index}` | `execution_router.py` | 1h |
| 4.2.5 | Wire up modify button in DetailPanel | `DetailPanel.tsx` | 1h |
| 4.2.6 | Add "modified" visual indicator | `FunctionNode.tsx` | 1h |

---

### 4.3 Selective Re-run

**Priority**: HIGH  
**Estimated Effort**: 2 days

Reset and re-execute from any node in the graph.

#### Requirements

1. **Re-run Analysis**
   - Identify all downstream nodes
   - Calculate reset scope
   - Show confirmation with affected nodes

2. **Backend Support**
   - `POST /api/execution/rerun-from/{flow_index}` endpoint
   - Reset target and all descendants
   - Clear affected references
   - Start execution from earliest ready

3. **Visual Feedback**
   - Highlight nodes to be reset (before confirm)
   - Show reset animation
   - Progress from re-run point

#### Implementation

**Backend**:
```python
async def rerun_from(self, flow_index: str) -> Dict[str, Any]:
    """Reset and re-execute from a specific node."""
    # Find all descendants
    descendants = self._find_descendants(flow_index)
    nodes_to_reset = [flow_index] + descendants
    
    # Reset node statuses
    for fi in nodes_to_reset:
        self.node_statuses[fi] = 'pending'
        # Clear computed reference if exists
        concept = self._get_concept_for_flow_index(fi)
        if concept and not concept.is_ground:
            concept.reference = None
    
    # Emit reset event
    self._emit("execution:partial_reset", {
        "reset_nodes": nodes_to_reset
    })
    
    # Start execution
    await self.start()
    
    return {
        "success": True,
        "reset_count": len(nodes_to_reset)
    }
```

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 4.3.1 | Add `rerun_from()` to ExecutionController | `execution_service.py` | 2h |
| 4.3.2 | Add descendant finding helper | `execution_service.py` | 1h |
| 4.3.3 | Add `POST /execution/rerun-from/{index}` | `execution_router.py` | 1h |
| 4.3.4 | Create confirmation modal | `panels/RerunConfirmModal.tsx` | 2h |
| 4.3.5 | Add "Re-run from here" button to DetailPanel | `DetailPanel.tsx` | 1h |
| 4.3.6 | Add highlight for affected nodes | `GraphCanvas.tsx` | 2h |
| 4.3.7 | Handle `execution:partial_reset` event | `useWebSocket.ts` | 1h |

---

### 4.4 Checkpoint Resume/Fork (Complete Implementation)

**Priority**: MEDIUM  
**Estimated Effort**: 2 days

The CheckpointPanel exists but needs full wiring.

#### Remaining Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 4.4.1 | Implement `list_runs()` in ExecutionController | `execution_service.py` | 1h |
| 4.4.2 | Implement `list_checkpoints()` | `execution_service.py` | 1h |
| 4.4.3 | Implement `resume_from_checkpoint()` | `execution_service.py` | 2h |
| 4.4.4 | Implement `fork_from_checkpoint()` | `execution_service.py` | 2h |
| 4.4.5 | Wire CheckpointPanel to API | `CheckpointPanel.tsx` | 2h |
| 4.4.6 | Add checkpoint API methods | `api.ts` | 1h |
| 4.4.7 | Sync node statuses from loaded checkpoint | `execution_service.py` | 1h |

---

## Phase 5: Polish & Advanced Features

**Goal**: Production-ready tool with advanced capabilities.

### 5.1 Keyboard Shortcuts

**Priority**: MEDIUM  
**Estimated Effort**: 1 day

| Shortcut | Action |
|----------|--------|
| `Space` | Run/Pause toggle |
| `S` | Step |
| `R` | Reset |
| `B` | Toggle breakpoint on selected |
| `F` | Fit view |
| `Escape` | Close modal/deselect |
| `Ctrl+F` | Search nodes |
| `Ctrl+S` | Save (in editor) |
| `1` | Switch to Canvas |
| `2` | Switch to Editor |

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 5.1.1 | Add keyboard event handler | `App.tsx` | 2h |
| 5.1.2 | Add shortcut hints to buttons | Various | 1h |
| 5.1.3 | Add keyboard shortcut help modal | `ShortcutHelp.tsx` | 1h |

---

### 5.2 Node Search

**Priority**: MEDIUM  
**Estimated Effort**: 1 day

Search and filter nodes in the graph.

#### Requirements

- Search by concept name
- Search by natural name
- Filter by status (pending/completed/failed)
- Filter by category
- Highlight matches
- Navigate to match

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 5.2.1 | Create `NodeSearchPanel` component | `panels/NodeSearchPanel.tsx` | 3h |
| 5.2.2 | Add search to graph store | `graphStore.ts` | 1h |
| 5.2.3 | Add highlight for search matches | `GraphCanvas.tsx` | 2h |
| 5.2.4 | Wire Ctrl+F to open search | `App.tsx` | 30min |

---

### 5.3 Export/Import

**Priority**: LOW  
**Estimated Effort**: 2 days

Export execution state and results.

#### Export Formats

| Format | Contents |
|--------|----------|
| **Execution Report** (JSON) | All node statuses, logs, reference data |
| **Execution Trace** (JSON) | Step-by-step execution history |
| **Results** (JSON/CSV) | Final values only |
| **Graph Image** (SVG/PNG) | Visual graph snapshot |

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 5.3.1 | Add `GET /execution/export` endpoint | `execution_router.py` | 2h |
| 5.3.2 | Add export button to ControlPanel | `ControlPanel.tsx` | 1h |
| 5.3.3 | Add export format selector modal | `ExportModal.tsx` | 2h |
| 5.3.4 | Implement graph SVG export | `GraphCanvas.tsx` | 2h |
| 5.3.5 | Add import checkpoint functionality | `CheckpointPanel.tsx` | 2h |

---

### 5.4 Run Comparison

**Priority**: LOW  
**Estimated Effort**: 3 days

Compare results between two runs.

#### Requirements

- Select two runs to compare
- Side-by-side node status comparison
- Value diff for changed nodes
- Highlight differences in graph

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 5.4.1 | Create `RunComparisonPanel` component | `panels/RunComparisonPanel.tsx` | 4h |
| 5.4.2 | Add run comparison API | `checkpoint_router.py` | 2h |
| 5.4.3 | Create diff visualization | `DiffViewer.tsx` | 4h |
| 5.4.4 | Add comparison mode to graph | `GraphCanvas.tsx` | 3h |

---

### 5.5 Performance Optimization

**Priority**: MEDIUM  
**Estimated Effort**: 2 days

Handle graphs with 500+ nodes smoothly.

#### Optimizations

1. **Virtual Rendering**: Only render visible nodes
2. **Lazy Data Loading**: Load reference data on demand
3. **Batch Updates**: Throttle WebSocket updates
4. **Web Workers**: Move heavy computation off main thread

#### Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 5.5.1 | Implement node virtualization | `GraphCanvas.tsx` | 4h |
| 5.5.2 | Add lazy reference loading | `DetailPanel.tsx` | 2h |
| 5.5.3 | Throttle WebSocket status updates | `useWebSocket.ts` | 2h |
| 5.5.4 | Profile and optimize hot paths | Various | 4h |

---

### 5.6 Watch Expressions

**Priority**: LOW  
**Estimated Effort**: 2 days

Monitor specific values during execution.

#### Requirements

- Add expressions to watch list
- Auto-update on node completion
- Show value history
- Conditional breakpoints based on values

---

## Implementation Priority

### High Priority (Do First)

| Task | Phase | Effort | Impact |
|------|-------|--------|--------|
| Value Override Dialog | 4.1 | 2-3 days | Enables manual intervention |
| Selective Re-run | 4.3 | 2 days | Enables iterative debugging |
| Checkpoint Resume | 4.4 | 2 days | Saves execution time |

### Medium Priority

| Task | Phase | Effort | Impact |
|------|-------|--------|--------|
| Function Modification | 4.2 | 2-3 days | Enables paradigm tweaking |
| Keyboard Shortcuts | 5.1 | 1 day | Improves UX |
| Node Search | 5.2 | 1 day | Helps with large graphs |
| Performance Optimization | 5.5 | 2 days | Needed for large plans |

### Low Priority (Nice to Have)

| Task | Phase | Effort | Impact |
|------|-------|--------|--------|
| Export/Import | 5.3 | 2 days | Reporting |
| Run Comparison | 5.4 | 3 days | Advanced debugging |
| Watch Expressions | 5.6 | 2 days | Advanced debugging |

---

## Estimated Timeline

| Week | Tasks | Deliverable |
|------|-------|-------------|
| Week 1 | 4.1 Value Override + 4.4 Checkpoint | Interactive value editing |
| Week 2 | 4.3 Selective Re-run + 5.1 Shortcuts | Re-run workflow |
| Week 3 | 4.2 Function Modification + 5.2 Search | Function editing |
| Week 4 | 5.5 Performance + 5.3 Export | Polish |

**Total Estimated Time**: 4 weeks (20 working days)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Value override works | Ground + computed nodes |
| Re-run works | From any node |
| Checkpoint resume | Full state restoration |
| Large graph handling | 500+ nodes without lag |
| Keyboard shortcuts | All common actions |

---

## Technical Notes

### Dependency Graph for Re-run

To find descendants for selective re-run:

```python
def _find_descendants(self, flow_index: str) -> List[str]:
    """Find all nodes that depend on the given node."""
    descendants = []
    queue = [flow_index]
    visited = set()
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        # Find inferences that use this concept
        for inf in self.inference_repo:
            if current in inf.value_concepts or current == inf.function_concept:
                target_fi = inf.flow_info['flow_index']
                if target_fi not in visited:
                    descendants.append(target_fi)
                    queue.append(target_fi)
    
    return descendants
```

### Value Override Validation

Before applying override:

1. Validate shape matches expected axes
2. Validate element types
3. Check for circular dependencies
4. Warn if node has already been used

---

## Related Documents

- **[Canvas App Overview](canvas_app_overview.md)**: Architecture and concepts
- **[User Guide](canvas_app_user_guide.md)**: Usage instructions
- **[API Reference](canvas_app_api_reference.md)**: REST and WebSocket API
- **[IMPLEMENTATION_JOURNAL.md](../../../../canvas_app/IMPLEMENTATION_JOURNAL.md)**: Development history
- **[AGENT_PANEL_PLAN.md](../../../../canvas_app/AGENT_PANEL_PLAN.md)**: Agent feature design
- **[CHECKPOINT_FEATURE_PLAN.md](../../../../canvas_app/CHECKPOINT_FEATURE_PLAN.md)**: Checkpoint feature design

---

**Last Updated**: December 2024  
**Status**: Active Development
