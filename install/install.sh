#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR_NAME="SundayNoteAgent"
VAULT_ROOT=""
INIT_CONTENT_SCAFFOLD=1
WITH_PAPER_SUMMARIZER=0
WIKI_DIR_EXISTED=0

usage() {
  cat <<'USAGE'
Usage:
  install.sh
  install.sh --vault-root <vault-dir>
  install.sh [--vault-root <vault-dir>] --with-paper-summarizer

Configure a vault that already contains this project under SundayNoteAgent/.
Without --vault-root, the installer initializes the standard Sunday Note
directory skeleton around the project. With --vault-root, it configures an
existing vault and creates any missing top-level architecture directories.
It does not migrate or rewrite existing personal notes.
Paper summarizer is optional because it requires a docling-capable environment.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --vault-root)
      [ "$#" -ge 2 ] || { echo "missing value for --vault-root" >&2; exit 2; }
      VAULT_ROOT="$2"
      INIT_CONTENT_SCAFFOLD=0
      shift 2
      ;;
    --with-paper-summarizer)
      WITH_PAPER_SUMMARIZER=1
      shift
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

ensure_skills_export_dir() {
  if [ -L .agents/skills ]; then
    rm -f .agents/skills
  fi
  if [ -e .agents/skills ] && [ ! -d .agents/skills ]; then
    echo ".agents/skills exists and is not a directory; refusing to replace it" >&2
    exit 1
  fi
  mkdir -p .agents/skills
}

move_existing_skill_aside() {
  local skill_name="$1"
  local skill_path=".agents/skills/$skill_name"
  local backup_dir=".agents/skills/.replaced-by-symlink/$(date +%Y%m%d-%H%M%S)"

  mkdir -p "$backup_dir"
  mv "$skill_path" "$backup_dir/$skill_name"
}

link_skill() {
  local skill_name="$1"
  local link_path=".agents/skills/$skill_name"
  local target="../../$PROJECT_DIR_NAME/skills/$skill_name"

  if [ -e "$link_path" ] && [ ! -L "$link_path" ]; then
    move_existing_skill_aside "$skill_name"
  elif [ -L "$link_path" ]; then
    rm -f "$link_path"
  fi

  ln -s "$target" "$link_path"
}

unlink_optional_skill() {
  local skill_name="$1"
  local link_path=".agents/skills/$skill_name"

  if [ -L "$link_path" ]; then
    rm -f "$link_path"
  elif [ -e "$link_path" ]; then
    move_existing_skill_aside "$skill_name"
  fi
}

ensure_vault_dirs() {
  mkdir -p \
    "$VAULT_ROOT/.agents" \
    "$VAULT_ROOT/00_导入暂存" \
    "$VAULT_ROOT/10_原始材料" \
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
    "$VAULT_ROOT/00_导入暂存/.gitkeep" \
    "$VAULT_ROOT/10_原始材料/.gitkeep" \
    "$VAULT_ROOT/20_每日记录/.gitkeep" \
    "$VAULT_ROOT/21_每周记录/.gitkeep" \
    "$VAULT_ROOT/22_每月记录/.gitkeep" \
    "$VAULT_ROOT/23_项目复盘/.gitkeep" \
    "$VAULT_ROOT/30_知识库/.gitkeep" \
    "$VAULT_ROOT/40_个人写作/.gitkeep" \
    "$VAULT_ROOT/个人模板/.gitkeep" \
    "$VAULT_ROOT/assets/figures/.gitkeep"
}

ensure_personal_context_file() {
  local wiki_dir="$VAULT_ROOT/30_知识库"
  local target="$wiki_dir/个人上下文.md"
  local current_date

  if [ ! -d "$wiki_dir" ] || [ -e "$target" ]; then
    return
  fi

  current_date="$(date +%F)"
  cat > "$target" <<EOF
---
last_updated: $current_date
update_count: 1
last_queried: ""
query_count: 0
sources: []
topic: "个人兴趣与近期计划"
keywords: []
---

# 个人上下文

## 兴趣方向

## 近期计划

## 推荐偏好

## 当前项目

## 不感兴趣
EOF
}

install_scaffold() {
  copy_scaffold_file AGENTS.md
  copy_scaffold_file CLAUDE.md
  copy_scaffold_file 首页.md
  copy_scaffold_file .gitignore

  ensure_vault_dirs

  if [ "$INIT_CONTENT_SCAFFOLD" -eq 1 ]; then
    copy_if_missing "$SOURCE_ROOT/config/obsidian/app.json" "$VAULT_ROOT/.obsidian/app.json"
    copy_if_missing "$SOURCE_ROOT/config/obsidian/appearance.json" "$VAULT_ROOT/.obsidian/appearance.json"
    copy_if_missing "$SOURCE_ROOT/config/obsidian/community-plugins.json" "$VAULT_ROOT/.obsidian/community-plugins.json"
    copy_if_missing "$SOURCE_ROOT/assets/figures/obsidian-layout.png" "$VAULT_ROOT/assets/figures/obsidian-layout.png"
  fi
}

export_agents_payload() {
  cd "$VAULT_ROOT"
  mkdir -p .agents

  if [ -e .sunday-note-agent/config/sunday-note-vault.yaml ] && [ ! -f .sunday-note-agent/config/sunday-note-vault.yaml ]; then
    echo ".sunday-note-agent/config/sunday-note-vault.yaml exists and is not a file; refusing to replace it" >&2
    exit 1
  fi

  mkdir -p .sunday-note-agent/config
  mkdir -p .claudian
  ensure_skills_export_dir
  link_skill sunday-note-ingest
  link_skill sunday-note-lint
  link_skill sunday-note-query
  if [ "$WITH_PAPER_SUMMARIZER" -eq 1 ]; then
    link_skill paper-summarizer
  else
    unlink_optional_skill paper-summarizer
  fi
  link_or_replace "../$PROJECT_DIR_NAME/automation/quickadd" ".sunday-note-agent/quickadd"
  copy_if_missing "$SOURCE_ROOT/config/sunday-note-vault.yaml" ".sunday-note-agent/config/sunday-note-vault.yaml"
  copy_if_missing "$SOURCE_ROOT/config/quickadd-rollups.json" ".sunday-note-agent/config/quickadd-rollups.json"
  copy_if_missing "$SOURCE_ROOT/config/claudian/claudian-settings.json" ".claudian/claudian-settings.json"
  copy_if_missing "$SOURCE_ROOT/config/obsidian/community-plugins.json" ".obsidian/community-plugins.json"
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

if [ -d "$VAULT_ROOT/30_知识库" ]; then
  WIKI_DIR_EXISTED=1
fi

ensure_agent_sources
cd "$VAULT_ROOT"

install_scaffold
if [ "$INIT_CONTENT_SCAFFOLD" -eq 1 ] || [ "$WIKI_DIR_EXISTED" -eq 1 ]; then
  ensure_personal_context_file
fi
export_agents_payload

echo "Installed Sunday Note vault at: $VAULT_ROOT"
echo "Agent directory: $PROJECT_DIR_NAME"
