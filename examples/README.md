# Examples

Demo posts and their Quarto sources, kept out of the build so they do not
appear on the blog. Eleventy only reads `src/`, so nothing here is published.

- `posts/` — rendered bundles (`index.md` plus figure assets) as produced by
  `scripts/render-qmd.mjs`.
- `notebooks/` — the `.qmd` sources. To re-render one, move it back to
  `notebooks/` (it needs `_quarto.yml` and `_oos_style.py` there) and run
  `npm run render -- notebooks/<name>.qmd`.
