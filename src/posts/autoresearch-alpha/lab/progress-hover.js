// Hover tooltips for the progress chart: each dot shows its trial's qex and claim.
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
                  font: inherit; white-space: pre; overflow: hidden; }`;
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

  function show(t, dot) {
    const status = t.status === "seed" ? "seed" : t.status;
    const cls = t.status === "reset" ? "ph-reset" : "ph-keep";
    tip.innerHTML =
      `<div class="ph-head">${t.trial === 0 ? "Seed" : "Trial " + t.trial} · <span class="${cls}">${status}</span>` +
      `${t.label ? " · " + esc(t.label) : ""} · score ${t.utility.toFixed(3)} · worst ${t.worst.toFixed(3)}</div>` +
      `<div class="ph-claim">${esc(t.claim)}</div><pre>${esc(t.qex)}</pre>`;
    tip.hidden = false;
    const W = wrap.clientWidth, x = dot.offsetLeft, y = dot.offsetTop;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    tip.style.left = Math.max(0, Math.min(W - tw, x + 14 - (x > W / 2 ? tw + 28 : 0))) + "px";
    tip.style.top = (y + th + 16 > wrap.clientHeight + 200 ? y - th - 12 : y + 12) + "px";
  }
  function hide() { if (!pinned) tip.hidden = true; }

  fetch(base + "progress-hover.json").then((r) => r.json()).then((trials) => {
    for (const t of trials) {
      for (const pos of [t.top, t.bottom]) {
        const dot = document.createElement("button");
        dot.className = "ph-dot";
        dot.setAttribute("aria-label", (t.trial === 0 ? "seed" : "trial " + t.trial) + ", " + t.status);
        dot.style.left = pos[0] * 100 + "%";
        dot.style.top = pos[1] * 100 + "%";
        dot.addEventListener("mouseenter", () => show(t, dot));
        dot.addEventListener("mouseleave", hide);
        dot.addEventListener("focus", () => show(t, dot));
        dot.addEventListener("blur", hide);
        dot.addEventListener("click", (e) => {             // tap to pin on touch screens
          e.stopPropagation();
          if (pinned) pinned.classList.remove("ph-on");
          pinned = pinned === dot ? null : dot;
          if (pinned) { dot.classList.add("ph-on"); show(t, dot); } else tip.hidden = true;
        });
        wrap.appendChild(dot);
      }
    }
  });
  document.addEventListener("click", () => { if (pinned) { pinned.classList.remove("ph-on"); pinned = null; tip.hidden = true; } });
})();
