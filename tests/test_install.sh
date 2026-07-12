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

vault="$TMP_ROOT/vault"
mkdir -p "$vault/SundayNoteAgent"

bash "$ROOT/install/install.sh" --vault-root "$vault" >/dev/null

test -f "$vault/AGENTS.md" || fail "new vault is missing AGENTS.md"
test -f "$vault/30_知识库/个人上下文.md" || fail "new vault is missing personal context"
test -f "$vault/个人模板/每日记录.md" || fail "new vault is missing Daily template"
test ! -e "$vault/.agents/skills/paper-summarizer" || fail "optional skill was installed without opt-in"

printf '%s\n' "local config" > "$vault/.sunday-note-agent/config/quickadd-rollups.json"
printf '%s\n' "local template" > "$vault/个人模板/每日记录.md"
printf '%s\n' "stale managed rule" > "$vault/AGENTS.md"
printf '%s\n' "extra skill file" > "$vault/.agents/skills/sunday-note-query/local.md"

bash "$ROOT/install/install.sh" --vault-root "$vault" --with-paper-summarizer >/dev/null

assert_file_contains "$vault/AGENTS.md" "Agent"
assert_file_contains "$vault/.sunday-note-agent/config/quickadd-rollups.json" "local config"
assert_file_contains "$vault/个人模板/每日记录.md" "local template"
assert_file_contains "$vault/.agents/skills/sunday-note-query/local.md" "extra skill file"
test -f "$vault/.agents/skills/paper-summarizer/SKILL.md" || fail "optional skill was not installed"

printf '%s\n' "stale optional skill" > "$vault/.agents/skills/paper-summarizer/SKILL.md"
bash "$ROOT/install/install.sh" --vault-root "$vault" >/dev/null
if grep -Fq "stale optional skill" "$vault/.agents/skills/paper-summarizer/SKILL.md"; then
  fail "enabled optional skill was not refreshed"
fi

conflict="$TMP_ROOT/conflict"
mkdir -p "$conflict/SundayNoteAgent" "$conflict/.sunday-note-agent"
printf '%s\n' "do not replace" > "$conflict/.sunday-note-agent/config"
if bash "$ROOT/install/install.sh" --vault-root "$conflict" >"$TMP_ROOT/conflict.out" 2>&1; then
  fail "real-file directory conflict did not stop installation"
fi
assert_file_contains "$TMP_ROOT/conflict.out" "$conflict/.sunday-note-agent/config"
assert_file_contains "$conflict/.sunday-note-agent/config" "do not replace"

echo "install fixture passed"
