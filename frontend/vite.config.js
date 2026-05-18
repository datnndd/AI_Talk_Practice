import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("@phosphor-icons")) return "icons";
          if (id.includes("@react-oauth")) return "auth-google";
          if (id.includes("react-router")) return "router";
          if (id.includes("react") || id.includes("scheduler")) return "react-vendor";
          if (id.includes("framer-motion")) return "motion";
          if (id.includes("pixi-live2d-display")) return "live2d";
          if (id.includes("pixi.js")) return "pixi";
          if (id.includes("axios")) return "http";
          return "vendor";
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  plugins: [
    react(),
    tailwindcss(),
  ],
})
