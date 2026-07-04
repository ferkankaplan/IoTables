import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const runtimeEnv = globalThis as { process?: { env?: Record<string, string | undefined> } };
const apiProxyTarget =
  runtimeEnv.process?.env?.IOTABLES_API_PROXY_TARGET ?? "http://127.0.0.1:8000";
const devServerHost = runtimeEnv.process?.env?.IOTABLES_DEV_SERVER_HOST ?? "127.0.0.1";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: devServerHost,
    port: 5173,
    proxy: {
      "/api": apiProxyTarget
    }
  }
});
