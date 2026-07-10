import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server proxies /api/* + /health to the backend so the SPA never
// talks to a different origin in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8002',
      '/health': 'http://localhost:8002',
    },
  },
});
