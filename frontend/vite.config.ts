import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true, // Listen on all addresses, including LAN and public addresses.
    port: 8080, // Explicitly set the port
    // Optional: Proxy API requests to backend during development to avoid CORS issues
    // proxy: {
    //   '/api': {
    //     target: 'http://backend:8000', // Target the backend service name in Docker Compose
    //     changeOrigin: true,
    //     // rewrite: (path) => path.replace(/^\/api/, ''), // Remove /api prefix if backend doesn't expect it
    //   }
    // }
  }
})
