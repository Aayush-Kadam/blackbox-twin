import { build } from "esbuild";
import { spawnSync } from "node:child_process";
await build({
  entryPoints: ["tests/render.test.jsx"],
  outfile: ".test-build.cjs",
  bundle: true,
  platform: "node",
  format: "cjs",
  define: { "process.env.NODE_ENV": '"production"' },
});
const result = spawnSync(process.execPath, ["--test", ".test-build.cjs"], {
  stdio: "inherit",
});
process.exitCode = result.status ?? 1;
