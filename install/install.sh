#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR_NAME="SundayNoteAgent"
VAULT_ROOT=""
WITH_PAPER_SUMMARIZER=0
OPTIONAL_CONFIG_PYTHON=""

usage() {
  cat <<'USAGE'
Usage:
  install.sh
  install.sh --vault-root <vault-dir>
  install.sh [--vault-root <vault-dir>] --with-paper-summarizer

Install or update SundayNoteAgent-managed files from the current checkout.
Without --vault-root, the vault root is the parent of SundayNoteAgent/.
The installer creates missing vault-local files and refreshes only managed files and plugin fields.
Paper summarizer is optional because it requires a docling-capable environment.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --vault-root)
      [ "$#" -ge 2 ] || { echo "missing value for --vault-root" >&2; exit 2; }
      VAULT_ROOT="$2"
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

if [ -n "$VAULT_ROOT" ]; then
  if [ ! -d "$VAULT_ROOT" ]; then
    echo "missing vault root: $VAULT_ROOT" >&2
    exit 1
  fi
  VAULT_ROOT="$(cd -- "$VAULT_ROOT" && pwd)"
else
  VAULT_ROOT="$(cd -- "$SOURCE_ROOT/.." && pwd)"
fi

require_source_file() {
  local path="$1"
  if [ ! -f "$path" ]; then
    echo "missing installer source file: $path" >&2
    exit 1
  fi
}

require_source_dir() {
  local path="$1"
  if [ ! -d "$path" ]; then
    echo "missing installer source directory: $path" >&2
    exit 1
  fi
}

preflight_container_dir() {
  local path="$1"
  if [ -L "$path" ]; then
    echo "installer container is a symlink; refusing to write through it: $path" >&2
    exit 1
  fi
  if [ -e "$path" ] && [ ! -d "$path" ]; then
    echo "installer container exists and is not a directory: $path" >&2
    exit 1
  fi
}

preflight_managed_file() {
  local path="$1"
  if [ -L "$path" ]; then
    echo "managed file destination is a symlink; refusing to replace it: $path" >&2
    exit 1
  fi
  if [ -e "$path" ] && [ ! -f "$path" ]; then
    echo "managed file destination exists and is not a file: $path" >&2
    exit 1
  fi
}

preflight_local_file() {
  local path="$1"
  if [ -L "$path" ]; then
    return
  fi
  if [ -e "$path" ] && [ ! -f "$path" ]; then
    echo "vault-local file destination exists and is not a file: $path" >&2
    exit 1
  fi
}

preflight_append_file() {
  local path="$1"
  if [ -L "$path" ]; then
    echo "vault-local append target is a symlink; refusing to write through it: $path" >&2
    exit 1
  fi
  if [ -e "$path" ] && [ ! -f "$path" ]; then
    echo "vault-local append target exists and is not a file: $path" >&2
    exit 1
  fi
}

preflight_managed_dir() {
  local path="$1"
  if [ -e "$path" ] && [ ! -d "$path" ] && [ ! -L "$path" ]; then
    echo "managed directory destination exists and is not a directory: $path" >&2
    exit 1
  fi
}

copy_managed_file() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname -- "$dst")"
  cp "$src" "$dst"
  chmod u+rw "$dst" 2>/dev/null || true
}

copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    return
  fi
  mkdir -p "$(dirname -- "$dst")"
  cp "$src" "$dst"
  chmod u+rw "$dst" 2>/dev/null || true
}

copy_managed_dir() {
  local src="$1"
  local dst="$2"
  if [ -L "$dst" ]; then
    rm -f "$dst"
  fi
  mkdir -p "$dst"
  cp -R "$src/." "$dst/"
}

ensure_vault_dirs() {
  mkdir -p \
    "$VAULT_ROOT/.agents" \
    "$VAULT_ROOT/.import_files" \
    "$VAULT_ROOT/10_原始材料" \
    "$VAULT_ROOT/20_每日记录" \
    "$VAULT_ROOT/21_每周记录" \
    "$VAULT_ROOT/22_每月记录" \
    "$VAULT_ROOT/23_项目复盘" \
    "$VAULT_ROOT/30_知识库" \
    "$VAULT_ROOT/40_个人写作" \
    "$VAULT_ROOT/个人模板" \
    "$VAULT_ROOT/assets/figures"

  touch \
    "$VAULT_ROOT/.import_files/.gitkeep" \
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
  local target="$VAULT_ROOT/30_知识库/个人上下文.md"
  local current_date

  if [ -e "$target" ] || [ -L "$target" ]; then
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

ensure_syncthing_ignores() {
  local target="$VAULT_ROOT/.stignore"
  local pattern

  for pattern in "/$PROJECT_DIR_NAME" "/.import_files"; do
    if [ -f "$target" ] && grep -Fxq -- "$pattern" "$target"; then
      continue
    fi
    if [ -s "$target" ] && [ -n "$(tail -c 1 "$target")" ]; then
      printf '\n' >> "$target"
    fi
    printf '%s\n' "$pattern" >> "$target"
  done
}

paper_skill_path="$VAULT_ROOT/.agents/skills/paper-summarizer"
install_paper_summarizer=0
if [ "$WITH_PAPER_SUMMARIZER" -eq 1 ] || [ -e "$paper_skill_path" ] || [ -L "$paper_skill_path" ]; then
  install_paper_summarizer=1
fi

require_source_file "$SCAFFOLD_DIR/AGENTS.md"
require_source_file "$SCAFFOLD_DIR/首页.md"
require_source_file "$SCAFFOLD_DIR/.gitignore"
require_source_file "$SOURCE_ROOT/config/quickadd-rollups.json"
require_source_file "$SOURCE_ROOT/config/obsidian/calendar.json"
require_source_file "$SOURCE_ROOT/config/obsidian/quickadd.json"
require_source_file "$SCRIPT_DIR/configure_optional_integrations.py"
require_source_file "$SOURCE_ROOT/templates/每日记录.md"
require_source_file "$SOURCE_ROOT/templates/每周记录.md"
require_source_file "$SOURCE_ROOT/templates/每月记录.md"
require_source_dir "$SOURCE_ROOT/automation/quickadd"
require_source_dir "$SOURCE_ROOT/skills/sunday-note-ingest"
require_source_dir "$SOURCE_ROOT/skills/sunday-note-lint"
require_source_dir "$SOURCE_ROOT/skills/sunday-note-query"
if [ "$install_paper_summarizer" -eq 1 ]; then
  require_source_dir "$SOURCE_ROOT/skills/paper-summarizer"
fi

if [ ! -d "$VAULT_ROOT/$PROJECT_DIR_NAME" ]; then
  echo "missing $PROJECT_DIR_NAME directory under vault root: $VAULT_ROOT" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  OPTIONAL_CONFIG_PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  OPTIONAL_CONFIG_PYTHON="$(command -v python)"
fi

preflight_container_dir "$VAULT_ROOT/.agents"
preflight_container_dir "$VAULT_ROOT/.agents/skills"
preflight_container_dir "$VAULT_ROOT/.sunday-note-agent"
preflight_container_dir "$VAULT_ROOT/.sunday-note-agent/config"

preflight_managed_file "$VAULT_ROOT/AGENTS.md"
preflight_local_file "$VAULT_ROOT/首页.md"
preflight_local_file "$VAULT_ROOT/.gitignore"
preflight_append_file "$VAULT_ROOT/.stignore"
preflight_local_file "$VAULT_ROOT/.sunday-note-agent/config/quickadd-rollups.json"
preflight_local_file "$VAULT_ROOT/个人模板/每日记录.md"
preflight_managed_file "$VAULT_ROOT/个人模板/每周记录.md"
preflight_managed_file "$VAULT_ROOT/个人模板/每月记录.md"

preflight_managed_dir "$VAULT_ROOT/.agents/skills/sunday-note-ingest"
preflight_managed_dir "$VAULT_ROOT/.agents/skills/sunday-note-lint"
preflight_managed_dir "$VAULT_ROOT/.agents/skills/sunday-note-query"
if [ "$install_paper_summarizer" -eq 1 ]; then
  preflight_managed_dir "$paper_skill_path"
fi

ensure_vault_dirs
copy_managed_file "$SCAFFOLD_DIR/AGENTS.md" "$VAULT_ROOT/AGENTS.md"
copy_if_missing "$SCAFFOLD_DIR/首页.md" "$VAULT_ROOT/首页.md"
copy_if_missing "$SCAFFOLD_DIR/.gitignore" "$VAULT_ROOT/.gitignore"
ensure_syncthing_ignores
copy_if_missing "$SOURCE_ROOT/templates/每日记录.md" "$VAULT_ROOT/个人模板/每日记录.md"
copy_managed_file "$SOURCE_ROOT/templates/每周记录.md" "$VAULT_ROOT/个人模板/每周记录.md"
copy_managed_file "$SOURCE_ROOT/templates/每月记录.md" "$VAULT_ROOT/个人模板/每月记录.md"
ensure_personal_context_file

copy_managed_dir "$SOURCE_ROOT/skills/sunday-note-ingest" "$VAULT_ROOT/.agents/skills/sunday-note-ingest"
copy_managed_dir "$SOURCE_ROOT/skills/sunday-note-lint" "$VAULT_ROOT/.agents/skills/sunday-note-lint"
copy_managed_dir "$SOURCE_ROOT/skills/sunday-note-query" "$VAULT_ROOT/.agents/skills/sunday-note-query"
if [ "$install_paper_summarizer" -eq 1 ]; then
  copy_managed_dir "$SOURCE_ROOT/skills/paper-summarizer" "$paper_skill_path"
fi
copy_if_missing "$SOURCE_ROOT/config/quickadd-rollups.json" "$VAULT_ROOT/.sunday-note-agent/config/quickadd-rollups.json"

if [ -n "$OPTIONAL_CONFIG_PYTHON" ]; then
  if ! "$OPTIONAL_CONFIG_PYTHON" "$SCRIPT_DIR/configure_optional_integrations.py" --vault-root "$VAULT_ROOT"; then
    echo "可选集成配置失败；核心安装已完成，Calendar/QuickAdd 未全部配置。" >&2
  fi
else
  echo "可选工作流未配置：Calendar Weekly 创建（未找到 python3 或 python；核心安装已完成）。"
  echo "可选工作流未配置：QuickAdd Routine 自动化（未找到 python3 或 python；核心安装已完成）。"
fi
echo "Installed or updated Sunday Note vault at: $VAULT_ROOT"
echo "Managed rules, skills, and Routine files were refreshed from: $PROJECT_DIR_NAME"
echo "Vault-local content and unmanaged configuration were preserved."
echo "安装期间应关闭 Obsidian；如果刚才正在运行，请退出后重新运行安装器，再启动 Obsidian。"
