// Build-time data. cssVersion is a short hash of styles.css so the
// stylesheet URL changes whenever the CSS does, defeating browser caches.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const css = fs.readFileSync(path.join(__dirname, "../assets/styles.css"));

module.exports = {
  cssVersion: crypto.createHash("md5").update(css).digest("hex").slice(0, 8),
};
