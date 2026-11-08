/* global process */
// Vite usado SO nos testes e2e: porta livre e proxy /api -> backend temporario.
// Assim o navegador fala com a mesma origem e nao depende do CORS (que so libera a porta 5173).
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  root: process.cwd(),
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.E2E_FRONT_PORT),
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.E2E_API_URL,
        rewrite: (caminho) => caminho.replace(/^\/api/, ''),
      },
    },
  },
})
