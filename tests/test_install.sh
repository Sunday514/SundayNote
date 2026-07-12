#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

fail() {
  echo "install fixture failed: $*" >&2
  exit 1
}

assert_file_contains() {
  grep -Fq -- "$2" "$1" || fail "$1 does not contain: $2"
}

assert_same_file() {
  cmp -s -- "$1" "$2" || fail "files differ: $1 -> $2"
}

assert_source_tree_exported() {
  local source_dir="$1"
  local target_dir="$2"
  local source_file
  local relative_path

  while IFS= read -r -d '' source_file; do
    relative_path="${source_file#"$source_dir/"}"
    test -f "$target_dir/$relative_path" || fail "missing exported file: $target_dir/$relative_path"
    assert_same_file "$source_file" "$target_dir/$relative_path"
  done < <(find "$source_dir" -type f -print0)
}

vault="$TMP_ROOT/vault"
mkdir -p "$vault/SundayNoteAgent"

bash "$ROOT/install/install.sh" --vault-root "$vault" >/dev/null

test -f "$vault/AGENTS.md" || fail "new vault is missing AGENTS.md"
test -f "$vault/30_知识库/个人上下文.md" || fail "new vault is missing personal context"
test -f "$vault/个人模板/每日记录.md" || fail "new vault is missing Daily template"
test ! -e "$vault/.agents/skills/paper-summarizer" || fail "optional skill was installed without opt-in"
assert_file_contains "$vault/.stignore" "/SundayNoteAgent"
assert_file_contains "$vault/.stignore" "/.import_files"
assert_same_file "$ROOT/install/scaffold/AGENTS.md" "$vault/AGENTS.md"
assert_source_tree_exported "$ROOT/skills/sunday-note-ingest" "$vault/.agents/skills/sunday-note-ingest"
assert_source_tree_exported "$ROOT/skills/sunday-note-lint" "$vault/.agents/skills/sunday-note-lint"
assert_source_tree_exported "$ROOT/skills/sunday-note-query" "$vault/.agents/skills/sunday-note-query"
assert_source_tree_exported "$ROOT/automation/quickadd" "$vault/.sunday-note-agent/quickadd"

cat > "$vault/30_知识库/集成测试.md" <<'EOF'
---
last_updated: 2026-07-13
update_count: 1
last_queried: ""
query_count: 0
sources: ["[[10_原始材料/集成来源]]"]
topic: "集成测试"
keywords: ["唯一集成词"]
---

# 集成测试

唯一集成词。

[[10_原始材料/集成来源]]
[[20_每日记录/2026-07-13]]
EOF
cat > "$vault/30_知识库/索引.md" <<'EOF'
---
last_updated: 2026-07-13
update_count: 1
last_queried: ""
query_count: 0
sources: []
topic: "索引"
keywords: ["索引"]
---

[[集成测试]]
EOF
printf '%s\n' "# 集成来源" > "$vault/10_原始材料/集成来源.md"
printf '%s\n' "唯一集成词只应作为直接来源读取。" > "$vault/20_每日记录/2026-07-13.md"

query_output="$(python "$vault/.agents/skills/sunday-note-query/scripts/query_search.py" \
  "唯一集成词" --vault-root "$vault")"
assert_file_contains <(printf '%s' "$query_output") "30_知识库/集成测试.md"
if grep -Fq "20_每日记录" <<< "$query_output"; then
  fail "installed Query searched Routine directly"
fi

python "$vault/.agents/skills/sunday-note-query/scripts/update_query_header.py" \
  "30_知识库/集成测试.md" --vault-root "$vault" --date 2026-07-13 >/dev/null
assert_file_contains "$vault/30_知识库/集成测试.md" "query_count: 1"
assert_file_contains "$vault/30_知识库/集成测试.md" "唯一集成词。"

lint_output="$(python "$vault/.agents/skills/sunday-note-lint/scripts/lint_headers.py" \
  --root "$vault" --scope "30_知识库/集成测试.md" --format json)"
assert_file_contains <(printf '%s' "$lint_output") '"issue_files": 0'

audit_output="$(python "$vault/.agents/skills/sunday-note-lint/scripts/audit_reachability.py" \
  --root "$vault" \
  --wiki-entry "30_知识库/索引.md" \
  --wiki-scope "30_知识库/索引.md" \
  --wiki-scope "30_知识库/集成测试.md" \
  --raw-scope "10_原始材料/集成来源.md" \
  --routine-scope "20_每日记录/2026-07-13.md" \
  --format json)"
assert_file_contains <(printf '%s' "$audit_output") '"wiki_unreachable": []'
assert_file_contains <(printf '%s' "$audit_output") '"raw_unlinked": []'

printf '%s\n' "local config" > "$vault/.sunday-note-agent/config/quickadd-rollups.json"
printf '%s\n' "local template" > "$vault/个人模板/每日记录.md"
printf '%s\n' "stale managed rule" > "$vault/AGENTS.md"
printf '%s\n' "stale managed script" > "$vault/.agents/skills/sunday-note-query/scripts/query_search.py"
printf '%s\n' "extra skill file" > "$vault/.agents/skills/sunday-note-query/local.md"
printf '%s\n' "local ignore" > "$vault/.stignore"

snapshot="$TMP_ROOT/local-content"
mkdir -p "$snapshot"
cp "$vault/.sunday-note-agent/config/quickadd-rollups.json" "$snapshot/config"
cp "$vault/个人模板/每日记录.md" "$snapshot/template"
cp "$vault/10_原始材料/集成来源.md" "$snapshot/raw"
cp "$vault/20_每日记录/2026-07-13.md" "$snapshot/routine"
cp "$vault/30_知识库/集成测试.md" "$snapshot/wiki"

assert_local_content_unchanged() {
  assert_same_file "$snapshot/config" "$vault/.sunday-note-agent/config/quickadd-rollups.json"
  assert_same_file "$snapshot/template" "$vault/个人模板/每日记录.md"
  assert_same_file "$snapshot/raw" "$vault/10_原始材料/集成来源.md"
  assert_same_file "$snapshot/routine" "$vault/20_每日记录/2026-07-13.md"
  assert_same_file "$snapshot/wiki" "$vault/30_知识库/集成测试.md"
}

bash "$ROOT/install/install.sh" --vault-root "$vault" --with-paper-summarizer >/dev/null

assert_file_contains "$vault/AGENTS.md" "Agent"
assert_file_contains "$vault/.sunday-note-agent/config/quickadd-rollups.json" "local config"
assert_file_contains "$vault/个人模板/每日记录.md" "local template"
assert_file_contains "$vault/.agents/skills/sunday-note-query/local.md" "extra skill file"
assert_file_contains "$vault/.stignore" "local ignore"
assert_file_contains "$vault/.stignore" "/SundayNoteAgent"
assert_file_contains "$vault/.stignore" "/.import_files"
test -f "$vault/.agents/skills/paper-summarizer/SKILL.md" || fail "optional skill was not installed"
assert_local_content_unchanged
assert_source_tree_exported "$ROOT/skills/sunday-note-ingest" "$vault/.agents/skills/sunday-note-ingest"
assert_source_tree_exported "$ROOT/skills/sunday-note-lint" "$vault/.agents/skills/sunday-note-lint"
assert_source_tree_exported "$ROOT/skills/sunday-note-query" "$vault/.agents/skills/sunday-note-query"
assert_source_tree_exported "$ROOT/skills/paper-summarizer" "$vault/.agents/skills/paper-summarizer"
assert_source_tree_exported "$ROOT/automation/quickadd" "$vault/.sunday-note-agent/quickadd"

printf '%s\n' "stale optional skill" > "$vault/.agents/skills/paper-summarizer/SKILL.md"
bash "$ROOT/install/install.sh" --vault-root "$vault" >/dev/null
if grep -Fq "stale optional skill" "$vault/.agents/skills/paper-summarizer/SKILL.md"; then
  fail "enabled optional skill was not refreshed"
fi
assert_local_content_unchanged
assert_source_tree_exported "$ROOT/skills/paper-summarizer" "$vault/.agents/skills/paper-summarizer"
test "$(grep -Fxc -- "/SundayNoteAgent" "$vault/.stignore")" -eq 1 || fail "Syncthing ignore rule was duplicated"
test "$(grep -Fxc -- "/.import_files" "$vault/.stignore")" -eq 1 || fail "Syncthing import ignore rule was duplicated"

conflict="$TMP_ROOT/conflict"
mkdir -p "$conflict/SundayNoteAgent" "$conflict/.sunday-note-agent"
printf '%s\n' "do not replace" > "$conflict/.sunday-note-agent/config"
if bash "$ROOT/install/install.sh" --vault-root "$conflict" >"$TMP_ROOT/conflict.out" 2>&1; then
  fail "real-file directory conflict did not stop installation"
fi
assert_file_contains "$TMP_ROOT/conflict.out" "$conflict/.sunday-note-agent/config"
assert_file_contains "$conflict/.sunday-note-agent/config" "do not replace"

stignore_conflict="$TMP_ROOT/stignore-conflict"
mkdir -p "$stignore_conflict/SundayNoteAgent" "$stignore_conflict/.stignore"
if bash "$ROOT/install/install.sh" --vault-root "$stignore_conflict" >"$TMP_ROOT/stignore-conflict.out" 2>&1; then
  fail "directory at .stignore did not stop installation"
fi
assert_file_contains "$TMP_ROOT/stignore-conflict.out" "$stignore_conflict/.stignore"

echo "install fixture passed"
