// Hover tooltips for the progress chart. A top-panel dot shows the trial before the test (claim and qex); a
// bottom-panel dot shows it after (the evaluator's numbers, the six slices of one deal, the agent's outcome).
// Reads progress-hover.json (written by figures.py), whose positions are fractions of the image,
// and lays invisible targets over the <img> in figure#progress, so the chart stays a plain SVG.
(function () {
  const base = document.currentScript.src.replace(/[^/]*$/, "");
  const fig = document.getElementById("progress");
  const img = fig && fig.querySelector("img");
  if (!img) return;

  const css = `
    .ph-wrap { position: relative; }
    .ph-dot { position: absolute; width: 16px; height: 16px; margin: -8px 0 0 -8px; border-radius: 50%;
              cursor: pointer; background: transparent; border: 0; padding: 0; }
    .ph-dot:hover, .ph-dot.ph-on { box-shadow: 0 0 0 2px #e8eaf0; }
    .ph-tip { position: absolute; z-index: 10; max-width: min(560px, 90vw); padding: 10px 12px;
              background: #131927; border: 1px solid #2a3344; border-radius: 6px; color: #c0c4cf;
              font: 12px/1.45 "IBM Plex Mono", Menlo, monospace; text-align: left; pointer-events: none;
              box-shadow: 0 6px 24px rgba(0,0,0,.45); }
    .ph-tip .ph-head { color: #e8eaf0; font-weight: 600; margin-bottom: 4px; }
    .ph-tip .ph-keep { color: #3ee87a; } .ph-tip .ph-reset { color: #6b7280; }
    .ph-tip .ph-claim { color: #9aa1ad; margin: 4px 0 8px; white-space: normal; }
    .ph-tip pre { margin: 0; padding: 0; background: none; border: 0; color: #e8eaf0;
                  font: inherit; white-space: pre-wrap; overflow-wrap: anywhere; }
    .ph-tip .ph-row { color: #c0c4cf; } .ph-tip .ph-bad { color: #ff6b4a; } .ph-tip .ph-good { color: #3ee87a; }
    .ph-tip .ph-sub { color: #6b7280; margin: 8px 0 2px; }
    .ph-tip svg { display: block; margin: 2px 0 6px; }`;
  document.head.appendChild(Object.assign(document.createElement("style"), { textContent: css }));

  const wrap = document.createElement("div");
  wrap.className = "ph-wrap";
  img.parentNode.insertBefore(wrap, img);
  wrap.appendChild(img);
  const tip = document.createElement("div");
  tip.className = "ph-tip";
  tip.hidden = true;
  wrap.appendChild(tip);

  const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
  let pinned = null;

  const f2 = (x) => (x >= 0 ? "+" : "") + x.toFixed(2);
  const head = (t, what) => {
    const cls = t.status === "reset" ? "ph-reset" : "ph-keep";
    return `<div class="ph-head">${t.trial === 0 ? "Seed" : "Trial " + t.trial} · <span class="${cls}">${t.status}</span>` +
      `${t.label ? " · " + esc(t.label) : ""} · ${what}</div>`;
  };
  function slices(folds) {                                  // six bars, Sharpe of each slice, worst slice (by score) in red
    const W = 300, H = 96, top = 12, floor = 62, lo = Math.min(-0.5, ...folds.map((f) => f.sharpe)), hi = Math.max(2.5, ...folds.map((f) => f.sharpe));
    const y = (v) => top + (floor - top) * (hi - v) / (hi - lo), bw = W / folds.length;
    const worst = folds.reduce((a, f, i) => (f.utility < folds[a].utility ? i : a), 0);
    let g = `<line x1="0" x2="${W}" y1="${y(0)}" y2="${y(0)}" stroke="#2a3344"/>`;
    folds.forEach((f, i) => {
      const x = i * bw + 8, w = bw - 16, y0 = y(Math.max(f.sharpe, 0)), h = Math.abs(y(f.sharpe) - y(0));
      const c = i === worst ? "#ff6b4a" : "#3ee87a";
      g += `<rect x="${x}" y="${y0}" width="${w}" height="${Math.max(h, 1)}" fill="${c}" opacity="0.85"/>`;
      // value above the bar when positive; above the zero line when negative, where the bar hangs down out of the way
      g += `<text x="${x + w / 2}" y="${(f.sharpe >= 0 ? y0 : y(0)) - 3}" fill="#c0c4cf" font-size="10" text-anchor="middle">${f.sharpe.toFixed(2)}</text>`;
      g += `<text x="${x + w / 2}" y="${H - 12}" fill="#6b7280" font-size="9.5" text-anchor="middle">${f.years.slice(2, 4)}–${f.years.slice(7)}</text>`;
    });
    return `<svg width="${W}" height="${H - 8}" viewBox="0 0 ${W} ${H - 8}" font-family="IBM Plex Mono, Menlo, monospace">${g}</svg>`;
  }
  // qex syntax colouring with the site's own code-block token classes: let/in keywords, functions, numbers,
  // strings ('sector'), the names being bound, and operators
  function highlight(src) {
    const re = /(\s+)|\b(let|in)\b|('[^']*')|(\d+(?:\.\d+)?)|([A-Za-z_]\w*)(?=\s*\()|([A-Za-z_]\w*)(?=\s*=(?!=))|([A-Za-z_]\w*)|([<>]=?|==|[-+*\/&|=])|(.)/g;
    let out = "", m;
    const span = (cls, x) => `<span class="token ${cls}">${esc(x)}</span>`;
    const bound = new Set([...src.matchAll(/(?:^[ \t]*(?:let[ \t]+)?|\blet[ \t]+)([A-Za-z_]\w*)[ \t]*=(?!=)/gm)].map((x) => x[1]));   // coloured wherever used
    while ((m = re.exec(src))) {
      if (m[1]) out += m[1];
      else if (m[2]) out += span("keyword", m[2]);
      else if (m[3]) out += span("string", m[3]);
      else if (m[4]) out += span("number", m[4]);
      else if (m[5]) out += span("function", m[5]);
      else if (m[6]) out += span("property", m[6]);
      else if (m[7]) out += bound.has(m[7]) ? span("property", m[7]) : esc(m[7]);
      else if (m[8]) out += span("operator", m[8]);
      else out += span("punctuation", m[9]);
    }
    return out;
  }
  function before(t) {
    return head(t, `score ${t.utility.toFixed(3)} · worst ${t.worst.toFixed(3)}`) +
      `<div class="ph-claim">${esc(t.claim)}</div><pre>${highlight(t.qex)}</pre>`;
  }
  function after(t) {
    const e = t.eval;
    let h = head(t, "what the evaluator said");
    if (t.best) {
      const su = t.utility > t.best[0] + 0.03, sw = t.worst >= t.best[1] - 0.13;
      h += `<div class="ph-row">score <span class="${su ? "ph-good" : "ph-bad"}">${t.utility.toFixed(3)}</span>` +
        ` (to keep: above ${(t.best[0] + 0.03).toFixed(3)}) · worst <span class="${sw ? "ph-good" : "ph-bad"}">${t.worst.toFixed(3)}</span>` +
        ` (no lower than ${(t.best[1] - 0.13).toFixed(3)})</div>`;
    }
    if (e) {
      h += `<div class="ph-row">eligible <span class="${e.eligible ? "ph-good" : "ph-bad"}">${e.eligible ? "yes" : "no"}</span> · margin ${e.margin} bps` +
        ` · Sharpe ${e.sharpe.toFixed(2)} · ${f2(e.ret * 100)}%/yr · turnover ${e.turnover} · crash-state Sharpe ${e.crash.toFixed(2)}</div>` +
        `<div class="ph-sub">Sharpe on the six slices of one of the fifty deals (worst slice in red), by the years each covers</div>` + slices(e.folds);
    }
    return h + `<div class="ph-sub">the agent's outcome</div><div class="ph-claim" style="margin-top:0">${esc(t.outcome)}</div>`;
  }
  function show(t, dot, panel) {
    tip.innerHTML = panel === "top" ? before(t) : after(t);
    const W = wrap.clientWidth, x = dot.offsetLeft, y = dot.offsetTop;
    tip.style.maxWidth = Math.min(560, W) + "px";                         // never wider than the chart
    tip.hidden = false;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    tip.style.left = Math.max(0, Math.min(W - tw, x + 14 - (x > W / 2 ? tw + 28 : 0))) + "px";
    tip.style.top = (panel === "bottom" ? y - th - 12 : y + 12) + "px";   // results open upward, over the top panel
  }
  function hide() { if (!pinned) tip.hidden = true; }

  fetch(base + "progress-hover.json").then((r) => r.json()).then((trials) => {
    for (const t of trials) {
      for (const [panel, pos] of [["top", t.top], ["bottom", t.bottom]]) {
        const dot = document.createElement("button");
        dot.className = "ph-dot";
        dot.setAttribute("aria-label", (t.trial === 0 ? "seed" : "trial " + t.trial) + ", " + t.status);
        dot.style.left = pos[0] * 100 + "%";
        dot.style.top = pos[1] * 100 + "%";
        dot.addEventListener("mouseenter", () => show(t, dot, panel));
        dot.addEventListener("mouseleave", hide);
        dot.addEventListener("focus", () => show(t, dot, panel));
        dot.addEventListener("blur", hide);
        dot.addEventListener("click", (e) => {             // tap to pin on touch screens
          e.stopPropagation();
          if (pinned) pinned.classList.remove("ph-on");
          pinned = pinned === dot ? null : dot;
          if (pinned) { dot.classList.add("ph-on"); show(t, dot, panel); } else tip.hidden = true;
        });
        wrap.appendChild(dot);
      }
    }
  });
  document.addEventListener("click", () => { if (pinned) { pinned.classList.remove("ph-on"); pinned = null; tip.hidden = true; } });
})();
