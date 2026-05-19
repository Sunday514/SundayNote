#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR_NAME="SundayNoteAgent"
VAULT_ROOT=""

usage() {
  cat <<'USAGE'
Usage:
  install.sh
  install.sh --vault-root <vault-dir>

Configure a vault that already contains this project under SundayNoteAgent/.
The installer writes the outer vault scaffold and export links. It does not
migrate or rewrite existing personal notes.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --vault-root)
      [ "$#" -ge 2 ] || { echo "missing value for --vault-root" >&2; exit 2; }
      VAULT_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      echo "unexpected argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SCAFFOLD_DIR="$SCRIPT_DIR/scaffold"

abs_path() {
  local path="$1"
  mkdir -p "$(dirname -- "$path")"
  local parent
  parent="$(cd -- "$(dirname -- "$path")" && pwd)"
  printf '%s/%s\n' "$parent" "$(basename -- "$path")"
}

copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [ -e "$src" ] && [ ! -e "$dst" ]; then
    mkdir -p "$(dirname -- "$dst")"
    cp -R "$src" "$dst"
    if [ -f "$dst" ]; then
      chmod u+rw "$dst" 2>/dev/null || true
    fi
  fi
}

copy_scaffold_file() {
  local name="$1"
  copy_if_missing "$SCAFFOLD_DIR/$name" "$VAULT_ROOT/$name"
}

link_or_replace() {
  local target="$1"
  local link_path="$2"
  if [ -e "$link_path" ] && [ ! -L "$link_path" ]; then
    rm -rf "$link_path"
  elif [ -L "$link_path" ]; then
    rm -f "$link_path"
  fi
  mkdir -p "$(dirname -- "$link_path")"
  ln -s "$target" "$link_path"
}

ensure_vault_dirs() {
  mkdir -p \
    "$VAULT_ROOT/.agents" \
    "$VAULT_ROOT/.obsidian/bin" \
    "$VAULT_ROOT/.obsidian/plugins/terminal" \
    "$VAULT_ROOT/10_原始材料/收件箱" \
    "$VAULT_ROOT/10_原始材料/Codex记录" \
    "$VAULT_ROOT/20_每日记录" \
    "$VAULT_ROOT/21_每周记录" \
    "$VAULT_ROOT/22_每月记录" \
    "$VAULT_ROOT/23_项目复盘" \
    "$VAULT_ROOT/30_知识库" \
    "$VAULT_ROOT/40_个人写作" \
    "$VAULT_ROOT/个人模板" \
    "$VAULT_ROOT/.sunday-note-agent/config" \
    "$VAULT_ROOT/.sunday-note-agent/quickadd" \
    "$VAULT_ROOT/assets/figures"

  touch \
    "$VAULT_ROOT/10_原始材料/.gitkeep" \
    "$VAULT_ROOT/10_原始材料/收件箱/.gitkeep" \
    "$VAULT_ROOT/10_原始材料/Codex记录/.gitkeep" \
    "$VAULT_ROOT/20_每日记录/.gitkeep" \
    "$VAULT_ROOT/21_每周记录/.gitkeep" \
    "$VAULT_ROOT/22_每月记录/.gitkeep" \
    "$VAULT_ROOT/23_项目复盘/.gitkeep" \
    "$VAULT_ROOT/30_知识库/.gitkeep" \
    "$VAULT_ROOT/40_个人写作/.gitkeep" \
    "$VAULT_ROOT/个人模板/.gitkeep" \
    "$VAULT_ROOT/assets/figures/.gitkeep"
}

install_scaffold() {
  copy_scaffold_file AGENTS.md
  copy_scaffold_file CLAUDE.md
  copy_scaffold_file README.md
  copy_scaffold_file 首页.md
  copy_scaffold_file .gitignore

  ensure_vault_dirs

  copy_if_missing "$SOURCE_ROOT/.obsidian/app.json" "$VAULT_ROOT/.obsidian/app.json"
  copy_if_missing "$SOURCE_ROOT/.obsidian/appearance.json" "$VAULT_ROOT/.obsidian/appearance.json"
  copy_if_missing "$SOURCE_ROOT/.obsidian/community-plugins.json" "$VAULT_ROOT/.obsidian/community-plugins.json"
  copy_if_missing "$SOURCE_ROOT/.obsidian/plugins/terminal/data.json" "$VAULT_ROOT/.obsidian/plugins/terminal/data.json"
  copy_if_missing "$SOURCE_ROOT/.obsidian/bin/obsidian-codex-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-codex-terminal"
  copy_if_missing "$SOURCE_ROOT/.obsidian/bin/obsidian-claude-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-claude-terminal"
  copy_if_missing "$SOURCE_ROOT/.obsidian/bin/obsidian-bash-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-bash-terminal"
  copy_if_missing "$SOURCE_ROOT/assets/figures/obsidian-layout.png" "$VAULT_ROOT/assets/figures/obsidian-layout.png"
}

export_agents_payload() {
  cd "$VAULT_ROOT"
  mkdir -p .agents

  if [ -e .sunday-note-agent/config/sunday-note-vault.yaml ] && [ ! -f .sunday-note-agent/config/sunday-note-vault.yaml ]; then
    echo ".sunday-note-agent/config/sunday-note-vault.yaml exists and is not a file; refusing to replace it" >&2
    exit 1
  fi

  mkdir -p .sunday-note-agent/config
  link_or_replace "../$PROJECT_DIR_NAME/skills" ".agents/skills"
  link_or_replace "../$PROJECT_DIR_NAME/automation/quickadd" ".sunday-note-agent/quickadd"
  copy_if_missing "$SOURCE_ROOT/config/sunday-note-vault.yaml" ".sunday-note-agent/config/sunday-note-vault.yaml"
}

ensure_agent_sources() {
  if [ ! -d "$VAULT_ROOT/$PROJECT_DIR_NAME" ]; then
    echo "missing $PROJECT_DIR_NAME directory under vault root: $VAULT_ROOT" >&2
    exit 1
  fi
  if [ ! -d "$VAULT_ROOT/$PROJECT_DIR_NAME/skills" ]; then
    echo "missing $PROJECT_DIR_NAME/skills under vault root: $VAULT_ROOT" >&2
    exit 1
  fi
  if [ ! -d "$VAULT_ROOT/$PROJECT_DIR_NAME/automation/quickadd" ]; then
    echo "missing $PROJECT_DIR_NAME/automation/quickadd under vault root: $VAULT_ROOT" >&2
    exit 1
  fi
}

if [ -n "$VAULT_ROOT" ]; then
  VAULT_ROOT="$(abs_path "$VAULT_ROOT")"
else
  VAULT_ROOT="$(cd -- "$SOURCE_ROOT/.." && pwd)"
fi

if [ ! -d "$VAULT_ROOT" ]; then
  echo "missing vault root: $VAULT_ROOT" >&2
  exit 1
fi

ensure_agent_sources
cd "$VAULT_ROOT"

install_scaffold
export_agents_payload

echo "Installed Sunday Note vault at: $VAULT_ROOT"
echo "Agent directory: $PROJECT_DIR_NAME"
