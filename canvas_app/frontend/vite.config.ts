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
