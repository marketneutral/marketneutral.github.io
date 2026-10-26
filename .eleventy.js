module.exports = function (eleventyConfig) {
  // Syntax highlighting for fenced code blocks (Python, JS, etc.)
  const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
  eleventyConfig.addPlugin(syntaxHighlight, {
    // qex, the alpha language (see the qex post): let/in keywords, function calls, the names a let binds,
    // 'sector'-style group names, numbers and operators. The autoresearch-alpha tooltips use the same rules.
    init: ({ Prism }) => {
      Prism.languages.qex = {
        string: /'[^']*'/,
        keyword: /\b(?:let|in)\b/,
        function: /\b[A-Za-z_]\w*(?=\s*\()/,
        property: /\b[A-Za-z_]\w*(?=\s*=(?!=))/,
        number: /\b\d+(?:\.\d+)?\b/,
        operator: /[<>]=?|==|[-+*\/&|=]/,
        punctuation: /[()[\],]/,
      };
      // a name a let binds is coloured wherever it is used, not only where it is defined
      Prism.hooks.add("before-tokenize", (env) => {
        if (env.language !== "qex") return;
        const names = [...new Set([...env.code.matchAll(/\b([A-Za-z_]\w*)\s*=(?!=)/g)].map((m) => m[1]))];
        if (!names.length) return;
        const grammar = {};                                   // a fresh grammar per block, so names never leak between blocks
        for (const [k, v] of Object.entries(Prism.languages.qex)) {
          if (k === "number") grammar.variable = { pattern: new RegExp("\\b(?:" + names.join("|") + ")\\b(?!\\s*\\()"), alias: "property" };
          grammar[k] = v;
        }
        env.grammar = grammar;
      });
    },
  });

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
  // a post's lab/ folder holds source files shown as-is (program, evaluator, notebook), not pages
  eleventyConfig.ignores.add("src/posts/**/lab/**");
  eleventyConfig.addPassthroughCopy("src/posts/**/lab/**");

  // ── filters ───────────────────────────────────────────────────────────

  // RFC 3339 timestamp — required by the Atom feed
  eleventyConfig.addFilter("rfc3339", (date) => new Date(date).toISOString());

  // 2026.05.28 — front-matter dates are parsed as UTC midnight, so format
  // in UTC too; otherwise builds west of Greenwich show the previous day.
  eleventyConfig.addFilter("dateISO", (date) => {
    const d = new Date(date);
    const yr = d.getUTCFullYear();
    const mo = String(d.getUTCMonth() + 1).padStart(2, "0");
    const dy = String(d.getUTCDate()).padStart(2, "0");
    return `${yr}.${mo}.${dy}`;
  });

  // 047
  eleventyConfig.addFilter("padNum", (num) => String(num).padStart(3, "0"));

  // a post's number in the archive: oldest = 1, newest = total
  eleventyConfig.addFilter("postNum", (posts, url) => {
    const i = posts.findIndex((p) => p.url === url);
    return i < 0 ? posts.length : posts.length - i;
  });

  // word count of rendered content, tags stripped
  const wordCount = (content) =>
    String(content).replace(/<[^>]*>/g, " ").split(/\s+/).filter(Boolean).length;
  const WPM = 220;

  // "8 MIN" — rough estimate
  eleventyConfig.addFilter("readTime", (content) => {
    const mins = Math.max(1, Math.round(wordCount(content) / WPM));
    return `${mins} MIN`;
  });

  // "06:30" — mean read time over an array of rendered post bodies, as MM:SS.
  // Takes content strings (not post objects): templateContent must be read
  // in the template so Eleventy can defer rendering until posts are ready.
  eleventyConfig.addFilter("avgReadTime", (contents) => {
    if (!contents || !contents.length) return "00:00";
    const totalWords = contents.reduce((n, c) => n + wordCount(c), 0);
    const secs = Math.round((totalWords / contents.length / WPM) * 60);
    const mm = String(Math.floor(secs / 60)).padStart(2, "0");
    const ss = String(secs % 60).padStart(2, "0");
    return `${mm}:${ss}`;
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
