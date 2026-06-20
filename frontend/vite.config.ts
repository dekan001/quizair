import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  // относительные пути — важно для деплоя на Vercel из подкаталога и для Mini App
  base: "./",
});
