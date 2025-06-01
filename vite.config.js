import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',          // Accept external connections (needed for ngrok/tunnels)
    allowedHosts: 'all',      // Allow all hosts for development (includes ngrok domains)
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/profile': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/social': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/face': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})