import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API requests to Flask backend
      // General rule for all /api calls
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true, // Recommended for virtual hosted sites
      },
      // Proxy for all /auth calls
      '/auth': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Profile routes
      '/profile': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Social routes
      '/social': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Proxy requests for static assets (like images) to Flask
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Proxy requests for face images served by /face/... routes
      '/face': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    }
  }
})
