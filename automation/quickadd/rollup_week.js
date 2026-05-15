module.exports = async function rollupWeek(params) {
  const { app, variables } = params;
  const config = await readConfig(app);
  const templateItems = await readTemplateCheckins(app, config.dailyTemplate);
  const weekFromContext = getWeekFromContext(app, variables);
  const anchorText = getDateFromContext(app, variables);
  const anchor = parseDate(anchorText);
  const weekId = weekFromContext || isoWeekId(anchor);
  const weekStart = weekFromContext ? mondayOfIsoWeek(weekId) : startOfIsoWeek(anchor);
  const days = Array.from({ length: 7 }, (_, index) => addDays(weekStart, index));
  const dailyRows = [];

  for (const day of days) {
    const dateText = formatDate(day);
    const path = `${config.dailyDir}/${dateText}.md`;
    const file = app.vault.getAbstractFileByPath(path);
    const text = file ? await app.vault.read(file) : "";
    dailyRows.push({
      dateText,
      weekday: weekdayName(day),
      path,
      exists: Boolean(file),
      checkins: parseCheckins(text),
    });
  }

  const autoBlock = renderAutoBlock(weekId, dailyRows, orderedItems(templateItems, dailyRows));
  const weeklyPath = `${config.weeklyDir}/${weekId}.md`;
  const content = await nextWeeklyContent(app, weeklyPath, weekId, autoBlock);
  const file = await writeFile(app, weeklyPath, content);
  await app.workspace.getLeaf(false).openFile(file);
};

const REFRESH_WEEK_CHOICE = encodeURIComponent("统计本周打卡");

async function readConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/sunday-note-vault.yaml");
  return {
    dailyDir: getValue(text, "daily", "20_每日记录"),
    weeklyDir: getValue(text, "weekly", "21_每周记录"),
    dailyTemplate: getValue(text, "daily_template", "个人模板/每日记录.md"),
  };
}

function getValue(text, key, fallback) {
  const re = new RegExp(`^\\s*${key}:\\s*"([^"]+)"\\s*$`, "m");
  const match = text.match(re);
  return match ? match[1] : fallback;
}

function getWeekFromContext(app, variables) {
  const raw = variables && variables.week ? String(variables.week).trim() : "";
  if (/^\d{4}-W\d{2}$/.test(raw)) return raw;
  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (active && /^\d{4}-W\d{2}$/.test(active.basename)) return active.basename;
  return "";
}

function getDateFromContext(app, variables) {
  const raw = variables && variables.date ? String(variables.date).trim() : "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (active && /^\d{4}-\d{2}-\d{2}$/.test(active.basename)) return active.basename;
  return formatDate(new Date());
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

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}

function startOfIsoWeek(date) {
  const start = new Date(date);
  const day = start.getDay() || 7;
  start.setDate(start.getDate() - day + 1);
  return start;
}

function mondayOfIsoWeek(weekId) {
  const match = weekId.match(/^(\d{4})-W(\d{2})$/);
  if (!match) throw new Error(`Invalid week id: ${weekId}`);
  const year = Number(match[1]);
  const week = Number(match[2]);
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const jan4Day = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - jan4Day + 1 + (week - 1) * 7);
  return new Date(monday.getUTCFullYear(), monday.getUTCMonth(), monday.getUTCDate());
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

function parseCheckins(text) {
  const checkins = new Map();
  const lines = text.split(/\r?\n/);
  let inSection = false;
  for (const line of lines) {
    if (/^##\s+打卡\s*$/.test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^##\s+/.test(line)) break;
    if (!inSection) continue;
    const match = line.match(/^- \[([ xX])\]\s*([^：:]+)[：:]\s*(.*)$/);
    if (!match) continue;
    checkins.set(match[2].trim(), {
      done: match[1].toLowerCase() === "x",
      note: match[3].trim(),
    });
  }
  return checkins;
}

async function readTemplateCheckins(app, templatePath) {
  try {
    return Array.from(parseCheckins(await app.vault.adapter.read(templatePath)).keys());
  } catch {
    return [];
  }
}

function orderedItems(templateItems, dailyRows) {
  const seen = new Set();
  const items = [];
  for (const item of templateItems) {
    if (seen.has(item)) continue;
    seen.add(item);
    items.push(item);
  }
  for (const row of dailyRows) {
    for (const item of row.checkins.keys()) {
      if (seen.has(item)) continue;
      seen.add(item);
      items.push(item);
    }
  }
  return items;
}

function renderAutoBlock(weekId, dailyRows, items) {
  const refreshLink = renderRefreshLink(weekId);
  const links = dailyRows
    .map((row) => `- [[${row.dateText}]]${row.exists ? "" : "（未创建）"}`)
    .join("\n");
  const stats = items.map((item) => statRow(item, dailyRows)).join("\n");
  return `<!-- SN:weekly:auto:start -->\n\n${refreshLink}\n\n## 打卡统计\n\n| 项目 | 完成 | 应统计 | 完成率 |\n| --- | ---: | ---: | ---: |\n${stats}\n\n## 每日记录\n\n${links}\n\n<!-- SN:weekly:auto:end -->`;
}

function renderRefreshLink(weekId) {
  return `[刷新本周统计](obsidian://quickadd?choice=${REFRESH_WEEK_CHOICE}&value-week=${weekId})`;
}

function statRow(item, dailyRows) {
  let total = 0;
  let done = 0;
  for (const row of dailyRows) {
    if (!row.checkins.has(item)) continue;
    total += 1;
    if (row.checkins.get(item).done) done += 1;
  }
  const rate = total > 0 ? `${Math.round((done / total) * 100)}%` : "-";
  return `| ${item} | ${done} | ${total} | ${rate} |`;
}

async function nextWeeklyContent(app, path, weekId, autoBlock) {
  const existing = app.vault.getAbstractFileByPath(path);
  if (!existing) {
    return `---\nweek: ${weekId}\ntype: weekly\n---\n\n# ${weekId}\n\n## 个人周计划\n\n- \n\n${autoBlock}\n\n## 个人周总结\n\n- \n\n## 分析与建议\n\n- \n`;
  }
  const oldContent = await app.vault.read(existing);
  const start = "<!-- SN:weekly:auto:start -->";
  const end = "<!-- SN:weekly:auto:end -->";
  if (oldContent.includes(start) && oldContent.includes(end)) {
    return oldContent.replace(
      new RegExp(`${escapeRegExp(start)}[\\s\\S]*?${escapeRegExp(end)}`),
      autoBlock,
    );
  }
  return `${autoBlock}\n\n${oldContent}`;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function writeFile(app, path, content) {
  let file = app.vault.getAbstractFileByPath(path);
  if (file) {
    await app.vault.modify(file, content);
    return file;
  }
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
