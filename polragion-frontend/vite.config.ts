import {defineConfig, loadEnv} from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";
import fs from "fs";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")

  const https =
    env.DEV_HTTPS === "true"
      ? {
        key: fs.readFileSync(
          fileURLToPath(new URL("../docker/certs/lan-key.pem", import.meta.url)),
        ),
        cert: fs.readFileSync(
          fileURLToPath(new URL("../docker/certs/lan-cert.pem", import.meta.url)),
        ),
      }
      : undefined

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      https: https,
    },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
  }
})
