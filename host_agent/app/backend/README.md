# NormCode Backend - Modular Architecture

This directory contains the refactored backend application with a clean, modular architecture.

## Structure

```
backend/
├── main.py              # Original monolithic file (kept for reference)
├── main_new.py          # New modular main application
├── models/              # Pydantic data models
│   ├── __init__.py
│   └── graph_models.py  # Node, Edge, and response models
├── services/            # Business logic layer
│   ├── __init__.py
│   └── graph_service.py # Graph operations and data persistence
├── routers/             # API route handlers
│   ├── __init__.py
│   └── graph_router.py  # HTTP endpoints for graph operations
├── schemas/             # Configuration and schemas
│   ├── __init__.py
│   └── config.py        # Application settings and configuration
└── data/                # Data storage (auto-created)
    ├── nodes.json
    └── edges.json
```

## Architecture Overview

### 1. Models (`models/graph_models.py`)
- **Position**: Node coordinate model
- **NodeData**: Node content data model
- **Node**: Complete node model with validation
- **Edge**: Edge/connection model
- **GraphResponse**: Standardized response model
- **ErrorResponse**: Error response model

### 2. Services (`services/graph_service.py`)
- **GraphService**: Business logic for graph operations
- Handles data persistence (JSON files)
- Node type validation
- CRUD operations for nodes and edges
- Data loading and saving

### 3. Routers (`routers/graph_router.py`)
- **graph_router**: HTTP endpoint handlers
- RESTful API endpoints
- Request/response handling
- Error handling and validation
- Dependency injection for services

### 4. Schemas (`schemas/config.py`)
- **Settings**: Application configuration
- CORS settings
- Server configuration
- Data file paths
- Node type validation rules

### 5. Main Application (`main_new.py`)
- **create_app()**: Application factory function
- CORS middleware configuration
- Router registration
- Server startup configuration

## API Endpoints

All endpoints are prefixed with `/api/v1`:

- `GET /` - Root endpoint
- `GET /nodes` - Get all nodes
- `GET /edges` - Get all edges
- `POST /nodes` - Create a new node
- `POST /edges` - Create a new edge
- `PUT /nodes/{node_id}` - Update a node
- `DELETE /nodes/{node_id}` - Delete a node and its edges
- `DELETE /edges/{edge_id}` - Delete an edge
- `POST /save` - Save graph to files
- `POST /load` - Load graph from files

## Benefits of This Architecture

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Maintainability**: Easy to modify individual components
3. **Testability**: Services can be unit tested independently
4. **Scalability**: Easy to add new features and endpoints
5. **Configuration Management**: Centralized settings
6. **Dependency Injection**: Clean service integration
7. **Type Safety**: Full Pydantic model validation

## Migration from Original

The original `main.py` is preserved for reference. To use the new modular structure:

1. **Development**: Use `main_new.py` for new development
2. **Testing**: The new structure is easier to test
3. **Configuration**: Settings are now centralized in `schemas/config.py`
4. **API**: All endpoints now use `/api/v1` prefix

## Running the Application

```bash
# Run the new modular version
python main_new.py

# Or using uvicorn directly
uvicorn main_new:app --host 0.0.0.0 --port 8000
```

## Configuration

Settings can be customized via environment variables or `.env` file:

```env
HOST=0.0.0.0
PORT=8000
DATA_DIR=data
NODES_FILE=nodes.json
EDGES_FILE=edges.json
```

## Future Enhancements

This modular structure makes it easy to add:

- Database integration
- Authentication/authorization
- Additional graph algorithms
- WebSocket support
- Caching layers
- Logging and monitoring
- API versioning 