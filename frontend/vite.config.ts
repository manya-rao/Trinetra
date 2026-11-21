import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

const backendPort = process.env.BACKEND_PORT || '8000';
const backendTarget = `http://localhost:${backendPort}`;

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    fs: {
      allow: ['..'],
    },
    proxy: {
      '/analyze': backendTarget,
      '/passport': backendTarget,
      '/p': backendTarget,
      '/match_hash': backendTarget,
      '/health': backendTarget,
      '/files': backendTarget,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
