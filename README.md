# Speculative Decoding

A terminal-aesthetic blog. Built with [Eleventy](https://www.11ty.dev/). Deploys to GitHub Pages on every push.

**RSS/Atom feed** is at `/feed.xml` once deployed — change the site URL in `src/_data/site.json` when you set up a custom domain.

**License:** code is Apache 2.0 (see `LICENSE`); post text is [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

---

## How this works

You write posts as Markdown files in `src/posts/`. Eleventy turns them into HTML using the layouts in `src/_includes/`. GitHub Actions builds the site on every push and publishes it to GitHub Pages.

```
.
├── .eleventy.js              ← build config
├── .github/workflows/        ← auto-deploy on push
├── package.json
├── src/
│   ├── _includes/
│   │   ├── base.njk          ← html shell, top bar, footer
│   │   └── post.njk          ← individual post layout
│   ├── assets/
│   │   └── styles.css        ← all styling (edit colors here)
│   ├── index.njk             ← homepage
│   └── posts/
│       ├── posts.json        ← defaults for every post
│       └── *.md              ← your actual blog posts
└── _site/                    ← built site (gitignored, don't edit)
```

---

## First-time setup

You need **Node.js 20+** installed locally. Check with `node --version`.

```bash
# 1. install dependencies
npm install

# 2. run the dev server (live reload on save)
npm start
# → opens at http://localhost:8080

# 3. one-off build
npm run build
# → outputs to _site/
```

---

## Adding a new post

Create a new file in `src/posts/` named `YYYY-MM-DD-some-slug.md`:

```markdown
---
title: How I learned to stop worrying and love the build step
date: 2026-06-12
tag: ESSAY
description: One-sentence summary that shows up on the homepage.
---

Your post body in **Markdown**. Headings, code blocks, lists, blockquotes —
all styled to match the terminal aesthetic.

## Section heading

More writing.

```bash
echo "code blocks render with a dark terminal theme"
```

> Blockquotes get a red left border.
```

That's it. The post will:

- automatically appear on the homepage (newest first)
- get a numbered index (047, 046, 045…)
- show up in the archive list with date, tag, and computed reading time
- have its own page at `/posts/some-slug/`

The newest post becomes the **featured** entry at the top.

---

## Deploying to GitHub Pages

### One-time setup

1. **Create a new GitHub repo.** Two options for the URL:
   - `username.github.io` → site serves at `https://username.github.io/` (recommended)
   - `any-repo-name` → site serves at `https://username.github.io/any-repo-name/` (you'll need to set `pathPrefix` in `.eleventy.js`)

2. **Push this project to the repo:**
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git branch -M main
   git remote add origin https://github.com/USERNAME/REPO.git
   git push -u origin main
   ```

3. **Enable GitHub Pages with Actions as the source:**
   - Go to your repo on github.com
   - **Settings → Pages**
   - Under "Build and deployment", set **Source** to **GitHub Actions**
   - That's the only setting you need to touch

4. **Watch the first deploy:**
   - Click the **Actions** tab
   - You'll see "Build & Deploy" running
   - When it finishes (about a minute), your site is live

### Every deploy after that

```bash
# write a new post...
git add src/posts/2026-06-12-some-slug.md
git commit -m "new post"
git push
```

The Action runs automatically. Site is live in about a minute.

---

## Adding a notebook post (.qmd)

For posts with code and plots, write a `.qmd` file (Quarto Markdown) in `notebooks/`, render it locally, and commit the output.

### One-time setup

Install Quarto: <https://quarto.org/docs/get-started/>. Test with `quarto --version`.

You'll also need Python with whatever libraries you import (matplotlib, numpy, pandas, etc.). The sample notebook uses just numpy + matplotlib.

### Authoring

Create a file like `notebooks/2026-06-12-my-analysis.qmd`:

````markdown
---
title: My analysis title
date: 2026-06-12
tag: ANALYSIS
description: One-sentence summary for the homepage.
---

Some intro text.

The model:
$$
y_i = \beta_0 + \beta_1 x_i + \varepsilon_i
$$

```{python}
import numpy as np
import matplotlib.pyplot as plt

# your code
plt.plot(...)
plt.show()
```

More text. Inline math works too: $\hat{\beta} = (X^\top X)^{-1} X^\top y$.
````

### Rendering and publishing

```bash
npm run render -- notebooks/2026-06-12-my-analysis.qmd
```

This executes the notebook, captures plot output, and produces a bundled post at `src/posts/my-analysis/index.md` (with plots saved alongside as PNGs). Then commit and push as normal:

```bash
git add src/posts/my-analysis notebooks/2026-06-12-my-analysis.qmd
git commit -m "new post"
git push
```

GitHub Pages rebuilds automatically — no Quarto needed in CI.

### Julia notebooks

Notebooks can also be written in Julia. Set `engine: julia` in the front
matter and use ```` ```{julia} ```` code cells; Quarto runs them through its
native Julia engine (no Jupyter needed). Requirements:

- **Julia 1.10** on your `PATH` (install with [juliaup](https://github.com/JuliaLang/juliaup):
  `juliaup add 1.10 && juliaup default 1.10`). Quarto 1.6's bundled
  `QuartoNotebookRunner` does not build on newer Julia releases.
- The package environment in `notebooks/Project.toml` + `Manifest.toml`.
  Quarto activates it automatically because it sits next to the `.qmd`.
  First time: `julia --project=notebooks -e 'using Pkg; Pkg.instantiate()'`.
- `include("_oos_style.jl")` after `using Plots` applies the site palette,
  the Julia twin of `_oos_style.py`.

Render exactly as for Python notebooks: `npm run render -- notebooks/<file>.qmd`.
Results are frozen in `notebooks/_freeze/` (gitignored), so prose-only
edits re-render without re-executing the code.

### What's set up for notebook posts

- **KaTeX math rendering** — `$inline$` and `$$display$$` math render server-side at build
- **Python (and other language) syntax highlighting** — via Prism, themed to match the site palette
- **Plot images** — automatically passthrough-copied alongside the post

---



### Branding (site name, tagline)

Edit `src/_includes/base.njk` (top bar, title tag) and `src/index.njk` (hero section, about text).

### Colors

All theming is in `src/assets/styles.css` at the top:

```css
:root {
  --paper:   #f1ede4;   /* background */
  --ink:     #0a0a0a;   /* text */
  --accent:  #c8371f;   /* oxide red — try #0a6a3a for green, #c8861f for amber */
  ...
}
```

### Fonts

Currently uses IBM Plex Mono from Google Fonts. To swap:
1. Change the `<link>` in `src/_includes/base.njk`
2. Change `font-family` at the top of `src/assets/styles.css`

JetBrains Mono, Fira Code, or Space Mono all work as drop-in replacements. Berkeley Mono (paid) is the holy grail if you want to pay for it.

### Stats block

The homepage stat grid (`POSTS PUBLISHED`, `SUBSCRIBERS`, etc.) is in `src/index.njk`. "Posts published" and "Last update" are auto-computed; the others are hardcoded — edit them or remove the block entirely.

---

## Custom domain

If you want `stdout.yourdomain.com` instead of `username.github.io`:

1. Add a `CNAME` file at `src/CNAME` containing just the domain:
   ```
   stdout.yourdomain.com
   ```
2. At your DNS provider, add a `CNAME` record pointing to `username.github.io`
3. In **Settings → Pages**, fill in the **Custom domain** field

---

## Local preview tips

- `npm start` runs a live dev server — saves trigger a reload
- The featured-post block uses your newest post by date, so to "feature" a different post, edit its date frontmatter
- Reading time is computed from word count (220 wpm) — no manual counting

---

## Troubleshooting

**Build fails with "command not found: eleventy"** → run `npm install` first.

**Site deploys but assets 404** → you used a non-`username.github.io` repo name. Add this to `.eleventy.js`:
```js
return {
  pathPrefix: "/your-repo-name/",
  dir: { ... }
}
```
and update the asset links in `base.njk` to use `{{ '/assets/styles.css' | url }}`.

**Posts don't appear** → check the frontmatter is valid YAML (three dashes top and bottom, no smart quotes).

---

Built with care. Modify with confidence.
