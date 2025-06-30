# Graph Visualization Frontend (TypeScript + Vite)

This is a TypeScript rewrite of the original JavaScript frontend for the graph visualization application. It uses Vite as the build tool and includes all the same functionality as the original version.

## Features

- Interactive graph visualization with ReactFlow
- Custom node types with different colors
- Editable node labels
- Custom edge styles (solid/dashed)
- Auto-save functionality
- Hierarchical layout calculation
- Real-time graph updates
- Modern TypeScript implementation

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **ReactFlow** - Graph visualization library
- **Styled Components** - CSS-in-JS styling

## Project Structure

```
src/
├── components/
│   ├── nodes/
│   │   ├── CustomNode.tsx
│   │   └── NodeStyles.ts
│   ├── edges/
│   │   └── CustomEdge.tsx
│   └── ControlPanel.tsx
├── context/
│   └── NodeContext.tsx
├── types/
│   └── index.ts
├── utils/
│   └── layout.ts
├── config.ts
├── App.tsx
└── main.ts
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## API Integration

This frontend connects to a backend API running on `http://localhost:8000`. Make sure the backend is running before using the frontend.

### API Endpoints

- `GET /nodes` - Fetch all nodes
- `POST /nodes` - Create a new node
- `PUT /nodes/:id` - Update a node
- `DELETE /nodes/:id` - Delete a node
- `GET /edges` - Fetch all edges
- `POST /edges` - Create a new edge
- `DELETE /edges/:id` - Delete an edge
- `POST /save` - Save the current graph state
- `POST /load` - Load a saved graph state

## TypeScript Features

- **Type Safety**: All components and functions are properly typed
- **Interface Definitions**: Clear interfaces for all data structures
- **Generic Types**: Proper use of ReactFlow's generic types
- **Strict Mode**: Full TypeScript strict mode compliance

## Key Improvements Over JavaScript Version

1. **Type Safety**: Catch errors at compile time
2. **Better IDE Support**: Enhanced autocomplete and refactoring
3. **Maintainability**: Easier to understand and modify code
4. **Modern Build Tool**: Vite provides faster development experience
5. **Better Error Handling**: TypeScript helps prevent runtime errors

## Development

### Adding New Node Types

1. Update the `NodeType` union type in `src/types/index.ts`
2. Add the color to `nodeColors` in `src/config.ts`
3. Update the `VALID_NODE_TYPES` array in `src/App.tsx`

### Styling

All styling is done with styled-components. The styles are co-located with their components for better maintainability.

### State Management

The application uses React's built-in state management with Context API for sharing state between components.

## Troubleshooting

### Common Issues

1. **Backend Connection**: Ensure the backend is running on port 8000
2. **Type Errors**: Run `npm run build` to check for TypeScript errors
3. **Dependencies**: If you encounter dependency issues, try `npm install --force`

### Development Tips

- Use the TypeScript language server in your IDE for better development experience
- Check the browser console for any runtime errors
- Use React DevTools for debugging component state 