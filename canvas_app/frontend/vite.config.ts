import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Production build settings
  base: './',  // Use relative paths for assets (important for packaged app)
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // Generate source maps for debugging (can be disabled for smaller builds)
    sourcemap: false,
    // Optimize chunk sizes
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor chunks for better caching
          'react-vendor': ['react', 'react-dom'],
          'flow-vendor': ['reactflow'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // REST API proxy
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Note: WebSocket connects directly to backend (ws://localhost:8000/ws/events)
      // to avoid Vite proxy issues. See websocket.ts
    },
  },
})
