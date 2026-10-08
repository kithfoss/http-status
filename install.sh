#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-/usr/local/bin/http-status}"

if [ -f "$TARGET" ] && [ ! -w "$TARGET" ]; then
    echo "http-status: $TARGET is not writable — try: sudo $0" >&2
    exit 1
fi

ln -sf "$SCRIPT_DIR/http_status.py" "$TARGET"
chmod +x "$SCRIPT_DIR/http_status.py"
echo "http-status installed → $TARGET"
