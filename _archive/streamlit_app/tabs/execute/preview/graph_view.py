"""
Graph view components for preview.
Handles rendering of concept dependency graphs using Viz.js.
"""

import streamlit as st
from typing import Dict, Any, Optional, List

from .utils import get_concept_category


# =============================================================================
# MAIN GRAPH VIEW
# =============================================================================

def render_graph_view(
    concepts_data: Optional[List[Dict[str, Any]]],
    inferences_data: Optional[List[Dict[str, Any]]]
):
    """Render the graph visualization of concept dependencies."""
    if not concepts_data or not inferences_data:
        st.warning("Both concepts and inferences are required for graph view")
        return
    
    st.subheader("🔀 Dependency Graph")
    
    # Info about the graph
    with st.expander("ℹ️ Graph Legend & Controls", expanded=False):
        st.markdown("""
**Node Colors:**
- 🟣 **Purple** (ellipse): Semantic Functions (`::({})`, `<{}>`)
- 🔵 **Blue** (box): Semantic Values (`{}`, `<>`, `[]`)
- ⚫ **Gray** (box): Syntactic Functions

**Edge Types:**
- **Solid blue arrow**: Function relationship (`<=`)
- **Dashed purple arrow**: Value relationship (`<-`)

**Node Shapes:**
- 🔶 **Double circle**: Ground concepts (inputs)
- 🎯 **Bold border**: Final concepts (outputs)

**Controls:**
- 🖱️ **Scroll to zoom** in/out
- 🖱️ **Click and drag** to pan
- 🔄 **Double-click** to reset view
- ⬇️ **Download** button in top-right of graph
        """)
    
    # Build and render the graph
    try:
        graph_source = build_graphviz_source(concepts_data, inferences_data)
        render_zoomable_graph_with_vizjs(graph_source)
        
    except Exception as e:
        st.error(f"Error rendering graph: {e}")
        
        # Fallback: show text-based representation
        st.markdown("### Text-based Flow")
        render_text_flow(inferences_data)


# =============================================================================
# GRAPH RENDERING
# =============================================================================

def render_zoomable_graph_with_vizjs(dot_source: str):
    """
    Render a Graphviz graph using Viz.js (pure JavaScript, no system binaries needed)
    with pan/zoom capabilities using svg-pan-zoom library.
    
    Args:
        dot_source: DOT format graph description
    """
    # Escape the DOT source for JavaScript
    dot_escaped = dot_source.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    
    # Create HTML with Viz.js + svg-pan-zoom
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/@viz-js/viz@3.2.4/lib/viz-standalone.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            #graph-container {{
                width: 100%;
                height: 550px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
                position: relative;
                overflow: hidden;
            }}
            #svg-container {{
                width: 100%;
                height: 100%;
            }}
            #svg-container svg {{
                width: 100%;
                height: 100%;
            }}
            .controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(255, 255, 255, 0.95);
                padding: 6px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                z-index: 1000;
                display: flex;
                gap: 4px;
                flex-wrap: wrap;
            }}
            .controls button {{
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: white;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.15s;
            }}
            .controls button:hover {{
                background: #f3f4f6;
                border-color: #9ca3af;
            }}
            .controls button.download {{
                background: #3b82f6;
                color: white;
                border-color: #2563eb;
            }}
            .controls button.download:hover {{
                background: #2563eb;
            }}
            #loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 14px;
                color: #666;
            }}
            #error {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #dc2626;
                text-align: center;
                padding: 20px;
            }}
            .zoom-info {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: rgba(255,255,255,0.9);
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div id="graph-container">
            <div class="controls">
                <button onclick="zoomIn()" title="Zoom In">🔍+</button>
                <button onclick="zoomOut()" title="Zoom Out">🔍−</button>
                <button onclick="resetView()" title="Reset View">🔄</button>
                <button onclick="fitGraph()" title="Fit to View">📐</button>
                <button onclick="downloadSvg()" class="download" title="Download SVG">⬇️ SVG</button>
            </div>
            <div id="loading">⏳ Rendering graph...</div>
            <div id="svg-container"></div>
            <div class="zoom-info" id="zoom-info">Scroll to zoom • Drag to pan</div>
        </div>
        <script>
            var panZoom = null;
            var svgContent = null;
            
            const dotSource = `{dot_escaped}`;
            
            async function renderGraph() {{
                try {{
                    const viz = await Viz.instance();
                    svgContent = viz.renderSVGElement(dotSource);
                    svgContent.id = 'graph-svg';
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('svg-container').appendChild(svgContent);
                    
                    // Initialize pan-zoom
                    panZoom = svgPanZoom('#graph-svg', {{
                        zoomEnabled: true,
                        controlIconsEnabled: false,
                        fit: true,
                        center: true,
                        minZoom: 0.1,
                        maxZoom: 15,
                        zoomScaleSensitivity: 0.25,
                        dblClickZoomEnabled: false,
                        mouseWheelZoomEnabled: true,
                        preventMouseEventsDefault: true
                    }});
                    
                    // Double-click to reset
                    svgContent.addEventListener('dblclick', resetView);
                    
                }} catch (e) {{
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error').innerHTML = '❌ Error: ' + e.message;
                    console.error('Graph render error:', e);
                }}
            }}
            
            function zoomIn() {{
                if (panZoom) panZoom.zoomIn();
            }}
            
            function zoomOut() {{
                if (panZoom) panZoom.zoomOut();
            }}
            
            function resetView() {{
                if (panZoom) {{
                    panZoom.reset();
                    panZoom.center();
                }}
            }}
            
            function fitGraph() {{
                if (panZoom) {{
                    panZoom.fit();
                    panZoom.center();
                }}
            }}
            
            function downloadSvg() {{
                if (!svgContent) return;
                
                // Clone and clean up SVG for download
                const svgClone = svgContent.cloneNode(true);
                svgClone.removeAttribute('style');
                
                const serializer = new XMLSerializer();
                let svgString = serializer.serializeToString(svgClone);
                svgString = '<?xml version="1.0" encoding="UTF-8"?>\\n' + svgString;
                
                const blob = new Blob([svgString], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = 'concept_graph.svg';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
            
            // Initialize
            renderGraph();
        </script>
        <div id="error"></div>
    </body>
    </html>
    """
    
    # Render the HTML component
    st.components.v1.html(html_content, height=580, scrolling=False)


# =============================================================================
# GRAPHVIZ DOT GENERATION
# =============================================================================

def build_graphviz_source(
    concepts_data: List[Dict[str, Any]],
    inferences_data: List[Dict[str, Any]]
) -> str:
    """Build Graphviz DOT source for the dependency graph."""
    
    # Build concept lookup for attributes
    concept_attrs = {}
    for c in concepts_data:
        name = c.get('concept_name', '')
        concept_attrs[name] = {
            'is_ground': c.get('is_ground_concept', False),
            'is_final': c.get('is_final_concept', False),
            'is_invariant': c.get('is_invariant', False),
            'category': get_concept_category(name)
        }
    
    # Start building DOT
    lines = [
        'digraph G {',
        '    rankdir=LR;',  # Left to right flow
        '    bgcolor="transparent";',
        '    node [fontname="Arial", fontsize=10];',
        '    edge [fontname="Arial", fontsize=8];',
        ''
    ]
    
    # Track all referenced concepts
    all_concepts = set()
    
    # Add edges from inferences
    for inf in inferences_data:
        target = inf.get('concept_to_infer', '')
        func = inf.get('function_concept', '')
        values = inf.get('value_concepts', [])
        seq = inf.get('inference_sequence', '')
        
        if target:
            all_concepts.add(target)
        if func:
            all_concepts.add(func)
            # Function edge (solid blue)
            lines.append(f'    "{escape_dot(func)}" -> "{escape_dot(target)}" '
                        f'[color="#4a90e2", penwidth=1.5, label="{seq}"];')
        
        for val in values:
            if val:
                all_concepts.add(val)
                # Value edge (dashed purple)
                lines.append(f'    "{escape_dot(val)}" -> "{escape_dot(target)}" '
                            f'[color="#7b68ee", style=dashed, penwidth=1.0];')
    
    lines.append('')
    
    # Add node styling
    for concept_name in all_concepts:
        attrs = concept_attrs.get(concept_name, {
            'is_ground': False,
            'is_final': False,
            'is_invariant': False,
            'category': get_concept_category(concept_name)
        })
        
        node_style = get_node_style(attrs)
        # Truncate label for display
        label = concept_name if len(concept_name) <= 25 else concept_name[:22] + "..."
        lines.append(f'    "{escape_dot(concept_name)}" [{node_style}, label="{escape_dot(label)}"];')
    
    lines.append('}')
    
    return '\n'.join(lines)


def escape_dot(s: str) -> str:
    """Escape special characters for DOT format."""
    return s.replace('"', '\\"').replace('\n', '\\n')


def get_node_style(attrs: Dict[str, Any]) -> str:
    """Get Graphviz node style based on concept attributes."""
    category = attrs.get('category', 'syntactic-function')
    is_ground = attrs.get('is_ground', False)
    is_final = attrs.get('is_final', False)
    
    # Base colors by category
    colors = {
        'semantic-function': ('#ede7f6', '#7b68ee'),  # fill, border
        'semantic-value': ('#dbeafe', '#3b82f6'),
        'syntactic-function': ('#f1f5f9', '#64748b'),
    }
    fill, border = colors.get(category, ('#ffffff', '#888888'))
    
    # Base shape by category
    if category == 'semantic-function':
        shape = 'ellipse'
    else:
        shape = 'box'
    
    # Modify for ground/final
    style_parts = ['filled']
    penwidth = '1.0'
    
    if is_ground:
        shape = 'doublecircle' if category == 'semantic-function' else 'doubleoctagon'
        penwidth = '2.0'
    
    if is_final:
        style_parts.append('bold')
        penwidth = '2.5'
        border = '#e11d48'  # Red border for final
    
    style = ','.join(style_parts)
    
    return f'shape={shape}, style="{style}", fillcolor="{fill}", color="{border}", penwidth={penwidth}'


# =============================================================================
# TEXT-BASED FALLBACK
# =============================================================================

def render_text_flow(inferences_data: List[Dict[str, Any]]):
    """Render a text-based flow representation as fallback."""
    # Group by sequence
    by_sequence = {}
    for inf in inferences_data:
        seq = inf.get('inference_sequence', 'unknown')
        if seq not in by_sequence:
            by_sequence[seq] = []
        by_sequence[seq].append(inf)
    
    for seq in sorted(by_sequence.keys()):
        st.markdown(f"**Sequence: {seq}**")
        for inf in by_sequence[seq]:
            target = inf.get('concept_to_infer', '?')
            func = inf.get('function_concept', '?')
            values = inf.get('value_concepts', [])
            
            flow_text = f"  `{target}` ⬅️ `{func}`"
            if values:
                flow_text += f" 📥 ({', '.join(values[:3])}{'...' if len(values) > 3 else ''})"
            st.markdown(flow_text)
        st.markdown("---")

