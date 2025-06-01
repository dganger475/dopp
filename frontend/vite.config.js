import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Accept external connections (needed for ngrok/tunnels)
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '7964-149-36-48-146.ngrok-free.app' // Added your ngrok domain here
    ],
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