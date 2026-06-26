import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/login': 'http://127.0.0.1:8000',
      '/procesar': 'http://127.0.0.1:8000',
      '/confirmar': 'http://127.0.0.1:8000',
      '/rechazar': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
