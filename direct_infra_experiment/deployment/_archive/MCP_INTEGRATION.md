# MCP Integration for NormCode Server

How NormCode Server integrates with the Model Context Protocol (MCP) ecosystem.

---

## Overview

NormCode Server can participate in MCP in two ways:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌─────────────┐      MCP       ┌─────────────────────────────┐ │
│  │ AI Assistant│ ─────────────→ │ NormCode as MCP SERVER      │ │
│  │ (Claude)    │                │ (Exposes plans, runs)       │ │
│  └─────────────┘                └─────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────┐      MCP       ┌─────────────┐ │
│  │ NormCode as MCP CLIENT      │ ─────────────→ │ External    │ │
│  │ (Uses tools in plan steps)  │                │ MCP Servers │ │
│  └─────────────────────────────┘                └─────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Role | Purpose |
|------|---------|
| **MCP Server** | AI assistants can trigger NormCode workflows |
| **MCP Client** | Plan steps can use external MCP tools |

---

## Part 1: NormCode as MCP Server

### What We Expose

| MCP Capability | NormCode Mapping |
|----------------|------------------|
| **Resources** | Deployed plans, run results, checkpoints |
| **Tools** | deploy_plan, start_run, pause_run, resume_run, fork_run |
| **Prompts** | Plan templates, workflow patterns |

### MCP Server Implementation

```python
# mcp_server/normcode_mcp.py

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

from engine.plan_registry import PlanRegistry
from engine.execution_manager import ExecutionManager

# Initialize MCP server
server = Server("normcode")

# Shared state (injected at startup)
plan_registry: PlanRegistry = None
execution_manager: ExecutionManager = None

# ============================================================================
# RESOURCES
# ============================================================================

@server.list_resources()
async def list_resources():
    """List all deployed plans and active runs as resources."""
    resources = []
    
    # Deployed plans
    for plan in plan_registry.list_all():
        resources.append(Resource(
            uri=f"normcode://plans/{plan.id}",
            name=f"Plan: {plan.name}",
            description=plan.description,
            mimeType="application/json"
        ))
    
    # Active runs
    for run in execution_manager.list_runs():
        resources.append(Resource(
            uri=f"normcode://runs/{run.id}",
            name=f"Run: {run.id} ({run.status})",
            description=f"Plan: {run.plan_id}, Status: {run.status}",
            mimeType="application/json"
        ))
    
    return resources

@server.read_resource()
async def read_resource(uri: str):
    """Read plan details or run status."""
    import json
    
    if uri.startswith("normcode://plans/"):
        plan_id = uri.replace("normcode://plans/", "")
        plan = plan_registry.get(plan_id)
        if plan:
            return json.dumps(plan.to_dict(), indent=2)
        raise ValueError(f"Plan not found: {plan_id}")
    
    elif uri.startswith("normcode://runs/"):
        run_id = uri.replace("normcode://runs/", "")
        run = execution_manager.get_run(run_id)
        if run:
            return json.dumps(run.to_dict(), indent=2)
        raise ValueError(f"Run not found: {run_id}")
    
    raise ValueError(f"Unknown resource URI: {uri}")

# ============================================================================
# TOOLS
# ============================================================================

@server.list_tools()
async def list_tools():
    """List available NormCode operations as MCP tools."""
    return [
        Tool(
            name="list_plans",
            description="List all deployed NormCode plans",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="start_run",
            description="Start execution of a deployed NormCode plan",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "ID of the plan to execute"
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Input values for ground concepts",
                        "additionalProperties": True
                    },
                    "agent": {
                        "type": "string",
                        "description": "Agent to use for execution (optional)"
                    }
                },
                "required": ["plan_id"]
            }
        ),
        Tool(
            name="get_run_status",
            description="Get the current status of a NormCode run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "ID of the run to check"
                    }
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="pause_run",
            description="Pause an active NormCode run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "ID of the run to pause"
                    }
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="resume_run",
            description="Resume a paused NormCode run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "ID of the run to resume"
                    },
                    "checkpoint_cycle": {
                        "type": "integer",
                        "description": "Optional: resume from specific checkpoint cycle"
                    }
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="fork_run",
            description="Create a new run forked from a checkpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_run_id": {
                        "type": "string",
                        "description": "ID of the run to fork from"
                    },
                    "checkpoint_cycle": {
                        "type": "integer",
                        "description": "Cycle number to fork from"
                    }
                },
                "required": ["source_run_id", "checkpoint_cycle"]
            }
        ),
        Tool(
            name="get_run_result",
            description="Get the final result of a completed run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "ID of the completed run"
                    }
                },
                "required": ["run_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute NormCode operations."""
    
    if name == "list_plans":
        plans = plan_registry.list_all()
        result = [{"id": p.id, "name": p.name, "description": p.description} for p in plans]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "start_run":
        run = await execution_manager.start_run(
            plan_id=arguments["plan_id"],
            inputs=arguments.get("inputs", {}),
            agent=arguments.get("agent")
        )
        return [TextContent(type="text", text=f"Started run: {run.id}")]
    
    elif name == "get_run_status":
        run = execution_manager.get_run(arguments["run_id"])
        if not run:
            return [TextContent(type="text", text=f"Run not found: {arguments['run_id']}")]
        return [TextContent(type="text", text=json.dumps(run.to_dict(), indent=2))]
    
    elif name == "pause_run":
        await execution_manager.pause_run(arguments["run_id"])
        return [TextContent(type="text", text=f"Paused run: {arguments['run_id']}")]
    
    elif name == "resume_run":
        await execution_manager.resume_run(
            run_id=arguments["run_id"],
            checkpoint_cycle=arguments.get("checkpoint_cycle")
        )
        return [TextContent(type="text", text=f"Resumed run: {arguments['run_id']}")]
    
    elif name == "fork_run":
        new_run = await execution_manager.fork_run(
            source_run_id=arguments["source_run_id"],
            checkpoint_cycle=arguments["checkpoint_cycle"]
        )
        return [TextContent(type="text", text=f"Forked to new run: {new_run.id}")]
    
    elif name == "get_run_result":
        run = execution_manager.get_run(arguments["run_id"])
        if not run:
            return [TextContent(type="text", text=f"Run not found: {arguments['run_id']}")]
        if run.status != "completed":
            return [TextContent(type="text", text=f"Run not completed: {run.status}")]
        return [TextContent(type="text", text=json.dumps(run.result, indent=2))]
    
    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# PROMPTS
# ============================================================================

@server.list_prompts()
async def list_prompts():
    """List workflow prompt templates."""
    return [
        {
            "name": "analyze_document",
            "description": "Template for document analysis workflow",
            "arguments": [
                {"name": "document_path", "description": "Path to document", "required": True}
            ]
        },
        {
            "name": "multi_step_reasoning",
            "description": "Template for multi-step reasoning workflow",
            "arguments": [
                {"name": "question", "description": "Question to analyze", "required": True},
                {"name": "context", "description": "Background context", "required": False}
            ]
        }
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    """Get a workflow prompt template."""
    if name == "analyze_document":
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"""Analyze the document at: {arguments['document_path']}

Use the NormCode workflow system:
1. First, list available plans with `list_plans`
2. Find a suitable document analysis plan
3. Start a run with `start_run` providing the document path as input
4. Monitor with `get_run_status` until complete
5. Retrieve results with `get_run_result`"""
                }
            ]
        }
    
    raise ValueError(f"Unknown prompt: {name}")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the MCP server."""
    global plan_registry, execution_manager
    
    # Initialize NormCode components
    from engine.plan_registry import PlanRegistry
    from engine.execution_manager import ExecutionManager
    
    plan_registry = PlanRegistry("/data/plans")
    execution_manager = ExecutionManager(plan_registry)
    
    # Run MCP server over stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Claude Desktop Configuration

To use NormCode from Claude Desktop, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "normcode": {
      "command": "python",
      "args": ["/path/to/normcode_server/mcp_server/normcode_mcp.py"],
      "env": {
        "NORMCODE_DATA_DIR": "/data"
      }
    }
  }
}
```

### Example Conversation with Claude

```
User: I have a legal document that needs analysis. Can you use NormCode?

Claude: I'll check what NormCode plans are available.

[Calls list_plans tool]

I found a "legal-document-analysis" plan. Let me start a run:

[Calls start_run with plan_id="legal-document-analysis", inputs={"document": "..."}]

Started run abc-123. Let me check the status:

[Calls get_run_status with run_id="abc-123"]

The run is still in progress (cycle 3 of 10). I'll wait...

[Later, calls get_run_result with run_id="abc-123"]

Here are the analysis results: ...
```

---

## Part 2: NormCode as MCP Client

### Using MCP Tools in Plan Steps

NormCode steps can invoke external MCP servers as tools.

### MCP Client Tool for Body

```python
# infra/_agent/_models/_mcp_client.py

import asyncio
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client

class MCPClientTool:
    """
    Tool that allows NormCode Body to call external MCP servers.
    """
    
    def __init__(self):
        self._sessions: Dict[str, ClientSession] = {}
        self._configs: Dict[str, dict] = {}
    
    def configure(self, servers: Dict[str, dict]):
        """
        Configure MCP servers.
        
        Args:
            servers: Dict mapping server name to config:
                {
                    "database": {
                        "command": "python",
                        "args": ["database_mcp.py"],
                        "env": {"DB_PATH": "/data/db.sqlite"}
                    },
                    "web-search": {
                        "command": "npx",
                        "args": ["-y", "@anthropic/mcp-server-brave-search"],
                        "env": {"BRAVE_API_KEY": "..."}
                    }
                }
        """
        self._configs = servers
    
    async def _get_session(self, server_name: str) -> ClientSession:
        """Get or create session for a server."""
        if server_name not in self._sessions:
            config = self._configs.get(server_name)
            if not config:
                raise ValueError(f"Unknown MCP server: {server_name}")
            
            # Create stdio client
            read, write = await stdio_client(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {})
            )
            
            session = ClientSession(read, write)
            await session.initialize()
            self._sessions[server_name] = session
        
        return self._sessions[server_name]
    
    async def list_tools(self, server_name: str) -> List[dict]:
        """List available tools from an MCP server."""
        session = await self._get_session(server_name)
        result = await session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on an MCP server."""
        session = await self._get_session(server_name)
        result = await session.call_tool(tool_name, arguments)
        
        # Extract text content
        if result.content:
            return result.content[0].text
        return None
    
    async def read_resource(self, server_name: str, uri: str) -> str:
        """Read a resource from an MCP server."""
        session = await self._get_session(server_name)
        result = await session.read_resource(uri)
        
        if result.contents:
            return result.contents[0].text
        return None
    
    async def close(self):
        """Close all MCP sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()


# Synchronous wrapper for use in Body
class MCPClientToolSync:
    """Synchronous wrapper for MCPClientTool."""
    
    def __init__(self):
        self._async_tool = MCPClientTool()
        self._loop = None
    
    def _get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop
    
    def configure(self, servers: Dict[str, dict]):
        self._async_tool.configure(servers)
    
    def list_tools(self, server_name: str) -> List[dict]:
        return self._get_loop().run_until_complete(
            self._async_tool.list_tools(server_name)
        )
    
    def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        return self._get_loop().run_until_complete(
            self._async_tool.call_tool(server_name, tool_name, arguments)
        )
    
    def read_resource(self, server_name: str, uri: str) -> str:
        return self._get_loop().run_until_complete(
            self._async_tool.read_resource(server_name, uri)
        )
```

### Adding MCP to Body

```python
# infra/_agent/_body.py (addition)

class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, 
                 mcp_servers: Dict[str, dict] | None = None, ...):
        # ... existing initialization ...
        
        # MCP Client Tool
        from infra._agent._models._mcp_client import MCPClientToolSync
        self.mcp = MCPClientToolSync()
        
        if mcp_servers:
            self.mcp.configure(mcp_servers)
```

### Using MCP in a Paradigm

A paradigm can invoke MCP tools as part of its composition:

```json
{
  "name": "h_Query-c_MCPTool-o_Result",
  "metadata": {
    "description": "Execute query via MCP tool",
    "inputs": {
      "horizontal": {
        "mcp_server": "Name of MCP server",
        "mcp_tool": "Name of tool to call"
      },
      "vertical": {
        "query": "Query or arguments to pass"
      }
    }
  },
  "composition": [
    {
      "step": "call_mcp",
      "action": "body.mcp.call_tool",
      "inputs": {
        "server_name": "{h_input.mcp_server}",
        "tool_name": "{h_input.mcp_tool}",
        "arguments": "{v_input.query}"
      },
      "output": "mcp_result"
    },
    {
      "step": "format_output",
      "action": "body.formatter_tool.format",
      "inputs": {
        "data": "{mcp_result}",
        "schema": "{o_shape}"
      },
      "output": "final_result"
    }
  ]
}
```

### Example: Plan Using MCP Database Tool

```ncds
/: Query database and summarize results

<- summary
    <= summarize the query results
    <- query results
        <= query the database for recent orders
            |%{paradigm}: h_Query-c_MCPTool-o_Result
            |%{mcp_server}: database
            |%{mcp_tool}: query
        <- query parameters
            |%{ground}: {"sql": "SELECT * FROM orders WHERE date > '2024-01-01'"}
```

---

## Part 3: Configuration

### Server Configuration for MCP

```yaml
# /data/config/server.yaml

server:
  host: "0.0.0.0"
  port: 8000

mcp:
  # NormCode as MCP Server
  server:
    enabled: true
    transport: "stdio"  # or "sse" for HTTP
    
  # NormCode as MCP Client  
  client:
    servers:
      database:
        command: "python"
        args: ["mcp_servers/database_mcp.py"]
        env:
          DB_PATH: "/data/database.sqlite"
          
      file-search:
        command: "npx"
        args: ["-y", "@anthropic/mcp-server-filesystem"]
        env:
          ALLOWED_PATHS: "/data/documents"
          
      web-search:
        command: "npx"
        args: ["-y", "@anthropic/mcp-server-brave-search"]
        env:
          BRAVE_API_KEY: "${BRAVE_API_KEY}"
```

---

## Part 4: Docker Integration

### Dockerfile with MCP Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Node.js for npm-based MCP servers
RUN apt-get update && apt-get install -y \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies including MCP SDK
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install mcp

# Install common MCP servers
RUN npm install -g @anthropic/mcp-server-filesystem

# Copy application
COPY . .

# Build frontend
WORKDIR /app/frontend
RUN npm ci && npm run build

WORKDIR /app

EXPOSE 8000

ENV NORMCODE_DATA_DIR=/data

# Start both REST API and MCP server
CMD ["python", "server/main.py"]
```

### requirements.txt Addition

```
# MCP SDK
mcp>=0.1.0
```

---

## Summary

### What We Get

| Integration | Benefit |
|-------------|---------|
| **NormCode as MCP Server** | AI assistants (Claude) can orchestrate NormCode workflows |
| **NormCode as MCP Client** | Plan steps can use external tools (databases, search, files) |
| **Unified Configuration** | Single `server.yaml` configures both directions |

### Architecture Result

```
┌─────────────────────────────────────────────────────────────────┐
│                    NORMCODE SERVER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  MCP Server Interface                                      │ │
│  │  (AI assistants connect here)                              │ │
│  │  ├── Resources: plans, runs, checkpoints                   │ │
│  │  ├── Tools: start_run, pause_run, resume_run, fork_run     │ │
│  │  └── Prompts: workflow templates                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  REST + WebSocket API                                      │ │
│  │  (Web clients, Canvas App connect here)                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Orchestrator + Agent Pool                                 │ │
│  │  ├── Body.mcp (MCP Client)                                 │ │
│  │  │     ├── database server                                 │ │
│  │  │     ├── file-search server                              │ │
│  │  │     └── web-search server                               │ │
│  │  └── Body.llm, Body.file_system, Body.python_interpreter   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

NormCode becomes a **hub** that:
1. **Receives** workflow requests from AI assistants via MCP
2. **Orchestrates** structured execution with full auditability
3. **Delegates** to external MCP tools when needed

