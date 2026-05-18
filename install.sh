#!/usr/bin/env sh
set -eu

BIN_DIR="${MBA_BIN_DIR:-$HOME/.local/bin}"
SKILL_HOME="${MBA_SKILL_HOME:-$HOME/.codex/skills}"
SKILL_NAME="mba-adversarial-evaluator"
DEFAULT_TARBALL_URL="https://github.com/kpince/MBA/archive/refs/heads/main.tar.gz"

cleanup() {
  if [ "${MBA_TMP_DIR:-}" != "" ] && [ -d "$MBA_TMP_DIR" ]; then
    rm -rf "$MBA_TMP_DIR"
  fi
}
trap cleanup EXIT

if [ "${MBA_AGENT_REPO:-}" != "" ]; then
  REPO_DIR="$MBA_AGENT_REPO"
else
  SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)"
  if [ "$SCRIPT_DIR" != "" ] && [ -d "$SCRIPT_DIR/skills/$SKILL_NAME" ]; then
    REPO_DIR="$SCRIPT_DIR"
  else
    TARBALL_URL="${MBA_AGENT_TARBALL_URL:-$DEFAULT_TARBALL_URL}"
    if [ "$TARBALL_URL" = "$DEFAULT_TARBALL_URL" ]; then
      echo "Set MBA_AGENT_TARBALL_URL to your GitHub tarball URL before using curl install." >&2
      echo "Example: MBA_AGENT_TARBALL_URL=https://github.com/USER/mba-agent/archive/refs/heads/main.tar.gz sh install.sh" >&2
      exit 2
    fi
    MBA_TMP_DIR="$(mktemp -d)"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$TARBALL_URL" | tar -xz -C "$MBA_TMP_DIR" --strip-components=1
    elif command -v wget >/dev/null 2>&1; then
      wget -qO- "$TARBALL_URL" | tar -xz -C "$MBA_TMP_DIR" --strip-components=1
    else
      echo "curl or wget is required for remote install." >&2
      exit 2
    fi
    REPO_DIR="$MBA_TMP_DIR"
  fi
fi

mkdir -p "$BIN_DIR" "$SKILL_HOME"
rm -rf "$SKILL_HOME/$SKILL_NAME"
cp -R "$REPO_DIR/skills/$SKILL_NAME" "$SKILL_HOME/$SKILL_NAME"
cp "$REPO_DIR/bin/mba" "$BIN_DIR/mba"
chmod +x "$BIN_DIR/mba"

echo "Installed mba CLI to $BIN_DIR/mba"
echo "Installed skill to $SKILL_HOME/$SKILL_NAME"
echo "Run: mba doctor"
