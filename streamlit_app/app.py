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
from tabs import render_execute_tab, render_results_tab, render_history_tab, render_help_tab

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
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Execute", "📊 Results", "📜 History", "📖 Help"])

# Render tabs
with tab1:
    render_execute_tab(config)

with tab2:
    render_results_tab(config['db_path'])

with tab3:
    render_history_tab(config['db_path'])

with tab4:
    render_help_tab()

# Render footer
render_footer()
