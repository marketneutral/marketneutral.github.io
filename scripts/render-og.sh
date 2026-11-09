#!/usr/bin/env bash
# Render scripts/og-card.html to src/assets/og-default.png (1200x630), the link-preview image.
# Headless Chrome leaves the bottom of an exact-size viewport unpainted, so render taller and crop.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
google-chrome --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=10000 \
  --window-size=1200,900 --screenshot="$tmp/card.png" "file://$PWD/scripts/og-card.html" 2>/dev/null
python3 -c "from PIL import Image; Image.open('$tmp/card.png').crop((0,0,1200,630)).save('src/assets/og-default.png', optimize=True)"
rm -rf "$tmp"
python3 -c "from PIL import Image; print('wrote src/assets/og-default.png', Image.open('src/assets/og-default.png').size)"
