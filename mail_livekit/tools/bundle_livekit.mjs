import {build} from "esbuild";
import {fileURLToPath} from "node:url";
import path from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "static", "lib", "bundles");

await build({
  entryPoints: [path.join(root, "tools", "livekit_vendor_entry.js")],
  bundle: true,
  format: "iife",
  platform: "browser",
  sourcemap: true,
  outdir: outDir,
  target: ["es2020"],
  minify: false,
  define: {
    "process.env.NODE_ENV": '"production"'
  },
});

console.log("Built LiveKit vendor bundle into", outDir);
