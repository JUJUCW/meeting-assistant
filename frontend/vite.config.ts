import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/transcribe':   'http://localhost:8000',
      '/health':       'http://localhost:8000',
      '/status':       'http://localhost:8000',
      '/result':       'http://localhost:8000',
      '/meetings':     'http://localhost:8000',
      '/categories':   'http://localhost:8000',
      '/action-items': 'http://localhost:8000',
      '/translate/':   'http://localhost:8000',
    },
  },
})
