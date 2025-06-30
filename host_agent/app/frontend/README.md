# Flow Graph Application

This is a full-stack application for creating and managing flow graphs. It consists of a React frontend and a FastAPI backend.

## Features

- Create, edit, and delete nodes
- Connect nodes with edges
- Different node types with various colors
- Real-time updates
- Persistent storage (in-memory for now, can be extended to use a database)

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

## Setup

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server:
```bash
cd backend
uvicorn main:app --reload
```

The backend will be available at http://localhost:8000

### Frontend Setup

1. Install dependencies:
```bash
cd interface
npm install
```

2. Start the development server:
```bash
npm start
```

The frontend will be available at http://localhost:3000

## API Endpoints

- `GET /nodes` - Get all nodes
- `POST /nodes` - Create a new node
- `PUT /nodes/{node_id}` - Update a node
- `DELETE /nodes/{node_id}` - Delete a node
- `GET /edges` - Get all edges
- `POST /edges` - Create a new edge
- `DELETE /edges/{edge_id}` - Delete an edge

## Development

### Backend Development

The backend is built with FastAPI and provides a RESTful API for managing nodes and edges. The current implementation uses in-memory storage, but it can be easily extended to use a database.

### Frontend Development

The frontend is built with React and uses ReactFlow for the graph visualization. It communicates with the backend API to persist changes.

## Future Improvements

1. Add database integration (e.g., PostgreSQL)
2. Add user authentication
3. Add graph export/import functionality
4. Add more node types and customization options
5. Add undo/redo functionality
6. Add graph validation rules
7. Add collaborative editing features 