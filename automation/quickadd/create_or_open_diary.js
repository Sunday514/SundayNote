module.exports = async function createOrOpenDiary(params) {
  const { app, variables } = params;
  const config = await readConfig(app);
  const dateText = getDateFromVariables(variables) || formatDate(new Date());
  const path = `${config.diaryDir}/${dateText}.md`;
  const file = await createIfMissing(app, path, "");
  await app.workspace.getLeaf(false).openFile(file);
};

const DIARY_SUBDIR = "日记";

async function readConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/sunday-note-vault.yaml");
  const journalDir = getValue(text, "journal", "40_个人写作");
  return {
    diaryDir: `${journalDir}/${DIARY_SUBDIR}`,
  };
}

function getValue(text, key, fallback) {
  const re = new RegExp(`^\\s*${key}:\\s*"([^"]+)"\\s*$`, "m");
  const match = text.match(re);
  return match ? match[1] : fallback;
}

function getDateFromVariables(variables) {
  const raw = variables && variables.date ? String(variables.date).trim() : "";
  return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? raw : "";
}

function formatDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

async function createIfMissing(app, path, content) {
  let file = app.vault.getAbstractFileByPath(path);
  if (file) return file;
  await ensureFolder(app, path.split("/").slice(0, -1).join("/"));
  return app.vault.create(path, content);
}

async function ensureFolder(app, folderPath) {
  const parts = folderPath.split("/").filter(Boolean);
  let current = "";
  for (const part of parts) {
    current = current ? `${current}/${part}` : part;
    if (!app.vault.getAbstractFileByPath(current)) {
      await app.vault.createFolder(current);
    }
  }
}
