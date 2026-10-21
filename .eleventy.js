module.exports = function (eleventyConfig) {
  // Syntax highlighting for fenced code blocks (Python, JS, etc.)
  const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
  eleventyConfig.addPlugin(syntaxHighlight);

  // KaTeX math rendering for $...$ (inline) and $$...$$ (display) blocks.
  // Catches Quarto's LaTeX math before markdown-it can chew on the backslashes.
  const markdownItKatex = require("@vscode/markdown-it-katex").default;
  eleventyConfig.amendLibrary("md", (md) => md.use(markdownItKatex));

  // copy /assets straight through to the build
  eleventyConfig.addPassthroughCopy("src/assets");

  // copy plot assets that live alongside bundled posts (for .qmd-rendered notebooks)
  eleventyConfig.addPassthroughCopy("src/posts/**/*.png");
  eleventyConfig.addPassthroughCopy("src/posts/**/*.jpg");
  eleventyConfig.addPassthroughCopy("src/posts/**/*.jpeg");
  eleventyConfig.addPassthroughCopy("src/posts/**/*.gif");
  eleventyConfig.addPassthroughCopy("src/posts/**/*.svg");
  eleventyConfig.addPassthroughCopy("src/posts/**/*.webp");

  // ── filters ───────────────────────────────────────────────────────────

  // RFC 3339 timestamp — required by the Atom feed
  eleventyConfig.addFilter("rfc3339", (date) => new Date(date).toISOString());

  // 2026.05.28
  eleventyConfig.addFilter("dateISO", (date) => {
    const d = new Date(date);
    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, "0");
    const dy = String(d.getDate()).padStart(2, "0");
    return `${yr}.${mo}.${dy}`;
  });

  // 047
  eleventyConfig.addFilter("padNum", (num) => String(num).padStart(3, "0"));

  // "8 MIN" — rough estimate
  eleventyConfig.addFilter("readTime", (content) => {
    const text = String(content).replace(/<[^>]*>/g, " ");
    const words = text.split(/\s+/).filter(Boolean).length;
    const mins = Math.max(1, Math.round(words / 220));
    return `${mins} MIN`;
  });

  // ── collections ───────────────────────────────────────────────────────

  // newest first — matches both flat .md and bundled .md/index.md posts
  eleventyConfig.addCollection("posts", (api) =>
    api.getFilteredByGlob("src/posts/**/*.md").reverse()
  );

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};
