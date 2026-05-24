#!/bin/sh
# Install the if-pbm-open-demo CLI from GitHub.
# Usage: curl -sSf https://raw.githubusercontent.com/thomas-boulier/if-pbm-open-demo/main/install.sh | sh
set -eu

REPO="git+https://github.com/thomas-boulier/if-pbm-open-demo"

if command -v uv >/dev/null 2>&1; then
    echo "Installing if-pbm-open-demo with uv..."
    uv tool install "$REPO"
elif command -v pipx >/dev/null 2>&1; then
    echo "Installing if-pbm-open-demo with pipx..."
    pipx install "$REPO"
else
    echo "Error: neither uv nor pipx found." >&2
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

echo
echo "Done. Run the demo with:"
echo "    if-pbm-demo demo"
