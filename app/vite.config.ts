import { defineConfig } from 'vite';
export default defineConfig({
  envDir: false, // Never load .env, including during local demo development/builds.
  server: { host: '127.0.0.1', port: 1420, strictPort: true, watch: { ignored: ['**/src-tauri/**'] } },
  clearScreen: false,
});
