import { build } from "esbuild";
import { mkdir, copyFile, readFile, writeFile } from "node:fs/promises";

const out = "../src/blackbox_twin/workbench_assets";
await mkdir(out, { recursive: true });
await build({
  entryPoints: ["src/main.jsx"],
  bundle: true,
  minify: true,
  outfile: `${out}/app.js`,
  define: { "process.env.NODE_ENV": '"production"' },
  target: ["es2020"],
  legalComments: "linked",
});
await copyFile("index.html", `${out}/index.html`);
const notices = [];
for (const name of ["react", "react-dom", "scheduler"]) {
  const manifest = JSON.parse(
    await readFile(`node_modules/${name}/package.json`, "utf8"),
  );
  const license = await readFile(`node_modules/${name}/LICENSE`, "utf8");
  notices.push(`${name} ${manifest.version}\n${license}`);
}
await writeFile(`${out}/THIRD_PARTY_LICENSES.txt`, notices.join("\n\n"));
console.log(
  "Built local React assets; no CDN or browser package downloads required.",
);
