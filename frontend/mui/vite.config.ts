import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    host: true,
    allowedHosts: [
      'localhost',
      'localhost:3000',
      'localhost:5173',
      // Add ngrok domains if environment variables are set
      ...(process.env.VITE_FRONTEND_URL ? [new URL(process.env.VITE_FRONTEND_URL).hostname] : []),
      ...(process.env.VITE_API_URL ? [new URL(process.env.VITE_API_URL).hostname] : [])
    ]
  }
})
