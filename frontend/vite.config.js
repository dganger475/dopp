import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Accept external connections
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'dopple503.fly.dev' // Added Fly.io domain
    ],
    proxy: {
      '/api': {
        target: process.env.NODE_ENV === 'production' 
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
      '/auth': {
        target: process.env.NODE_ENV === 'production'
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
      '/profile': {
        target: process.env.NODE_ENV === 'production'
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
      '/social': {
        target: process.env.NODE_ENV === 'production'
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
      '/static': {
        target: process.env.NODE_ENV === 'production'
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
      '/face': {
        target: process.env.NODE_ENV === 'production'
          ? 'https://dopple503.fly.dev'
          : 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})