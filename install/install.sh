#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_REPO="git@github.com:Sunday514/SundayNoteAgent.git"
PROJECT_DIR_NAME="SundayNoteAgent"
TARGET_DIR=""
VAULT_ROOT=""

usage() {
  cat <<'USAGE'
Usage:
  install.sh <target-dir> [--framework-repo <url-or-path>]
  install.sh --vault-root <vault-dir>

Modes:
  <target-dir>
    Create a new private vault, initialize git, and add this project as the
    SundayNoteAgent/ submodule.

  --vault-root <vault-dir>
    Configure an existing vault that already contains this project under
    SundayNoteAgent/.
    If <vault-dir> has no git repository, one is initialized.

The installer writes only the outer private vault scaffold. It does not migrate
or rewrite existing personal notes.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --framework-repo)
      [ "$#" -ge 2 ] || { echo "missing value for --framework-repo" >&2; exit 2; }
      FRAMEWORK_REPO="$2"
      shift 2
      ;;
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
      [ -z "$TARGET_DIR" ] || { echo "target directory specified more than once" >&2; exit 2; }
      TARGET_DIR="$1"
      shift
      ;;
  esac
done

if [ -n "$TARGET_DIR" ] && [ -n "$VAULT_ROOT" ]; then
  echo "use either <target-dir> or --vault-root, not both" >&2
  exit 2
fi

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CHECKOUT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$CHECKOUT_ROOT" ]; then
  CHECKOUT_ROOT="$SOURCE_ROOT"
fi
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
    cp -a "$src" "$dst"
  fi
}

copy_scaffold_file() {
  local name="$1"
  copy_if_missing "$SCAFFOLD_DIR/$name" "$VAULT_ROOT/$name"
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

  copy_if_missing "$CHECKOUT_ROOT/.obsidian/app.json" "$VAULT_ROOT/.obsidian/app.json"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/appearance.json" "$VAULT_ROOT/.obsidian/appearance.json"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/community-plugins.json" "$VAULT_ROOT/.obsidian/community-plugins.json"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/plugins/terminal/data.json" "$VAULT_ROOT/.obsidian/plugins/terminal/data.json"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/bin/obsidian-codex-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-codex-terminal"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/bin/obsidian-claude-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-claude-terminal"
  copy_if_missing "$CHECKOUT_ROOT/.obsidian/bin/obsidian-bash-terminal" "$VAULT_ROOT/.obsidian/bin/obsidian-bash-terminal"
  copy_if_missing "$CHECKOUT_ROOT/assets/figures/obsidian-layout.png" "$VAULT_ROOT/assets/figures/obsidian-layout.png"
}

export_agents_payload() {
  cd "$VAULT_ROOT"
  mkdir -p .agents

  if [ -e .agents/skills ] && [ ! -d .agents/skills ]; then
    echo ".agents/skills exists and is not a directory; refusing to replace it" >&2
    exit 1
  fi
  if [ -e .sunday-note-agent/quickadd ] && [ ! -d .sunday-note-agent/quickadd ]; then
    echo ".sunday-note-agent/quickadd exists and is not a directory; refusing to replace it" >&2
    exit 1
  fi
  if [ -e .sunday-note-agent/config/sunday-note-vault.yaml ] && [ ! -f .sunday-note-agent/config/sunday-note-vault.yaml ]; then
    echo ".sunday-note-agent/config/sunday-note-vault.yaml exists and is not a file; refusing to replace it" >&2
    exit 1
  fi

  rm -rf .agents/skills
  rm -rf .sunday-note-agent/quickadd
  cp -a "$SOURCE_ROOT/skills" .agents/skills
  mkdir -p .sunday-note-agent/config
  cp -a "$SOURCE_ROOT/automation/quickadd" .sunday-note-agent/quickadd
  copy_if_missing "$SOURCE_ROOT/config/sunday-note-vault.yaml" ".sunday-note-agent/config/sunday-note-vault.yaml"
}

ensure_private_git() {
  cd "$VAULT_ROOT"
  if [ ! -d .git ]; then
    git init -b main >/dev/null
  fi
}

safe_local_git_config() {
  local repo="$1"
  local config_file="$2"
  git config --file "$config_file" --add safe.directory "$repo"
  git config --file "$config_file" --add safe.directory "$repo/.git"
}

add_agent_submodule() {
  cd "$VAULT_ROOT"
  if [ -e "$PROJECT_DIR_NAME" ]; then
    echo "$PROJECT_DIR_NAME already exists; not adding a new submodule" >&2
    return
  fi

  git_options=(-c protocol.file.allow=always)
  if [ -d "$FRAMEWORK_REPO" ]; then
    FRAMEWORK_REPO="$(cd -- "$FRAMEWORK_REPO" && pwd)"
    temp_git_config="$(mktemp)"
    trap 'rm -f "$temp_git_config"' EXIT
    safe_local_git_config "$FRAMEWORK_REPO" "$temp_git_config"
    GIT_CONFIG_GLOBAL="$temp_git_config" git "${git_options[@]}" submodule add "$FRAMEWORK_REPO" "$PROJECT_DIR_NAME" >/dev/null
  else
    git "${git_options[@]}" submodule add "$FRAMEWORK_REPO" "$PROJECT_DIR_NAME" >/dev/null
  fi
}

register_existing_agent_submodule() {
  cd "$VAULT_ROOT"
  if git config --file .gitmodules --get-regexp '^submodule\\.SundayNoteAgent\\.' >/dev/null 2>&1; then
    return
  fi

  if [ ! -d "$PROJECT_DIR_NAME" ]; then
    echo "missing $PROJECT_DIR_NAME directory under vault root: $VAULT_ROOT" >&2
    exit 1
  fi

  local origin_url
  origin_url="$(git -C "$PROJECT_DIR_NAME" config --get remote.origin.url || true)"
  if [ -z "$origin_url" ]; then
    origin_url="$FRAMEWORK_REPO"
  fi

  git_options=(-c protocol.file.allow=always)
  git "${git_options[@]}" submodule add --force "$origin_url" "$PROJECT_DIR_NAME" >/dev/null
}

if [ -n "$TARGET_DIR" ]; then
  VAULT_ROOT="$(abs_path "$TARGET_DIR")"
  if [ -e "$VAULT_ROOT" ] && [ -n "$(find "$VAULT_ROOT" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    echo "target directory is not empty: $VAULT_ROOT" >&2
    exit 1
  fi
  mkdir -p "$VAULT_ROOT"
  ensure_private_git
  add_agent_submodule
elif [ -n "$VAULT_ROOT" ]; then
  VAULT_ROOT="$(abs_path "$VAULT_ROOT")"
  mkdir -p "$VAULT_ROOT"
  ensure_private_git
  register_existing_agent_submodule
else
  if [ "$(basename -- "$CHECKOUT_ROOT")" != "$PROJECT_DIR_NAME" ]; then
    echo "no target provided, and this project is not installed under $PROJECT_DIR_NAME/" >&2
    usage
    exit 2
  fi
  VAULT_ROOT="$(cd -- "$CHECKOUT_ROOT/.." && pwd)"
  ensure_private_git
  register_existing_agent_submodule
fi

install_scaffold
export_agents_payload

echo "Installed Sunday Note vault at: $VAULT_ROOT"
echo "Framework submodule: $PROJECT_DIR_NAME"
echo
echo "Verify:"
echo "  find -L .agents/skills -maxdepth 3 -name SKILL.md -print"
echo
echo "Initial commit:"
echo "  git add ."
echo "  git commit -m 'Initialize Sunday Note private vault'"
