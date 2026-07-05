#!/bin/bash
# One-time setup for headless screenshot verification in the Claude
# sandbox (or any Linux box without root). Safe to re-run.
#
# After running, use:
#   export LD_LIBRARY_PATH=$HOME/stublibs
#   export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
#   python3 build/screenshot.py
set -e

pip install playwright --break-system-packages -q
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 \
  "$(python3 -c 'import site;print(site.USER_BASE)')/bin/playwright" install chromium || true

# Chromium links libXdamage but never calls it headlessly; stub it out
# when the real library can't be installed (no root, blocked apt).
mkdir -p "$HOME/stublibs"
cat > "$HOME/stublibs/xdamage_stub.c" <<'EOF'
long XDamageCreate(void*a,long b,int c){return 0;}
void XDamageDestroy(void*a,long b){}
int XDamageQueryExtension(void*a,int*eb,int*er){if(eb)*eb=0;if(er)*er=0;return 0;}
void XDamageSubtract(void*a,long b,long c,long d){}
EOF
gcc -shared -fPIC -o "$HOME/stublibs/libXdamage.so.1" "$HOME/stublibs/xdamage_stub.c"
echo "setup done"
