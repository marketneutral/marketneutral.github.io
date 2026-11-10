#!/usr/bin/env node
//
// scripts/render-qmd.mjs
//
// Renders a Quarto notebook (.qmd) to a bundled post at
//   src/posts/<slug>/index.md
// with any generated plot assets moved to
//   src/posts/<slug>/<slug>_files/
//
// Usage: npm run render -- notebooks/2026-06-12-my-post.qmd
//

import { execSync } from "node:child_process";
import {
  existsSync,
  rmSync,
  renameSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

const qmdPath = process.argv[2];

if (!qmdPath) {
  console.error("Usage: npm run render -- notebooks/your-notebook.qmd");
  process.exit(1);
}

if (!existsSync(qmdPath)) {
  console.error(`File not found: ${qmdPath}`);
  process.exit(1);
}

if (!qmdPath.endsWith(".qmd")) {
  console.error(`Expected a .qmd file, got: ${qmdPath}`);
  process.exit(1);
}

const slug = path.basename(qmdPath, ".qmd");
const qmdDir = path.dirname(qmdPath);

// Strip leading YYYY-MM-DD- from the bundle dir so the on-disk path matches
// the URL Eleventy will serve (which date-strips automatically). The full
// dated slug is still used for the *_files/ directory because Quarto
// references it by that name in the markdown image paths.
const urlSlug = slug.replace(/^\d{4}-\d{2}-\d{2}-/, "");
const postDir = path.join("src", "posts", urlSlug);

// quick check that quarto is available
try {
  execSync("quarto --version", { stdio: "ignore" });
} catch {
  console.error("Quarto not found on PATH.");
  console.error("Install: https://quarto.org/docs/get-started/");
  process.exit(1);
}

console.log(`\nRendering ${qmdPath}`);
console.log(`Target:    ${postDir}/index.md\n`);

// Clean any previous render so re-renders are clean
if (existsSync(postDir)) {
  rmSync(postDir, { recursive: true, force: true });
}
mkdirSync(postDir, { recursive: true });

// Run Quarto. Output is gfm (GitHub-flavored markdown) with frontmatter preserved.
try {
  execSync(`quarto render "${qmdPath}" --to gfm`, { stdio: "inherit" });
} catch {
  console.error("\nQuarto render failed.");
  process.exit(1);
}

// Quarto writes its output next to the .qmd:
//   notebooks/<slug>.md
//   notebooks/<slug>_files/        (figures, if any)
const renderedMd = path.join(qmdDir, `${slug}.md`);
const renderedFiles = path.join(qmdDir, `${slug}_files`);

if (!existsSync(renderedMd)) {
  console.error(`Expected output not found at: ${renderedMd}`);
  process.exit(1);
}

// Move the .md into the bundle as index.md
renameSync(renderedMd, path.join(postDir, "index.md"));

// Move the _files directory if it exists (it won't if the notebook produced no figures)
if (existsSync(renderedFiles)) {
  renameSync(renderedFiles, path.join(postDir, `${slug}_files`));
}

// Quarto writes a captioned figure as ![caption](file). The site shows alt text
// nowhere, so turn each one into <figure> + <figcaption>, which styles.css knows:
// "wide" breaks out of the text column for wide plots, "diagram" centres narrow ones.
const imageWidthPx = (file) => {
  if (!existsSync(file)) return 0;
  if (file.endsWith(".svg")) {
    const m = readFileSync(file, "utf8").match(/<svg[^>]*\swidth="([\d.]+)(pt|px)?"/);
    return m ? parseFloat(m[1]) * (m[2] === "pt" ? 96 / 72 : 1) : 0;
  }
  if (file.endsWith(".png")) return readFileSync(file).readUInt32BE(16);
  return 0;
};
// Quarto also writes a title block (# Title, then the date) at the top of the body, which the
// post layout already renders. And its printed cell outputs are indented code blocks, which
// Eleventy's markdown-it does not recognise, so fence them.
const stripTitleBlock = (text) =>
  text.replace(/^(---\n[\s\S]*?\n---\n)\s*# [^\n]+\n\n(\d{4}-\d{2}-\d{2}\n\n)?/, "$1\n");
const fenceIndentedOutputs = (text) => {
  const lines = text.split("\n"), out = [];
  let inFence = false, inIndent = false;
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^```/.test(l)) {
      if (inIndent) { out.push("```"); inIndent = false; }
      inFence = !inFence; out.push(l); continue;
    }
    if (inFence) { out.push(l); continue; }
    if (inIndent) {
      if (/^    /.test(l)) { out.push(l.slice(4)); continue; }
      if (l.trim() === "" && /^    /.test(lines[i + 1] || "")) { out.push(""); continue; }
      out.push("```"); inIndent = false;
    }
    const prev = out.slice().reverse().find((x) => x.trim() !== "") || "";
    if (/^    \S/.test(l) && (lines[i - 1] || "").trim() === "" && !/^(\s*[-*+]|\s*\d+\.)\s/.test(prev) && !/^\s/.test(prev)) {
      out.push("```"); out.push(l.slice(4)); inIndent = true; continue;
    }
    out.push(l);
  }
  if (inIndent) out.push("```");
  return out.join("\n");
};
const indexMd = path.join(postDir, "index.md");
const md = fenceIndentedOutputs(stripTitleBlock(readFileSync(indexMd, "utf8"))).replace(
  /^!\[([^\]]*)\]\(([^)\s]+)\)[ \t]*$/gm,
  (_, alt, src) => {
    const caption = alt.replace(/\s+/g, " ").trim();
    const cls = imageWidthPx(path.join(postDir, src)) >= 850 ? "wide" : "diagram";
    return [`<figure class="${cls}">`,
            `<img src="${src}" alt="${caption.replace(/"/g, "&quot;")}">`,
            caption ? `<figcaption>${caption}</figcaption>` : "",
            `</figure>`].filter(Boolean).join("\n");
  });
writeFileSync(indexMd, md);

console.log(`\n✓ Rendered to ${postDir}/index.md`);
console.log(`  Preview: npm start, then http://localhost:8080/posts/${urlSlug}/\n`);
