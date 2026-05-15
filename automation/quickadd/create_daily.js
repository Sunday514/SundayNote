module.exports = async function createDaily(params) {
  const { app, variables } = params;
  const config = await readConfig(app);
  const dateText = getDateFromVariables(variables) || formatDate(new Date());
  const date = parseDate(dateText);
  const week = isoWeekId(date);
  const weekday = weekdayName(date);
  const path = `${config.dailyDir}/${dateText}.md`;
  const template = await app.vault.adapter.read(config.dailyTemplate);
  const content = renderTemplate(template, { dateText, week, weekday });
  const file = await createIfMissing(app, path, content);
  await app.workspace.getLeaf(false).openFile(file);
};

async function readConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/sunday-note-vault.yaml");
  return {
    dailyDir: getValue(text, "daily", "20_每日记录"),
    dailyTemplate: getValue(text, "daily_template", "个人模板/每日记录.md"),
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

function parseDate(text) {
  const [year, month, day] = text.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function isoWeekId(date) {
  const utc = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = utc.getUTCDay() || 7;
  utc.setUTCDate(utc.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(utc.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((utc - yearStart) / 86400000) + 1) / 7);
  return `${utc.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function weekdayName(date) {
  return ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][date.getDay()];
}

function renderTemplate(template, { dateText, week, weekday }) {
  return template
    .replace(/{{DATE:YYYY-MM-DD}}/g, dateText)
    .replace(/{{DATE:gggg-\[W\]ww}}/g, week)
    .replace(/{{DATE:dddd}}/g, weekday)
    .replace(/value-date={{DATE:YYYY-MM-DD}}/g, `value-date=${dateText}`);
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
