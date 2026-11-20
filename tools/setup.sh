#!/usr/bin/env bash
# One-time setup of a fresh machine (a scheduled run starts on one). Run from the repository root:  bash tools/setup.sh
# It installs what the generators and the checks need, fetches the pdf branch, and prints READY or what is missing.
set -u
cd "$(dirname "$0")/.."
miss=""

command -v lilypond >/dev/null 2>&1 || { (apt-get update -qq && apt-get install -y -qq lilypond) >/dev/null 2>&1; }
command -v lilypond >/dev/null 2>&1 || miss="$miss lilypond"

python3 -c "import reportlab, pypdf, PIL, qrcode, cryptography" 2>/dev/null \
  || pip install -q --break-system-packages reportlab pypdf pillow "qrcode[pil]" cryptography >/dev/null 2>&1
python3 -c "import reportlab, pypdf, PIL, qrcode, cryptography" 2>/dev/null || miss="$miss python-packages"

fc-list 2>/dev/null | grep -qi poppins || miss="$miss font:Poppins"
fc-list 2>/dev/null | grep -qi dejavu || miss="$miss font:DejaVu"

[ -d tools/node_modules/abcjs ] || (cd tools && npm install --silent >/dev/null 2>&1)
[ -d tools/node_modules/abcjs ] || miss="$miss node-packages"
node -e "require('playwright')" 2>/dev/null || miss="$miss playwright"

git fetch -q origin main "+refs/heads/pdf:refs/remotes/origin/pdf" 2>/dev/null || miss="$miss git-fetch"

if [ -n "$miss" ]; then echo "SETUP: MISSING:$miss"; exit 1; fi
echo "SETUP: READY  (lilypond $(lilypond --version | head -1 | awk '{print $3}'), version $(cat VERSION 2>/dev/null))"
