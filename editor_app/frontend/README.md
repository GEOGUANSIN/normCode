# Normcode Editor Frontend

A modern React + TypeScript + Vite frontend for the Normcode Repository Editor.

## Features

- **Modern React Architecture**: Built with React 18, TypeScript, and Vite for fast development and building
- **JSON Editor Integration**: Uses @jsoneditor/jsoneditor for powerful JSON editing capabilities
- **Real-time Logs**: Live log streaming during repository execution
- **Responsive Design**: Clean, modern UI with responsive layout
- **Type Safety**: Full TypeScript support for better development experience

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety and better development experience
- **Vite** - Fast build tool and development server
- **@jsoneditor/jsoneditor** - JSON editing component
- **CSS3** - Modern styling with flexbox and grid

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd editor_app/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000` and will automatically proxy API requests to the backend at `http://127.0.0.1:8001`.

### Building for Production

```bash
npm run build
```

This will create a `dist` folder with the production build.

## Project Structure

```
src/
├── components/          # React components
│   ├── JsonEditor.tsx   # JSON editor wrapper
│   ├── Sidebar.tsx      # Repository management sidebar
│   └── LogViewer.tsx    # Log display component
├── services/            # API services
│   └── api.ts           # Backend API client
├── types/               # TypeScript type definitions
│   └── index.ts         # API and data types
├── App.tsx              # Main application component
├── App.css              # Application styles
├── main.tsx             # Application entry point
└── index.css            # Global styles
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### API Integration

The frontend communicates with the backend through the `/api` endpoints. The Vite development server is configured to proxy these requests to the backend server.

### Styling

The application uses modern CSS with:
- Flexbox for layout
- CSS custom properties for theming
- Responsive design principles
- Clean, modern UI components

## Backend Integration

Make sure the backend server is running on `http://127.0.0.1:8001` for the frontend to work properly. The backend should have CORS enabled to allow requests from the frontend development server.
