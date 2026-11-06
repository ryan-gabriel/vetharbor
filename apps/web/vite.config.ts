import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    // Hermetic: a developer's git-ignored apps/web/.env.local must not change
    // what these tests assert. Suites that need a base URL stub it themselves.
    env: { VITE_API_URL: "" },
    // WSL1 + Windows mounts make fork workers time out; threads are reliable.
    pool: "threads",
    setupFiles: ["./src/test/setup.ts"],
    restoreMocks: true,
    coverage: {
      provider: "v8",
      include: ["src/lib/**", "src/components/**"],
      thresholds: { lines: 70, functions: 70, statements: 70, branches: 65 },
      reporter: ["text", "lcov"],
    },
  },
});
