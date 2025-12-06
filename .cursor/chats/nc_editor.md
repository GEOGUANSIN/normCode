# Review project documentation files
_Exported on 12/5/2025 at 11:08:17 GMT+8 from Cursor (2.1.32)_

---

**User**

read the background in @.cursor/chats/orchestrator_context.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/raw--normcode_terminology_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/raw--normcode_to_orchestrator_repo_mapping.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/raw--normcode_translation_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_agent_sequence_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_core_syntax.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_orchestrator_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_reference_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_semantical_concepts.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_syntactical_concepts.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_syntax_guide.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared--file_info-normcode_draft-ncd.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared--file_info-normcode_formal-nc.md @direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared--file_info-normcode_natural-ncn.md 

---

**Cursor**


## Summary of Key Concepts

### 1. **NormCode Architecture**
- Semi-formal language for constructing a plan of inferences
- Core units: inferences defined by functional concepts (`<=`) and value concepts (`<-`)
- Concepts: semantical (`{}`, `<>`, `[]`, `::()`) and syntactical (operators like `*every`, `&across`, `$.`, `@if`)

### 2. **Execution Flow**
- CLI → Orchestrator → Body + AgentFrame → Agent's Sequences → Paradigms → Tools
- Orchestrator manages dependency-driven execution using a Blackboard pattern
- Agent's Sequences (Simple, Grouping, Quantifying, Assigning, Imperative, Judgement, Timing) execute individual inferences

### 3. **Data Storage (References)**
- Multi-dimensional containers with named axes
- Concepts have References that hold actual data
- Shape and axes organize information by context

### 4. **Translation Process**
- Normtext → NormCode Draft (`.ncd`) → Formal NormCode (`.nc`) → Natural summary (`.ncn`)
- Multi-step decomposition using prompts (initialization, completion check, concept identification, question inquiry, operator selection, etc.)

### 5. **Repository Mapping**
- NormCode drafts map to `ConceptRepo` and `InferenceRepo`
- `working_interpretation` bridges syntax to orchestration
- Patterns for converting NormCode to Python repository scripts

### 6. **File Formats**
- `.ncd`: Annotated blueprint with `?:`, `/:`, `...:` annotations
- `.nc`: Formal, machine-readable with flow indices and agent sequence types
- `.ncn`: Natural language summary for human readability

I understand the system architecture, execution model, and translation workflow. What would you like to explore or work on next?

---

**User**

@editor_app understand how this works as an editor. and why it does not handle .ncd .nc and .ncn in the best interface 

---

**Cursor**

I'll explore the editor app to understand its architecture and limitations with NormCode files.

## Analysis: How the Editor Works and Its Limitations for NormCode Files

### Current Architecture

The **NormCode Editor** is a web-based IDE with the following architecture:

**Backend (FastAPI):**
- RESTful API for managing repositories, concepts, and inferences
- Stores data in JSON files in `data/` directory
- Supports repository execution via the NormCode orchestrator
- Structure: `data/repositories/{name}/`, `data/concepts/`, `data/inferences/`, `data/logs/`

**Frontend (React + TypeScript + Vite):**
- Single-page application with 3 main views:
  - **Global Concepts View**: Manage reusable concept templates
  - **Global Inferences View**: Manage reusable inference templates
  - **Repository View**: Compose repositories from concepts/inferences
- Uses `JSONEditor` component for editing structured data
- Supports multiple sub-views: Concepts, Inferences, Flow Editor, Graph Visualization, Logs

### What It's Designed For

The editor is specifically built to work with **Python repository format**:
- `ConceptEntry` objects (JSON schema with fields like `concept_name`, `type`, `reference_data`, etc.)
- `InferenceEntry` objects (JSON schema with `inference_sequence`, `working_interpretation`, etc.)
- Direct mapping to `ConceptRepo` and `InferenceRepo` Python classes
- Focus on **visual flow editing** and **graph visualization** of inference dependencies

### Why It Doesn't Handle .ncd, .nc, and .ncn Well

#### **1. Fundamentally Different Formats**

| Feature | Current Editor | NormCode Files (.ncd/.nc/.ncn) |
|---------|---------------|--------------------------------|
| **Format** | JSON (structured objects) | Plain text with special syntax |
| **Structure** | Flat lists of concepts/inferences | Hierarchical, indentation-based |
| **Editing** | Form-based + JSON tree editor | Text-based with syntax rules |
| **Annotations** | JSON fields | Special markers (`?:`, `/:`, `...:`) |
| **Flow Index** | Separate metadata field | Inline with syntax (e.g., `1.1.2`) |

#### **2. Missing Text-Oriented Features**

The current editor **lacks** essential features for NormCode text files:

❌ **No syntax highlighting** for NormCode operators (`<=`, `<-`, `::()`, `{}`, `[]`)  
❌ **No indentation awareness** - critical for NormCode hierarchy  
❌ **No annotation support** for `...:`, `?:`, `/:` markers  
❌ **No validation** for NormCode syntax rules  
❌ **No auto-completion** for operators and patterns  
❌ **No line-by-line editing** suitable for textual inferences  

#### **3. Design Mismatch**

**Current Design:**
```json
{
  "id": "abc-123",
  "concept_name": "{number pair}",
  "type": "{}",
  "reference_data": [["%(123)", "%(98)"]],
  "is_ground_concept": true
}
```

**NormCode (.ncd) Format:**
```normcode
<- {number pair}
    ...: "The two numbers to add"
    <= $.({pair})
    <- {number 1}
        /: The first number
    <- {number 2}
        /: The second number
```

The editor expects **structured JSON objects** but NormCode files are **semi-formal text** with:
- Hierarchical indentation (4 spaces per level)
- Inline operators and annotations
- Natural language mixed with formal syntax
- Context conveyed through visual layout

#### **4. Workflow Impedance**

The NormCode translation process (from your guides) follows:
```
Normtext → .ncd (annotated draft) → .nc (formal) → .ncn (natural)
                                            ↓
                                    Python repos (.py)
                                            ↓
                                    JSON export (current editor format)
```

The current editor operates **only at the final stage** (JSON), missing the entire:
- **Phase 2**: Deconstruction to `.ncd` 
- **Phase 3**: Formalization to `.nc`
- **Phase 4**: Natural summary to `.ncn`

### What Would Make It Better for NormCode Files

To properly support `.ncd`, `.nc`, and `.ncn` files, the editor would need:

1. **Text Editor Mode**
   - Monaco Editor or CodeMirror with custom NormCode language
   - Syntax highlighting for operators and concept types
   - Indentation guides and auto-indentation
   - Bracket/operator matching

2. **NormCode-Aware Features**
   - Annotation markers (color-coded `?:`, `/:`, `...:`)
   - Operator palette for inserting `<=`, `<-`, `::()`, etc.
   - Flow index visualization in gutter
   - Hierarchical outline view

3. **Multi-Format Support**
   - Side-by-side view: `.ncd` ↔ `.nc` ↔ `.ncn`
   - Format conversion utilities
   - Import/export between text and JSON formats

4. **Translation Workflow Integration**
   - Step-by-step decomposition interface
   - Question formulation helpers
   - Operator selection wizards
   - Draft update preview

### Recommendation

The current editor is **excellent for its intended purpose** (managing Python repository JSON files), but it's **fundamentally incompatible** with the text-based NormCode file formats. 

**Two paths forward:**

**Option A: Separate Tool**
- Keep current editor for JSON repositories
- Build a separate text editor for `.ncd`/`.nc`/`.ncn` files
- Provide conversion utilities between formats

**Option B: Dual-Mode Editor**
- Add a "Text Mode" tab alongside current "JSON Mode"
- Implement NormCode syntax support in text mode
- Bidirectional sync between text and JSON representations
- More complex but provides unified experience

The key insight: **JSON editing ≠ NormCode editing**. The hierarchical, annotation-rich, indentation-based nature of NormCode files requires a fundamentally different editing paradigm than form-based JSON manipulation.

```json
{
  "id": "abc-123",
  "concept_name": "{number pair}",
  "type": "{}",
  "reference_data": [["%(123)", "%(98)"]],
  "is_ground_concept": true
}
```

```plaintext
<- {number pair}
    ...: "The two numbers to add"
    <= $.({pair})
    <- {number 1}
        /: The first number
    <- {number 2}
        /: The second number
```

```plaintext
Normtext → .ncd (annotated draft) → .nc (formal) → .ncn (natural)
                                            ↓
                                    Python repos (.py)
                                            ↓
                                    JSON export (current editor format)
```

---

**User**

think about a better interface directly editing  the .ncn, .ncd, and .nc - and also how these files can be linked together dynamically - this can later be added to @launch_streamlit_app.py 

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

I'll implement the NormCode File Editor Tab according to the plan. Let me start by marking the first todo as in_progress and begin implementation.

```python
"""
NormCode Manifest Management

Manages manifest files that link related NormCode files (.ncd, .nc, .ncn).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List


class ManifestManager:
    """Manages NormCode project manifests."""
    
    def __init__(self, manifests_dir: str = "data/manifests"):
        """
        Initialize the manifest manager.
        
        Args:
            manifests_dir: Directory to store manifest files
        """
        # Get the streamlit_app directory
        script_dir = Path(__file__).parent.parent
        self.manifests_dir = script_dir / manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    def create(
        self, 
        project_name: str,
        draft_path: Optional[str] = None,
        formal_path: Optional[str] = None,
        natural_path: Optional[str] = None,
        description: str = "",
        version: str = "1.0"
    ) -> Dict:
        """
        Create a new manifest.
        
        Args:
            project_name: Name of the project
            draft_path: Path to .ncd file
            formal_path: Path to .nc file
            natural_path: Path to .ncn file
            description: Project description
            version: Project version
            
        Returns:
            Created manifest dictionary
        """
        manifest = {
            "project_name": project_name,
            "created": datetime.now().isoformat(),
            "files": {
                "draft": draft_path,
                "formal": formal_path,
                "natural": natural_path
            },
            "metadata": {
                "description": description,
                "version": version
            }
        }
        
        # Validate the manifest
        self._validate(manifest)
        
        return manifest
    
    def save(self, manifest: Dict) -> str:
        """
        Save a manifest to disk.
        
        Args:
            manifest: Manifest dictionary to save
            
        Returns:
            Path to saved manifest file
        """
        self._validate(manifest)
        
        project_name = manifest["project_name"]
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        return str(manifest_path)
    
    def load(self, project_name: str) -> Optional[Dict]:
        """
        Load a manifest from disk.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Manifest dictionary or None if not found
        """
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        self._validate(manifest)
        return manifest
    
    def list_manifests(self) -> List[str]:
        """
        List all available manifest files.
        
        Returns:
            List of project names
        """
        if not self.manifests_dir.exists():
            return []
        
        manifests = []
        for file_path in self.manifests_dir.glob("*.json"):
            project_name = file_path.stem
            manifests.append(project_name)
        
        return sorted(manifests)
    
    def update_file_path(
        self, 
        manifest: Dict, 
        file_type: str, 
        new_path: str
    ) -> Dict:
        """
        Update a file path in the manifest.
        
        Args:
            manifest: Manifest dictionary
            file_type: Type of file ('draft', 'formal', or 'natural')
            new_path: New file path
            
        Returns:
            Updated manifest
        """
        if file_type not in ['draft', 'formal', 'natural']:
            raise ValueError(f"Invalid file type: {file_type}")
        
        manifest["files"][file_type] = new_path
        self._validate(manifest)
        
        return manifest
    
    def delete(self, project_name: str) -> bool:
        """
        Delete a manifest file.
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if deleted, False if not found
        """
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        if manifest_path.exists():
            manifest_path.unlink()
            return True
        
        return False
    
    def _validate(self, manifest: Dict) -> None:
        """
        Validate manifest structure.
        
        Args:
            manifest: Manifest to validate
            
        Raises:
            ValueError: If manifest is invalid
        """
        required_keys = ["project_name", "created", "files", "metadata"]
        for key in required_keys:
            if key not in manifest:
                raise ValueError(f"Missing required key: {key}")
        
        # Validate files section
        if not isinstance(manifest["files"], dict):
            raise ValueError("'files' must be a dictionary")
        
        file_types = ["draft", "formal", "natural"]
        for file_type in file_types:
            if file_type not in manifest["files"]:
                raise ValueError(f"Missing file type in 'files': {file_type}")
        
        # Validate metadata section
        if not isinstance(manifest["metadata"], dict):
            raise ValueError("'metadata' must be a dictionary")
        
        if "description" not in manifest["metadata"]:
            raise ValueError("Missing 'description' in metadata")
        
        if "version" not in manifest["metadata"]:
            raise ValueError("Missing 'version' in metadata")

```

```python
"""
NormCode Format Parsers

Provides parsers for .ncd, .nc, and .ncn file formats with a common IR.
"""

from .ir import NormCodeNode
from .ncd_parser import NCDParser
from .nc_parser import NCParser
from .ncn_parser import NCNParser

__all__ = ['NormCodeNode', 'NCDParser', 'NCParser', 'NCNParser']

```

```python
"""
Intermediate Representation (IR) for NormCode

Common data structure used by all parsers and converters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class NormCodeNode:
    """
    Intermediate representation for a NormCode node.
    
    This structure is format-agnostic and can represent nodes from
    .ncd, .nc, or .ncn files.
    """
    
    flow_index: str = ""  # e.g., "1.2.3"
    depth: int = 0  # Indentation depth
    node_type: str = ""  # e.g., "inference", "concept"
    sequence_type: str = ""  # e.g., "imperative", "grouping", "assigning"
    content: str = ""  # The main content of the node
    
    # Annotations (from .ncd format)
    annotations: Dict[str, str] = field(default_factory=dict)
    # Possible keys: "question" (?:), "description" (/:), "source_text" (...:)
    
    # Child nodes
    children: List['NormCodeNode'] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    # Can store format-specific information
    
    def __repr__(self):
        """String representation for debugging."""
        return f"NormCodeNode(flow={self.flow_index}, type={self.node_type}, depth={self.depth}, content={self.content[:50]}...)"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "flow_index": self.flow_index,
            "depth": self.depth,
            "node_type": self.node_type,
            "sequence_type": self.sequence_type,
            "content": self.content,
            "annotations": self.annotations,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NormCodeNode':
        """Create from dictionary."""
        node = cls(
            flow_index=data.get("flow_index", ""),
            depth=data.get("depth", 0),
            node_type=data.get("node_type", ""),
            sequence_type=data.get("sequence_type", ""),
            content=data.get("content", ""),
            annotations=data.get("annotations", {}),
            metadata=data.get("metadata", {})
        )
        node.children = [cls.from_dict(child) for child in data.get("children", [])]
        return node

```

```python
"""
NormCode Draft (.ncd) Parser

Parses indentation-based .ncd files into IR and serializes back.
"""

import re
from typing import List, Tuple, Optional
from .ir import NormCodeNode


class NCDParser:
    """Parser for .ncd (NormCode Draft) format."""
    
    INDENT_SIZE = 4  # Standard indentation is 4 spaces
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .ncd file content into IR nodes.
        
        Args:
            file_content: Content of .ncd file
            
        Returns:
            List of root-level NormCodeNode objects
        """
        lines = file_content.split('\n')
        return cls._parse_lines(lines)
    
    @classmethod
    def _parse_lines(cls, lines: List[str]) -> List[NormCodeNode]:
        """Parse lines into a tree structure."""
        if not lines:
            return []
        
        nodes = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Parse this line and its children
            node, consumed = cls._parse_node(lines, i)
            if node:
                nodes.append(node)
            i += consumed
        
        return nodes
    
    @classmethod
    def _parse_node(cls, lines: List[str], start_idx: int) -> Tuple[Optional[NormCodeNode], int]:
        """
        Parse a single node and its children.
        
        Returns:
            Tuple of (node, number of lines consumed)
        """
        line = lines[start_idx]
        
        # Calculate depth from indentation
        depth = cls._get_depth(line)
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return None, 1
        
        # Parse the line content
        node = cls._parse_line_content(stripped, depth)
        
        # Parse children (lines with greater depth)
        i = start_idx + 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                i += 1
                continue
            
            next_depth = cls._get_depth(next_line)
            
            # If next line is a child (deeper indentation)
            if next_depth > depth:
                child, consumed = cls._parse_node(lines, i)
                if child:
                    node.children.append(child)
                i += consumed
            else:
                # Next line is a sibling or parent, stop processing children
                break
        
        lines_consumed = i - start_idx
        return node, lines_consumed
    
    @classmethod
    def _get_depth(cls, line: str) -> int:
        """Calculate indentation depth."""
        leading_spaces = len(line) - len(line.lstrip())
        return leading_spaces // cls.INDENT_SIZE
    
    @classmethod
    def _parse_line_content(cls, line: str, depth: int) -> NormCodeNode:
        """
        Parse the content of a single line.
        
        Handles:
        - Concept definitions (<-, <=)
        - Flow indices (1.2.3)
        - Annotations (?:, /:, ...:)
        - Sequence types
        """
        node = NormCodeNode(depth=depth)
        
        # Check for annotations
        if line.startswith('?:'):
            # Question annotation
            node.annotations['question'] = line[2:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        elif line.startswith('/:'):
            # Description annotation
            node.annotations['description'] = line[2:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        elif line.startswith('...:'):
            # Source text annotation
            node.annotations['source_text'] = line[4:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        
        # Parse main concept line with optional metadata
        # Format: concept_def | flow_index sequence_type // comment
        parts = line.split('|')
        concept_part = parts[0].strip()
        
        # Extract metadata if present
        if len(parts) > 1:
            metadata_part = parts[1].strip()
            
            # Extract flow index (numeric pattern like 1.2.3)
            flow_match = re.match(r'^([\d.]+)', metadata_part)
            if flow_match:
                node.flow_index = flow_match.group(1).strip()
                metadata_part = metadata_part[len(flow_match.group(1)):].strip()
            
            # Extract sequence type
            # Common types: imperative, grouping, assigning, quantifying, timing, judgement
            sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
            for seq_type in sequence_types:
                if seq_type in metadata_part.lower():
                    node.sequence_type = seq_type
                    break
        
        # Determine node type from concept syntax
        if concept_part.startswith('<='):
            node.node_type = 'functional_concept'
            node.content = concept_part[2:].strip()
        elif concept_part.startswith('<-'):
            node.node_type = 'value_concept'
            node.content = concept_part[2:].strip()
        elif concept_part.startswith(':<:'):
            node.node_type = 'output_concept'
            node.content = concept_part
        else:
            # Generic concept
            node.node_type = 'concept'
            node.content = concept_part
        
        return node
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes back to .ncd format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .ncd format string
        """
        lines = []
        for node in nodes:
            cls._serialize_node(node, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_node(cls, node: NormCodeNode, lines: List[str]) -> None:
        """Recursively serialize a node and its children."""
        indent = ' ' * (node.depth * cls.INDENT_SIZE)
        
        # Handle annotations
        if node.node_type == 'annotation':
            lines.append(f"{indent}{node.content}")
        else:
            # Build the line
            if node.node_type == 'functional_concept':
                line = f"{indent}<= {node.content}"
            elif node.node_type == 'value_concept':
                line = f"{indent}<- {node.content}"
            elif node.node_type == 'output_concept':
                line = f"{indent}{node.content}"
            else:
                line = f"{indent}{node.content}"
            
            # Add metadata if present
            metadata_parts = []
            if node.flow_index:
                metadata_parts.append(node.flow_index)
            if node.sequence_type:
                metadata_parts.append(node.sequence_type)
            
            if metadata_parts:
                line += f" | {' '.join(metadata_parts)}"
            
            lines.append(line)
            
            # Add annotations as children
            for ann_type, ann_value in node.annotations.items():
                if ann_type == 'question':
                    lines.append(f"{indent}    ?: {ann_value}")
                elif ann_type == 'description':
                    lines.append(f"{indent}    /: {ann_value}")
                elif ann_type == 'source_text':
                    lines.append(f"{indent}    ...: {ann_value}")
        
        # Serialize children
        for child in node.children:
            cls._serialize_node(child, lines)

```

```python
"""
NormCode Formal (.nc) Parser

Parses line-based .nc files into IR and serializes back.
"""

import re
from typing import List, Optional
from .ir import NormCodeNode


class NCParser:
    """Parser for .nc (NormCode Formal) format."""
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .nc file content into IR nodes.
        
        .nc format: flow_index.type|content
        Example: 1.2.3.imperative|<= ::(do something)
        
        Args:
            file_content: Content of .nc file
            
        Returns:
            List of NormCodeNode objects
        """
        lines = file_content.strip().split('\n')
        nodes = []
        
        for line in lines:
            if not line.strip():
                continue
            
            node = cls._parse_line(line)
            if node:
                nodes.append(node)
        
        # Build tree structure from flat list
        return cls._build_tree(nodes)
    
    @classmethod
    def _parse_line(cls, line: str) -> Optional[NormCodeNode]:
        """
        Parse a single .nc format line.
        
        Format: flow_index.type|content
        Example: 1.2.3.imperative|<= ::(do something)
        """
        # Split on first | to separate metadata from content
        if '|' not in line:
            return None
        
        metadata_part, content = line.split('|', 1)
        
        # Parse metadata: flow_index.type or flow_index.type_detail
        parts = metadata_part.split('.')
        
        if len(parts) < 2:
            return None
        
        # Flow index is all parts except the last (type)
        flow_index = '.'.join(parts[:-1])
        type_info = parts[-1]
        
        # Determine depth from flow index
        depth = len(flow_index.split('.')) - 1
        
        # Parse type info (may include additional details like _::{%(composition)})
        node_type, sequence_type = cls._parse_type_info(type_info)
        
        node = NormCodeNode(
            flow_index=flow_index,
            depth=depth,
            node_type=node_type,
            sequence_type=sequence_type,
            content=content.strip()
        )
        
        return node
    
    @classmethod
    def _parse_type_info(cls, type_info: str) -> tuple:
        """
        Parse type information from .nc format.
        
        Examples:
        - "imperative" -> ("inference", "imperative")
        - "object" -> ("concept", "")
        - "imperative_::{%(composition)}" -> ("inference", "imperative")
        """
        # Common sequence types
        sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
        
        for seq_type in sequence_types:
            if type_info.startswith(seq_type):
                return "inference", seq_type
        
        # If it's not a sequence type, it's likely a concept type
        if type_info.startswith('object') or type_info.startswith('statement') or type_info.startswith('relation'):
            return "concept", ""
        
        if type_info == 'output':
            return "output_concept", ""
        
        return "concept", ""
    
    @classmethod
    def _build_tree(cls, nodes: List[NormCodeNode]) -> List[NormCodeNode]:
        """
        Build tree structure from flat list of nodes.
        
        Uses flow indices to determine parent-child relationships.
        """
        if not nodes:
            return []
        
        # Create a map of flow_index -> node
        node_map = {node.flow_index: node for node in nodes}
        
        # Find root nodes and build parent-child relationships
        roots = []
        
        for node in nodes:
            # Determine parent index
            parent_index = cls._get_parent_index(node.flow_index)
            
            if parent_index and parent_index in node_map:
                # Add as child to parent
                parent = node_map[parent_index]
                parent.children.append(node)
            else:
                # This is a root node
                roots.append(node)
        
        return roots
    
    @classmethod
    def _get_parent_index(cls, flow_index: str) -> Optional[str]:
        """
        Get parent flow index.
        
        Example: "1.2.3" -> "1.2"
        """
        parts = flow_index.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes to .nc format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .nc format string
        """
        lines = []
        cls._serialize_nodes(nodes, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_nodes(cls, nodes: List[NormCodeNode], lines: List[str]) -> None:
        """Recursively serialize nodes in depth-first order."""
        for node in nodes:
            # Build type info
            if node.sequence_type:
                type_info = node.sequence_type
            elif node.node_type == 'output_concept':
                type_info = 'output'
            elif node.node_type == 'concept' or node.node_type == 'value_concept':
                type_info = 'object'
            else:
                type_info = 'object'
            
            # Build line: flow_index.type|content
            line = f"{node.flow_index}.{type_info}|{node.content}"
            lines.append(line)
            
            # Serialize children
            cls._serialize_nodes(node.children, lines)

```

```python
"""
NormCode Natural (.ncn) Parser

Parses natural language .ncn files into IR and serializes back.
"""

import re
from typing import List, Optional
from .ir import NormCodeNode


class NCNParser:
    """Parser for .ncn (NormCode Natural) format."""
    
    INDENT_SIZE = 4  # Standard indentation is 4 spaces
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .ncn file content into IR nodes.
        
        .ncn format is similar to .ncd but with natural language content
        and structure markers (<= for method, <- for component).
        
        Args:
            file_content: Content of .ncn file
            
        Returns:
            List of root-level NormCodeNode objects
        """
        lines = file_content.split('\n')
        return cls._parse_lines(lines)
    
    @classmethod
    def _parse_lines(cls, lines: List[str]) -> List[NormCodeNode]:
        """Parse lines into a tree structure."""
        if not lines:
            return []
        
        nodes = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Parse this line and its children
            node, consumed = cls._parse_node(lines, i)
            if node:
                nodes.append(node)
            i += consumed
        
        return nodes
    
    @classmethod
    def _parse_node(cls, lines: List[str], start_idx: int) -> tuple:
        """
        Parse a single node and its children.
        
        Returns:
            Tuple of (node, number of lines consumed)
        """
        line = lines[start_idx]
        
        # Calculate depth from indentation
        depth = cls._get_depth(line)
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return None, 1
        
        # Parse the line content
        node = cls._parse_line_content(stripped, depth)
        
        # Parse children (lines with greater depth)
        i = start_idx + 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                i += 1
                continue
            
            next_depth = cls._get_depth(next_line)
            
            # If next line is a child (deeper indentation)
            if next_depth > depth:
                child, consumed = cls._parse_node(lines, i)
                if child:
                    node.children.append(child)
                i += consumed
            else:
                # Next line is a sibling or parent, stop processing children
                break
        
        lines_consumed = i - start_idx
        return node, lines_consumed
    
    @classmethod
    def _get_depth(cls, line: str) -> int:
        """Calculate indentation depth."""
        leading_spaces = len(line) - len(line.lstrip())
        return leading_spaces // cls.INDENT_SIZE
    
    @classmethod
    def _parse_line_content(cls, line: str, depth: int) -> NormCodeNode:
        """
        Parse the content of a single line.
        
        .ncn uses <= and <- markers with natural language content.
        """
        node = NormCodeNode(depth=depth)
        
        # Determine node type from syntax
        if line.startswith('<='):
            node.node_type = 'functional_concept'
            node.content = line[2:].strip()
        elif line.startswith('<-'):
            node.node_type = 'value_concept'
            node.content = line[2:].strip()
        elif line.startswith(':<:'):
            node.node_type = 'output_concept'
            node.content = line
        else:
            # Natural language statement
            node.node_type = 'concept'
            node.content = line
        
        # Store as description annotation since .ncn is descriptive
        if node.content:
            node.annotations['description'] = node.content
        
        return node
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes to .ncn format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .ncn format string
        """
        lines = []
        for node in nodes:
            cls._serialize_node(node, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_node(cls, node: NormCodeNode, lines: List[str]) -> None:
        """Recursively serialize a node and its children."""
        indent = ' ' * (node.depth * cls.INDENT_SIZE)
        
        # Use description annotation if available, otherwise use content
        content = node.annotations.get('description', node.content)
        
        # Build the line based on node type
        if node.node_type == 'functional_concept':
            line = f"{indent}<= {content}"
        elif node.node_type == 'value_concept':
            line = f"{indent}<- {content}"
        elif node.node_type == 'output_concept':
            line = f"{indent}{content}"
        else:
            line = f"{indent}{content}"
        
        lines.append(line)
        
        # Serialize children
        for child in node.children:
            cls._serialize_node(child, lines)

```

```python
"""
NormCode Format Converters

Provides bidirectional conversion between .ncd, .nc, and .ncn formats.
"""

from .format_converter import FormatConverter

__all__ = ['FormatConverter']

```

```python
"""
Format Converter for NormCode Files

Provides bidirectional conversion between .ncd, .nc, and .ncn formats
using the common IR (Intermediate Representation).
"""

from typing import List, Tuple
from ..parsers import NCDParser, NCParser, NCNParser, NormCodeNode


class FormatConverter:
    """Bidirectional converter between NormCode formats."""
    
    @classmethod
    def ncd_to_nc(cls, ncd_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncd to .nc format.
        
        Args:
            ncd_content: Content of .ncd file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncd to IR
        nodes = NCDParser.parse(ncd_content)
        
        # Check for lossy conversions
        warnings.extend(cls._check_ncd_to_nc_warnings(nodes))
        
        # Ensure flow indices are present
        nodes = cls._ensure_flow_indices(nodes)
        
        # Serialize to .nc
        nc_content = NCParser.serialize(nodes)
        
        return nc_content, warnings
    
    @classmethod
    def nc_to_ncd(cls, nc_content: str) -> Tuple[str, List[str]]:
        """
        Convert .nc to .ncd format.
        
        Args:
            nc_content: Content of .nc file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .nc to IR
        nodes = NCParser.parse(nc_content)
        
        # Serialize to .ncd
        ncd_content = NCDParser.serialize(nodes)
        
        warnings.append("Note: .nc to .ncd conversion may lose type details")
        
        return ncd_content, warnings
    
    @classmethod
    def ncd_to_ncn(cls, ncd_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncd to .ncn format.
        
        Args:
            ncd_content: Content of .ncd file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncd to IR
        nodes = NCDParser.parse(ncd_content)
        
        # Convert annotations to natural language descriptions
        nodes = cls._convert_to_natural_language(nodes)
        
        # Serialize to .ncn
        ncn_content = NCNParser.serialize(nodes)
        
        warnings.append("Converted to natural language format")
        
        return ncn_content, warnings
    
    @classmethod
    def ncn_to_ncd(cls, ncn_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncn to .ncd format.
        
        Args:
            ncn_content: Content of .ncn file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncn to IR
        nodes = NCNParser.parse(ncn_content)
        
        # Serialize to .ncd
        ncd_content = NCDParser.serialize(nodes)
        
        warnings.append("Warning: .ncn to .ncd may lose formal syntax details")
        
        return ncd_content, warnings
    
    @classmethod
    def nc_to_ncn(cls, nc_content: str) -> Tuple[str, List[str]]:
        """
        Convert .nc to .ncn format.
        
        Args:
            nc_content: Content of .nc file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .nc to IR
        nodes = NCParser.parse(nc_content)
        
        # Convert to natural language
        nodes = cls._convert_to_natural_language(nodes)
        
        # Serialize to .ncn
        ncn_content = NCNParser.serialize(nodes)
        
        warnings.append("Converted to natural language format")
        
        return ncn_content, warnings
    
    @classmethod
    def ncn_to_nc(cls, ncn_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncn to .nc format.
        
        Args:
            ncn_content: Content of .ncn file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncn to IR
        nodes = NCNParser.parse(ncn_content)
        
        # Ensure flow indices
        nodes = cls._ensure_flow_indices(nodes)
        
        # Serialize to .nc
        nc_content = NCParser.serialize(nodes)
        
        warnings.append("Warning: .ncn to .nc may lose natural language nuances")
        
        return nc_content, warnings
    
    # Helper methods
    
    @classmethod
    def _check_ncd_to_nc_warnings(cls, nodes: List[NormCodeNode]) -> List[str]:
        """Check for potential lossy conversions from .ncd to .nc."""
        warnings = []
        
        def check_node(node: NormCodeNode):
            # Check for annotations that might be lost
            if node.annotations:
                if 'question' in node.annotations:
                    warnings.append(f"Question annotation will be lost: {node.annotations['question'][:50]}...")
                if 'source_text' in node.annotations:
                    warnings.append(f"Source text annotation will be lost: {node.annotations['source_text'][:50]}...")
            
            # Check children
            for child in node.children:
                check_node(child)
        
        for node in nodes:
            check_node(node)
        
        return list(set(warnings))[:5]  # Limit to 5 unique warnings
    
    @classmethod
    def _ensure_flow_indices(cls, nodes: List[NormCodeNode], parent_index: str = "") -> List[NormCodeNode]:
        """
        Ensure all nodes have flow indices.
        
        Generates indices like 1, 1.1, 1.2, 1.2.1, etc.
        """
        for i, node in enumerate(nodes, 1):
            if parent_index:
                node.flow_index = f"{parent_index}.{i}"
            else:
                node.flow_index = str(i)
            
            # Recursively ensure indices for children
            if node.children:
                cls._ensure_flow_indices(node.children, node.flow_index)
        
        return nodes
    
    @classmethod
    def _convert_to_natural_language(cls, nodes: List[NormCodeNode]) -> List[NormCodeNode]:
        """
        Convert formal syntax to natural language descriptions.
        
        This is a simplified conversion that uses available annotations
        or content to create readable descriptions.
        """
        def convert_node(node: NormCodeNode):
            # Use description annotation if available
            if 'description' in node.annotations:
                node.content = node.annotations['description']
            
            # Convert children
            for child in node.children:
                convert_node(child)
        
        for node in nodes:
            convert_node(node)
        
        return nodes

```

```python
"""
Version Control System for NormCode Files

Provides version history, rollback, and diff capabilities for NormCode files.
"""

import sqlite3
import hashlib
import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Version:
    """Represents a version snapshot."""
    id: str
    file_path: str
    content: str
    timestamp: str
    message: str
    hash: str


class VersionControl:
    """Version control system for NormCode files."""
    
    def __init__(self, db_path: str = "data/normcode_versions.db"):
        """
        Initialize version control system.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Get the streamlit_app directory
        script_dir = Path(__file__).parent.parent
        self.db_path = script_dir / db_path
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL,
                hash TEXT NOT NULL
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path 
            ON versions(file_path, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_snapshot(
        self, 
        file_path: str, 
        content: str, 
        message: str = "Manual save"
    ) -> str:
        """
        Save a snapshot of file content.
        
        Args:
            file_path: Path to the file
            content: File content
            message: Commit message
            
        Returns:
            Version ID
        """
        # Generate version ID and hash
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        version_id = f"{content_hash[:8]}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO versions (id, file_path, content, timestamp, message, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (version_id, file_path, content, timestamp, message, content_hash))
        
        conn.commit()
        conn.close()
        
        return version_id
    
    def get_history(self, file_path: str, limit: int = 50) -> List[Version]:
        """
        Get version history for a file.
        
        Args:
            file_path: Path to the file
            limit: Maximum number of versions to return
            
        Returns:
            List of Version objects, newest first
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, file_path, content, timestamp, message, hash
            FROM versions
            WHERE file_path = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (file_path, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        versions = [
            Version(
                id=row[0],
                file_path=row[1],
                content=row[2],
                timestamp=row[3],
                message=row[4],
                hash=row[5]
            )
            for row in rows
        ]
        
        return versions
    
    def get_version(self, version_id: str) -> Optional[Version]:
        """
        Get a specific version by ID.
        
        Args:
            version_id: Version ID
            
        Returns:
            Version object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, file_path, content, timestamp, message, hash
            FROM versions
            WHERE id = ?
        """, (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Version(
            id=row[0],
            file_path=row[1],
            content=row[2],
            timestamp=row[3],
            message=row[4],
            hash=row[5]
        )
    
    def rollback(self, file_path: str, version_id: str) -> str:
        """
        Rollback to a specific version.
        
        This creates a new version with the old content.
        
        Args:
            file_path: Path to the file
            version_id: Version ID to rollback to
            
        Returns:
            New version ID
        """
        # Get the target version
        target_version = self.get_version(version_id)
        
        if not target_version:
            raise ValueError(f"Version not found: {version_id}")
        
        if target_version.file_path != file_path:
            raise ValueError("Version does not belong to this file")
        
        # Create a new snapshot with the old content
        message = f"Rollback to version {version_id[:8]}"
        new_version_id = self.save_snapshot(file_path, target_version.content, message)
        
        return new_version_id
    
    def diff(
        self, 
        file_path: str, 
        version1_id: Optional[str] = None, 
        version2_id: Optional[str] = None,
        content1: Optional[str] = None,
        content2: Optional[str] = None
    ) -> str:
        """
        Generate a unified diff between two versions or content.
        
        Args:
            file_path: Path to the file
            version1_id: First version ID (or None to use content1)
            version2_id: Second version ID (or None to use content2)
            content1: First content (if version1_id is None)
            content2: Second content (if version2_id is None)
            
        Returns:
            Unified diff string
        """
        # Get content for version 1
        if version1_id:
            v1 = self.get_version(version1_id)
            if not v1:
                raise ValueError(f"Version not found: {version1_id}")
            text1 = v1.content
            label1 = f"Version {version1_id[:8]}"
        elif content1 is not None:
            text1 = content1
            label1 = "Current"
        else:
            raise ValueError("Must provide either version1_id or content1")
        
        # Get content for version 2
        if version2_id:
            v2 = self.get_version(version2_id)
            if not v2:
                raise ValueError(f"Version not found: {version2_id}")
            text2 = v2.content
            label2 = f"Version {version2_id[:8]}"
        elif content2 is not None:
            text2 = content2
            label2 = "New"
        else:
            raise ValueError("Must provide either version2_id or content2")
        
        # Generate unified diff
        diff = difflib.unified_diff(
            text1.splitlines(keepends=True),
            text2.splitlines(keepends=True),
            fromfile=label1,
            tofile=label2,
            lineterm=''
        )
        
        return ''.join(diff)
    
    def get_file_versions_count(self, file_path: str) -> int:
        """
        Get the number of versions for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of versions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM versions WHERE file_path = ?
        """, (file_path,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def delete_file_versions(self, file_path: str) -> int:
        """
        Delete all versions for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of versions deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM versions WHERE file_path = ?
        """, (file_path,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

```

```python
"""
Syntax Highlighter for NormCode Files

Provides syntax highlighting for .ncd, .nc, and .ncn file formats.
"""

import re
from typing import List, Tuple


class SyntaxHighlighter:
    """Syntax highlighter for NormCode formats."""
    
    # Color scheme
    COLORS = {
        'operator': '#ff79c6',  # Pink
        'concept': '#8be9fd',   # Cyan
        'keyword': '#bd93f9',   # Purple
        'string': '#f1fa8c',    # Yellow
        'comment': '#6272a4',   # Gray
        'annotation': '#50fa7b', # Green
        'flow_index': '#ffb86c', # Orange
        'sequence_type': '#ff5555' # Red
    }
    
    @classmethod
    def highlight_ncd(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .ncd format.
        
        Args:
            content: .ncd file content
            
        Returns:
            HTML string with syntax highlighting
        """
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            highlighted = cls._highlight_ncd_line(line)
            highlighted_lines.append(highlighted)
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def _highlight_ncd_line(cls, line: str) -> str:
        """Highlight a single .ncd line."""
        if not line.strip():
            return line
        
        # Preserve leading whitespace
        leading_spaces = len(line) - len(line.lstrip())
        indent = line[:leading_spaces]
        content = line[leading_spaces:]
        
        # Check for annotations first
        if content.startswith('?:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">?:</span>{cls._escape_html(content[2:])}'
        elif content.startswith('/:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">/:< /span>{cls._escape_html(content[2:])}'
        elif content.startswith('...:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">...:</span>{cls._escape_html(content[4:])}'
        
        # Highlight operators
        if content.startswith('<='):
            op_color = cls.COLORS['operator']
            rest = content[2:].strip()
            result = f'{indent}<span style="color: {op_color}">&lt;=</span> '
            result += cls._highlight_concept_content(rest)
            return result
        elif content.startswith('<-'):
            op_color = cls.COLORS['operator']
            rest = content[2:].strip()
            result = f'{indent}<span style="color: {op_color}">&lt;-</span> '
            result += cls._highlight_concept_content(rest)
            return result
        elif content.startswith(':<:'):
            op_color = cls.COLORS['operator']
            rest = content[3:]
            result = f'{indent}<span style="color: {op_color}">:&lt;:</span>'
            result += cls._highlight_concept_content(rest)
            return result
        
        # Default: highlight any concept syntax
        return indent + cls._highlight_concept_content(content)
    
    @classmethod
    def _highlight_concept_content(cls, content: str) -> str:
        """Highlight concept syntax within content."""
        # Split by | to separate metadata
        if '|' in content:
            parts = content.split('|', 1)
            concept_part = parts[0]
            metadata_part = parts[1] if len(parts) > 1 else ""
            
            highlighted = cls._highlight_concept_syntax(concept_part)
            
            if metadata_part:
                # Highlight flow index
                flow_match = re.match(r'^\s*([\d.]+)', metadata_part)
                if flow_match:
                    flow_idx = flow_match.group(1)
                    color = cls.COLORS['flow_index']
                    highlighted += f' <span style="color: {color}">| {flow_idx}</span>'
                    rest = metadata_part[flow_match.end():]
                    
                    # Highlight sequence type
                    seq_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
                    for seq in seq_types:
                        if seq in rest:
                            color = cls.COLORS['sequence_type']
                            rest = rest.replace(seq, f'<span style="color: {color}">{seq}</span>')
                            break
                    
                    highlighted += rest
                else:
                    highlighted += ' | ' + cls._escape_html(metadata_part)
            
            return highlighted
        else:
            return cls._highlight_concept_syntax(content)
    
    @classmethod
    def _highlight_concept_syntax(cls, content: str) -> str:
        """Highlight concept bracket syntax."""
        # Highlight {} [] <> :: etc.
        result = content
        
        # Concept brackets
        result = re.sub(r'(\{[^}]*\})', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{cls._escape_html(m.group(1))}</span>', result)
        result = re.sub(r'(\[[^\]]*\])', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{cls._escape_html(m.group(1))}</span>', result)
        result = re.sub(r'(&lt;[^&gt;]*&gt;)', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{m.group(1)}</span>', result)
        
        # Operators
        result = re.sub(r'(::|\$=|\$\.|\$%|\$\+|@if|@if!|@after|@by|&in|&across|\*every)', 
                       lambda m: f'<span style="color: {cls.COLORS["keyword"]}">{cls._escape_html(m.group(1))}</span>', result)
        
        return result
    
    @classmethod
    def highlight_nc(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .nc format.
        
        Args:
            content: .nc file content
            
        Returns:
            HTML string with syntax highlighting
        """
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            if not line.strip():
                highlighted_lines.append(line)
                continue
            
            # Format: flow_index.type|content
            if '|' in line:
                parts = line.split('|', 1)
                metadata = parts[0]
                content_part = parts[1] if len(parts) > 1 else ""
                
                # Highlight flow index
                flow_color = cls.COLORS['flow_index']
                type_color = cls.COLORS['sequence_type']
                
                highlighted = f'<span style="color: {flow_color}">{cls._escape_html(metadata)}</span>'
                highlighted += '<span style="color: ' + cls.COLORS['operator'] + '">|</span>'
                highlighted += cls._highlight_concept_syntax(content_part)
                
                highlighted_lines.append(highlighted)
            else:
                highlighted_lines.append(cls._escape_html(line))
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def highlight_ncn(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .ncn format.
        
        Args:
            content: .ncn file content
            
        Returns:
            HTML string with syntax highlighting
        """
        # .ncn is similar to .ncd but with natural language
        # Use simplified highlighting
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            if not line.strip():
                highlighted_lines.append(line)
                continue
            
            # Preserve leading whitespace
            leading_spaces = len(line) - len(line.lstrip())
            indent = line[:leading_spaces]
            content_part = line[leading_spaces:]
            
            # Highlight operators
            if content_part.startswith('<='):
                op_color = cls.COLORS['operator']
                rest = content_part[2:].strip()
                highlighted = f'{indent}<span style="color: {op_color}">&lt;=</span> {cls._escape_html(rest)}'
            elif content_part.startswith('<-'):
                op_color = cls.COLORS['operator']
                rest = content_part[2:].strip()
                highlighted = f'{indent}<span style="color: {op_color}">&lt;-</span> {cls._escape_html(rest)}'
            elif content_part.startswith(':<:'):
                op_color = cls.COLORS['operator']
                rest = content_part[3:]
                highlighted = f'{indent}<span style="color: {op_color}">:&lt;:</span>{cls._escape_html(rest)}'
            else:
                highlighted = indent + cls._escape_html(content_part)
            
            highlighted_lines.append(highlighted)
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def _escape_html(cls, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @classmethod
    def get_css(cls) -> str:
        """Get custom CSS for syntax highlighting."""
        return """
        <style>
        .normcode-editor {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            background-color: #282a36;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .normcode-editor pre {
            margin: 0;
            padding: 0;
        }
        </style>
        """

```

```python
"""
NormCode Files Editor Tab

Provides UI for editing .ncd, .nc, and .ncn files with bidirectional sync
and version control.
"""

import streamlit as st
from pathlib import Path
import os

# Import core functionality
import sys
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.manifest import ManifestManager
from core.version_control import VersionControl
from core.syntax_highlighter import SyntaxHighlighter
from core.converters import FormatConverter


def render_normcode_editor_tab():
    """Render the NormCode files editor tab."""
    st.header("📝 NormCode Files Editor")
    st.markdown("Edit .ncd, .nc, and .ncn files with bidirectional synchronization and version control.")
    
    # Initialize session state
    if 'nc_editor_manifest' not in st.session_state:
        st.session_state.nc_editor_manifest = None
    if 'nc_editor_current_file' not in st.session_state:
        st.session_state.nc_editor_current_file = 'draft'
    if 'nc_editor_content' not in st.session_state:
        st.session_state.nc_editor_content = {'draft': '', 'formal': '', 'natural': ''}
    if 'nc_editor_modified' not in st.session_state:
        st.session_state.nc_editor_modified = {'draft': False, 'formal': False, 'natural': False}
    if 'nc_sync_preview' not in st.session_state:
        st.session_state.nc_sync_preview = None
    
    # Initialize managers
    manifest_mgr = ManifestManager()
    version_ctrl = VersionControl()
    
    # Project Management Section
    st.subheader("Project Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Load existing manifest
        available_manifests = manifest_mgr.list_manifests()
        
        if available_manifests:
            selected_manifest = st.selectbox(
                "Load Existing Project",
                options=[''] + available_manifests,
                key='nc_manifest_selector'
            )
            
            if selected_manifest and st.button("Load Project"):
                manifest = manifest_mgr.load(selected_manifest)
                if manifest:
                    st.session_state.nc_editor_manifest = manifest
                    # Load file contents
                    _load_manifest_files(manifest, st.session_state.nc_editor_content)
                    st.success(f"Loaded project: {selected_manifest}")
                    st.rerun()
        else:
            st.info("No projects found. Create a new one below.")
    
    with col2:
        if st.button("➕ Create New"):
            st.session_state.nc_show_create_form = True
    
    with col3:
        if st.session_state.nc_editor_manifest and st.button("💾 Save Manifest"):
            manifest_mgr.save(st.session_state.nc_editor_manifest)
            st.success("Manifest saved!")
    
    # Create new project form
    if st.session_state.get('nc_show_create_form', False):
        with st.expander("Create New Project", expanded=True):
            project_name = st.text_input("Project Name", key='nc_new_project_name')
            description = st.text_area("Description (optional)", key='nc_new_project_desc')
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Create"):
                    if project_name:
                        # Create manifest with placeholder paths
                        manifest = manifest_mgr.create(
                            project_name=project_name,
                            draft_path=f"{project_name}.ncd",
                            formal_path=f"{project_name}.nc",
                            natural_path=f"{project_name}.ncn",
                            description=description
                        )
                        st.session_state.nc_editor_manifest = manifest
                        st.session_state.nc_show_create_form = False
                        st.success(f"Created project: {project_name}")
                        st.rerun()
            with col_b:
                if st.button("Cancel"):
                    st.session_state.nc_show_create_form = False
                    st.rerun()
    
    # Only show editor if a manifest is loaded
    if not st.session_state.nc_editor_manifest:
        st.info("👆 Load or create a project to get started")
        return
    
    manifest = st.session_state.nc_editor_manifest
    
    # Display current project info
    st.divider()
    st.markdown(f"**Current Project:** {manifest['project_name']}")
    if manifest['metadata'].get('description'):
        st.caption(manifest['metadata']['description'])
    
    # File selector tabs
    st.subheader("File Editor")
    
    file_tabs = st.tabs(["📄 .ncd (Draft)", "📋 .nc (Formal)", "📖 .ncn (Natural)"])
    
    file_types = ['draft', 'formal', 'natural']
    file_extensions = ['.ncd', '.nc', '.ncn']
    
    for i, (tab, file_type, ext) in enumerate(zip(file_tabs, file_types, file_extensions)):
        with tab:
            _render_file_editor(
                file_type=file_type,
                extension=ext,
                manifest=manifest,
                version_ctrl=version_ctrl
            )
    
    # Sync Panel
    st.divider()
    st.subheader("Synchronization")
    
    col_sync1, col_sync2, col_sync3, col_sync4 = st.columns(4)
    
    with col_sync1:
        if st.button("🔄 .ncd → .nc"):
            _sync_files('draft', 'formal', manifest, version_ctrl)
    
    with col_sync2:
        if st.button("🔄 .ncd → .ncn"):
            _sync_files('draft', 'natural', manifest, version_ctrl)
    
    with col_sync3:
        if st.button("🔄 .nc → .ncd"):
            _sync_files('formal', 'draft', manifest, version_ctrl)
    
    with col_sync4:
        if st.button("🔄 .ncn → .ncd"):
            _sync_files('natural', 'draft', manifest, version_ctrl)
    
    # Show sync preview if active
    if st.session_state.nc_sync_preview:
        _show_sync_preview(version_ctrl)


def _render_file_editor(file_type: str, extension: str, manifest: dict, version_ctrl: VersionControl):
    """Render editor for a specific file type."""
    file_path = manifest['files'][file_type]
    
    # File info
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.caption(f"📁 {file_path}")
    with col_info2:
        if st.session_state.nc_editor_modified.get(file_type, False):
            st.caption("⚠️ Modified")
    
    # Editor
    content = st.session_state.nc_editor_content.get(file_type, '')
    
    new_content = st.text_area(
        "Content",
        value=content,
        height=400,
        key=f'nc_editor_{file_type}',
        label_visibility='collapsed'
    )
    
    # Track modifications
    if new_content != content:
        st.session_state.nc_editor_content[file_type] = new_content
        st.session_state.nc_editor_modified[file_type] = True
    
    # Syntax highlighting preview
    with st.expander("🎨 Syntax Highlight Preview"):
        if extension == '.ncd':
            highlighted = SyntaxHighlighter.highlight_ncd(new_content)
        elif extension == '.nc':
            highlighted = SyntaxHighlighter.highlight_nc(new_content)
        else:
            highlighted = SyntaxHighlighter.highlight_ncn(new_content)
        
        st.markdown(highlighted, unsafe_allow_html=True)
    
    # Actions
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("💾 Save", key=f'nc_save_{file_type}'):
            _save_file(file_type, file_path, new_content, version_ctrl)
            st.session_state.nc_editor_modified[file_type] = False
            st.success(f"Saved {extension} file")
    
    with col_act2:
        if st.button("📜 View History", key=f'nc_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = True
    
    with col_act3:
        if st.button("📥 Load from File", key=f'nc_load_{file_type}'):
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_content = f.read()
                st.session_state.nc_editor_content[file_type] = loaded_content
                st.success(f"Loaded from {file_path}")
                st.rerun()
    
    # Version history viewer
    if st.session_state.get(f'nc_show_history_{file_type}', False):
        with st.expander("📜 Version History", expanded=True):
            _show_version_history(file_type, file_path, version_ctrl)
            
            if st.button("Close History", key=f'nc_close_history_{file_type}'):
                st.session_state[f'nc_show_history_{file_type}'] = False
                st.rerun()


def _save_file(file_type: str, file_path: str, content: str, version_ctrl: VersionControl):
    """Save file and create version snapshot."""
    # Save to disk
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create version snapshot
    message = st.session_state.get(f'nc_commit_msg_{file_type}', 'Manual save')
    version_ctrl.save_snapshot(file_path, content, message)


def _load_manifest_files(manifest: dict, content_dict: dict):
    """Load file contents from manifest."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content_dict[file_type] = f.read()
        else:
            content_dict[file_type] = ''


def _sync_files(source_type: str, target_type: str, manifest: dict, version_ctrl: VersionControl):
    """Sync content from source file type to target file type."""
    source_content = st.session_state.nc_editor_content.get(source_type, '')
    
    if not source_content:
        st.warning(f"Source file is empty")
        return
    
    # Determine conversion function
    ext_map = {'draft': 'ncd', 'formal': 'nc', 'natural': 'ncn'}
    source_ext = ext_map[source_type]
    target_ext = ext_map[target_type]
    
    conversion_key = f"{source_ext}_to_{target_ext}"
    
    # Perform conversion
    try:
        if conversion_key == "ncd_to_nc":
            converted, warnings = FormatConverter.ncd_to_nc(source_content)
        elif conversion_key == "ncd_to_ncn":
            converted, warnings = FormatConverter.ncd_to_ncn(source_content)
        elif conversion_key == "nc_to_ncd":
            converted, warnings = FormatConverter.nc_to_ncd(source_content)
        elif conversion_key == "ncn_to_ncd":
            converted, warnings = FormatConverter.ncn_to_ncd(source_content)
        elif conversion_key == "nc_to_ncn":
            converted, warnings = FormatConverter.nc_to_ncn(source_content)
        elif conversion_key == "ncn_to_nc":
            converted, warnings = FormatConverter.ncn_to_nc(source_content)
        else:
            st.error(f"Unsupported conversion: {conversion_key}")
            return
        
        # Store sync preview
        st.session_state.nc_sync_preview = {
            'source_type': source_type,
            'target_type': target_type,
            'source_content': source_content,
            'target_content': converted,
            'warnings': warnings,
            'current_target': st.session_state.nc_editor_content.get(target_type, '')
        }
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Conversion error: {str(e)}")


def _show_sync_preview(version_ctrl: VersionControl):
    """Show sync preview with diff."""
    preview = st.session_state.nc_sync_preview
    
    st.subheader("🔍 Sync Preview")
    
    # Show warnings
    if preview['warnings']:
        for warning in preview['warnings']:
            st.warning(warning)
    
    # Show diff
    col_diff1, col_diff2 = st.columns(2)
    
    with col_diff1:
        st.caption(f"Current {preview['target_type']} content")
        st.code(preview['current_target'][:500] + ('...' if len(preview['current_target']) > 500 else ''))
    
    with col_diff2:
        st.caption(f"New content from {preview['source_type']}")
        st.code(preview['target_content'][:500] + ('...' if len(preview['target_content']) > 500 else ''))
    
    # Diff view
    with st.expander("📊 Detailed Diff"):
        diff = version_ctrl.diff(
            file_path="temp",
            content1=preview['current_target'],
            content2=preview['target_content']
        )
        st.code(diff, language='diff')
    
    # Actions
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("✅ Apply Changes"):
            st.session_state.nc_editor_content[preview['target_type']] = preview['target_content']
            st.session_state.nc_editor_modified[preview['target_type']] = True
            st.session_state.nc_sync_preview = None
            st.success("Changes applied!")
            st.rerun()
    
    with col_act2:
        if st.button("❌ Cancel"):
            st.session_state.nc_sync_preview = None
            st.rerun()


def _show_version_history(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Show version history for a file."""
    versions = version_ctrl.get_history(file_path, limit=20)
    
    if not versions:
        st.info("No version history yet")
        return
    
    st.caption(f"📊 {len(versions)} version(s) found")
    
    for version in versions:
        with st.container():
            col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
            
            with col_v1:
                st.caption(f"🕒 {version.timestamp[:19]}")
            
            with col_v2:
                st.caption(f"💬 {version.message}")
            
            with col_v3:
                if st.button("Restore", key=f'nc_restore_{version.id}'):
                    st.session_state.nc_editor_content[file_type] = version.content
                    st.success(f"Restored version {version.id[:8]}")
                    st.rerun()

```

```python
"""
Tab modules for NormCode Orchestrator Streamlit App.
"""

# Use the refactored execute tab (now organized in execute/ package)
from .execute import render_execute_tab

# Use the refactored results tab (now organized in results/ package)
from .results import render_results_tab

from .history_tab import render_history_tab
from .help_tab import render_help_tab
from .sandbox_tab import render_sandbox_tab
from .paradigms import render_paradigms_tab
from .normcode_editor_tab import render_normcode_editor_tab

__all__ = [
    'render_execute_tab',
    'render_results_tab',
    'render_history_tab',
    'render_help_tab',
    'render_sandbox_tab',
    'render_paradigms_tab',
    'render_normcode_editor_tab'
]


```

```python
"""
NormCode Orchestrator - Streamlit App

A minimal web interface for running the NormCode orchestration engine.
Upload repository JSON files, configure execution parameters, and view results.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path (app is in streamlit_app/, need to go up one level)
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import refactored modules (need to be relative or package imports)
# Since we're in streamlit_app/app.py, we can use direct imports if streamlit_app is a package
# Or use sys.path manipulation to make local imports work
import os
import sys

# Add streamlit_app directory to path for clean imports
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core import init_session_state
from ui import apply_custom_styling, render_main_header, render_footer, render_sidebar
from tabs import render_execute_tab, render_results_tab, render_history_tab, render_help_tab, render_sandbox_tab, render_paradigms_tab, render_normcode_editor_tab

# Configure page
st.set_page_config(
    page_title="NormCode Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_custom_styling()

# Initialize session state
init_session_state()

# Render sidebar and get configuration
config = render_sidebar()

# Render main header
render_main_header()

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚀 Execute", "📊 Results", "📜 History", "🧪 Sandbox", "🎨 Paradigms", "📖 Help"])

# Render tabs
with tab1:
    render_execute_tab(config)

with tab2:
    render_results_tab(config['db_path'])

with tab3:
    render_history_tab(config['db_path'])

with tab4:
    render_sandbox_tab()

with tab5:
    render_paradigms_tab()

with tab6:
    render_help_tab()

# Render footer
render_footer()

```

```python
"""
NormCode Orchestrator - Streamlit App

A minimal web interface for running the NormCode orchestration engine.
Upload repository JSON files, configure execution parameters, and view results.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path (app is in streamlit_app/, need to go up one level)
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import refactored modules (need to be relative or package imports)
# Since we're in streamlit_app/app.py, we can use direct imports if streamlit_app is a package
# Or use sys.path manipulation to make local imports work
import os
import sys

# Add streamlit_app directory to path for clean imports
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core import init_session_state
from ui import apply_custom_styling, render_main_header, render_footer, render_sidebar
from tabs import render_execute_tab, render_results_tab, render_history_tab, render_help_tab, render_sandbox_tab, render_paradigms_tab, render_normcode_editor_tab

# Configure page
st.set_page_config(
    page_title="NormCode Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_custom_styling()

# Initialize session state
init_session_state()

# Render sidebar and get configuration
config = render_sidebar()

# Render main header
render_main_header()

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🚀 Execute", "📊 Results", "📜 History", "🧪 Sandbox", "🎨 Paradigms", "📝 NormCode Files", "📖 Help"])

# Render tabs
with tab1:
    render_execute_tab(config)

with tab2:
    render_results_tab(config['db_path'])

with tab3:
    render_history_tab(config['db_path'])

with tab4:
    render_sandbox_tab()

with tab5:
    render_paradigms_tab()

with tab6:
    render_normcode_editor_tab()

with tab7:
    render_help_tab()

# Render footer
render_footer()

```

```markdown
# NormCode Files Editor Tab

## Overview

The NormCode Files Editor is a new tab in the Streamlit app that provides a sophisticated interface for editing `.ncd`, `.nc`, and `.ncn` files with bidirectional synchronization, manifest-based file linking, and version control.

## Features

### 1. **Project Management**
- Create new projects with manifest files
- Load existing projects from saved manifests
- Link related `.ncd`, `.nc`, and `.ncn` files together
- Save project configurations

### 2. **Multi-Format Editing**
- Edit `.ncd` (NormCode Draft) files with full syntax support
- Edit `.nc` (NormCode Formal) files
- Edit `.ncn` (NormCode Natural) files
- Switch between formats using tabs
- Track modifications for each file

### 3. **Syntax Highlighting**
- Color-coded syntax highlighting for each format
- Preview mode to see highlighted content
- Support for:
  - Operators (`<=`, `<-`, `::`, `&in`, etc.)
  - Concepts (`{}`, `[]`, `<>`)
  - Annotations (`?:`, `/:`, `...:`)
  - Flow indices and sequence types

### 4. **Bidirectional Format Conversion**
- Convert between any two formats:
  - `.ncd` ↔ `.nc`
  - `.ncd` ↔ `.ncn`
  - `.nc` ↔ `.ncn`
- Preview changes before applying
- View detailed diffs
- Warnings for lossy conversions

### 5. **Version Control**
- Automatic version snapshots on save
- View version history for each file
- Restore previous versions
- Diff between versions
- SQLite-based storage

## Architecture

### Core Components

1. **`streamlit_app/core/manifest.py`**
   - `ManifestManager` class for managing project manifests
   - Create, load, save, update, and delete manifests
   - Validates manifest structure

2. **`streamlit_app/core/parsers/`**
   - `ir.py`: Common intermediate representation (`NormCodeNode`)
   - `ncd_parser.py`: Parse/serialize `.ncd` format
   - `nc_parser.py`: Parse/serialize `.nc` format
   - `ncn_parser.py`: Parse/serialize `.ncn` format

3. **`streamlit_app/core/converters/`**
   - `format_converter.py`: Bidirectional format conversion
   - Uses parsers to convert between formats
   - Provides warnings for lossy conversions

4. **`streamlit_app/core/version_control.py`**
   - `VersionControl` class for version management
   - SQLite database storage
   - Snapshot, history, rollback, and diff functionality

5. **`streamlit_app/core/syntax_highlighter.py`**
   - `SyntaxHighlighter` class for syntax highlighting
   - HTML generation with inline styles
   - Format-specific highlighting rules

6. **`streamlit_app/tabs/normcode_editor_tab.py`**
   - Main UI component
   - Project management interface
   - File editors with tabs
   - Sync preview with diff viewer

## Usage

### Creating a New Project

1. Navigate to the "📝 NormCode Files" tab
2. Click "➕ Create New"
3. Enter a project name and optional description
4. Click "Create"
5. The manifest will be created with placeholder file paths

### Loading an Existing Project

1. Select a project from the dropdown
2. Click "Load Project"
3. Files will be loaded if they exist at the specified paths

### Editing Files

1. Use the file tabs to switch between `.ncd`, `.nc`, and `.ncn`
2. Edit content in the text area
3. Preview syntax highlighting in the expander
4. Click "💾 Save" to save changes and create a version snapshot

### Synchronizing Files

1. Make changes to one file (e.g., `.ncd`)
2. Click a sync button (e.g., "🔄 .ncd → .nc")
3. Review the preview with warnings and diff
4. Click "✅ Apply Changes" to update the target file
5. Save the target file when ready

### Version Control

1. Click "📜 View History" for any file
2. Browse previous versions with timestamps
3. Click "Restore" to load a previous version
4. Use the diff viewer to compare versions

## Data Storage

### Manifests
- Stored in: `streamlit_app/data/manifests/`
- Format: `{project_name}.json`
- Contains file paths and metadata

### Version History
- Stored in: `streamlit_app/data/normcode_versions.db` (SQLite)
- Schema:
  - `id`: Unique version ID
  - `file_path`: Path to file
  - `content`: File content snapshot
  - `timestamp`: When snapshot was created
  - `message`: Commit message
  - `hash`: SHA256 hash of content

## File Formats

### .ncd (NormCode Draft)
- Indentation-based hierarchy (4 spaces per level)
- Annotations: `?:`, `/:`, `...:`
- Operators: `<=`, `<-`, `:<:`
- Metadata: `| flow_index sequence_type`

### .nc (NormCode Formal)
- Line-based format
- Format: `flow_index.type|content`
- No annotations
- Machine-readable

### .ncn (NormCode Natural)
- Similar to `.ncd` but with natural language
- Simplified content
- Easier for human reading

## Integration

The NormCode Files editor is integrated into the main Streamlit app:

1. **`streamlit_app/app.py`**: Imports and renders the tab
2. **`streamlit_app/tabs/__init__.py`**: Exports the render function

## Future Enhancements

- Auto-complete for NormCode operators
- Visual graph view of flow structure
- Integration with translation pipeline (normtext → .ncd)
- Export to Python repository format (JSON)
- Collaborative editing with conflict resolution
- Real-time collaboration
- Import from existing files
- Batch operations

## Technical Notes

### Parser Complexity
The `.ncd` parser handles indentation-based parsing with care for whitespace preservation.

### Lossy Conversions
Some conversions lose information:
- `.ncd` → `.nc`: Loses annotations (`?:`, `/:`, `...:`)
- `.ncn` → `.nc`: Loses natural language nuances
- `.nc` → `.ncd`: May lose type details

The system provides warnings for these cases.

### Performance
- Large files (>10MB) may need optimization
- Consider streaming/chunking for very large files
- SQLite provides fast version retrieval

## Troubleshooting

### Files Not Loading
- Check that file paths in manifest are correct
- Ensure files exist at specified locations
- Try using absolute paths

### Sync Not Working
- Ensure source file has content
- Check console for error messages
- Verify file format is valid

### Version History Empty
- Save the file at least once to create first snapshot
- Check that database file exists at `data/normcode_versions.db`

## Support

For issues or questions, consult the main project documentation or review the source code in `streamlit_app/tabs/normcode_editor_tab.py`.

```

```json
{
  "project_name": "example_project",
  "created": "2025-12-04T14:00:00",
  "files": {
    "draft": "examples/example.ncd",
    "formal": "examples/example.nc",
    "natural": "examples/example.ncn"
  },
  "metadata": {
    "description": "Example NormCode project demonstrating the file format",
    "version": "1.0"
  }
}

```

```plaintext
:<:({result}) | 1. assigning
    ?: What is the result?
    <= $.({number})
    <- {number a} | 1.1. imperative
        /: The first number
    <- {number b} | 1.2. imperative
        /: The second number
    <- {sum} | 1.3. imperative
        <= ::(add {1}<$({number a})%_> and {2}<$({number b})%_> to get {3}?<$({sum})%_>)
        <- {number a}<:{1}>
        <- {number b}<:{2}>
        <- {sum}?<:{3}>

```

```plaintext
1.output|:<:({result})
1.1.assigning|<= $.({number})
1.2.object|<- {number a}
1.3.object|<- {number b}
1.4.imperative|<- {sum}
1.4.1.imperative|<= ::(add {1}<$({number a})%_> and {2}<$({number b})%_> to get {3}?<$({sum})%_>)
1.4.2.object|<- {number a}<:{1}>
1.4.3.object|<- {number b}<:{2}>
1.4.4.object|<- {sum}?<:{3}>

```

```plaintext
:<: The result is calculated.
    <= This is accomplished by a defined method.
    <- The first number is number a.
    <- The second number is number b.
    <- The sum is calculated.
        <= Add number a and number b to get the sum.
        <- Use number a as the first input.
        <- Use number b as the second input.
        <- Store the result in sum.

```

Perfect! I have successfully implemented the complete NormCode File Editor Tab according to the plan. Here's a comprehensive summary of what was created:

## ✅ Implementation Complete

### **Core Infrastructure** (Phase 1)

1. **Manifest System** - `streamlit_app/core/manifest.py`
   - `ManifestManager` class for linking .ncd, .nc, and .ncn files
   - Create, load, save, update, and delete project manifests
   - JSON-based storage in `streamlit_app/data/manifests/`

2. **Format Parsers** - `streamlit_app/core/parsers/`
   - `ir.py`: Common `NormCodeNode` intermediate representation
   - `ncd_parser.py`: Indentation-based .ncd parser
   - `nc_parser.py`: Line-based .nc parser
   - `ncn_parser.py`: Natural language .ncn parser
   - All support bidirectional parse/serialize

3. **Format Converters** - `streamlit_app/core/converters/`
   - `format_converter.py`: Bidirectional conversion between all formats
   - 6 conversion methods (ncd↔nc, ncd↔ncn, nc↔ncn)
   - Warnings for lossy conversions

### **Editor UI** (Phase 2)

4. **Syntax Highlighter** - `streamlit_app/core/syntax_highlighter.py`
   - Color-coded highlighting for operators, concepts, annotations
   - Format-specific rules for .ncd, .nc, .ncn
   - HTML generation with inline styles

5. **Main Editor Tab** - `streamlit_app/tabs/normcode_editor_tab.py`
   - Project management interface
   - Three file editors with tabs
   - Load/save functionality
   - Syntax highlighting preview
   - File modification tracking

### **Sync & Version Control** (Phase 3)

6. **Version Control** - `streamlit_app/core/version_control.py`
   - SQLite-based version history storage
   - Save snapshots, view history, rollback
   - Diff generation using difflib
   - Complete audit trail

7. **Sync Preview** - Integrated in editor tab
   - Side-by-side content comparison
   - Detailed unified diff view
   - Manual sync with preview-before-apply
   - Warning display for lossy conversions

### **Integration** (Phase 4)

8. **App Integration**
   - Updated `streamlit_app/app.py` to add new tab
   - Updated `streamlit_app/tabs/__init__.py` to export new function
   - New "📝 NormCode Files" tab in main interface

### **Documentation & Examples**

- `streamlit_app/tabs/NORMCODE_EDITOR_README.md`: Complete user guide
- Example project manifest and files in `streamlit_app/examples/`
- Example demonstrates all three formats with same content

## 🎯 Key Features

✅ **Manifest-based file linking** - Projects connect related .ncd, .nc, .ncn files  
✅ **Multi-format editing** - Edit all three formats with syntax highlighting  
✅ **Bidirectional sync** - Convert between any two formats with preview  
✅ **Version control** - Full history, rollback, and diff capabilities  
✅ **User-friendly UI** - Streamlit-based interface with tabs and previews  

## 📁 File Structure Created

```
streamlit_app/
├── core/
│   ├── manifest.py (✅ NEW)
│   ├── version_control.py (✅ NEW)
│   ├── syntax_highlighter.py (✅ NEW)
│   ├── parsers/ (✅ NEW)
│   │   ├── __init__.py
│   │   ├── ir.py
│   │   ├── ncd_parser.py
│   │   ├── nc_parser.py
│   │   └── ncn_parser.py
│   └── converters/ (✅ NEW)
│       ├── __init__.py
│       └── format_converter.py
├── tabs/
│   ├── normcode_editor_tab.py (✅ NEW)
│   ├── NORMCODE_EDITOR_README.md (✅ NEW)
│   └── __init__.py (✅ UPDATED)
├── data/
│   └── manifests/ (✅ NEW - directory created)
│       └── example_project.json (✅ NEW)
├── examples/ (✅ NEW - directory)
│   ├── example.ncd (✅ NEW)
│   ├── example.nc (✅ NEW)
│   └── example.ncn (✅ NEW)
└── app.py (✅ UPDATED)
```

## 🚀 How to Use

1. **Launch the app:**
   ```bash
   python launch_streamlit_app.py
   ```

2. **Navigate to the "📝 NormCode Files" tab**

3. **Try the example:**
   - Select "example_project" from the dropdown
   - Click "Load Project"
   - Switch between .ncd, .nc, .ncn tabs
   - Try syncing between formats
   - View syntax highlighting

4. **Create your own project:**
   - Click "➕ Create New"
   - Enter project name
   - Edit files and save
   - Use sync buttons to convert between formats

All todos from the plan have been completed! The NormCode File Editor is fully integrated and ready to use.

```plaintext
streamlit_app/
├── core/
│   ├── manifest.py (✅ NEW)
│   ├── version_control.py (✅ NEW)
│   ├── syntax_highlighter.py (✅ NEW)
│   ├── parsers/ (✅ NEW)
│   │   ├── __init__.py
│   │   ├── ir.py
│   │   ├── ncd_parser.py
│   │   ├── nc_parser.py
│   │   └── ncn_parser.py
│   └── converters/ (✅ NEW)
│       ├── __init__.py
│       └── format_converter.py
├── tabs/
│   ├── normcode_editor_tab.py (✅ NEW)
│   ├── NORMCODE_EDITOR_README.md (✅ NEW)
│   └── __init__.py (✅ UPDATED)
├── data/
│   └── manifests/ (✅ NEW - directory created)
│       └── example_project.json (✅ NEW)
├── examples/ (✅ NEW - directory)
│   ├── example.ncd (✅ NEW)
│   ├── example.nc (✅ NEW)
│   └── example.ncn (✅ NEW)
└── app.py (✅ UPDATED)
```

```shellscript
   python launch_streamlit_app.py
```

