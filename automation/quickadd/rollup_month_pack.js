module.exports = async function rollupMonthPack(params) {
  const { app, quickAddApi, variables } = params;
  const config = await readConfig(app);
  const defaultWeeks = recentIsoWeeks(new Date(), 4);
  const weeks = await getWeeks(quickAddApi, variables, defaultWeeks);
  if (!weeks || weeks.length === 0) return;
  const label = await getLabel(quickAddApi, variables, weeks);
  if (!label) return;

  const weeklyRows = [];
  for (const week of weeks) {
    const path = `${config.weeklyDir}/${week}.md`;
    const file = app.vault.getAbstractFileByPath(path);
    const text = file ? await app.vault.read(file) : "";
    weeklyRows.push({
      week,
      exists: Boolean(file),
      stats: parseWeeklyStats(text),
    });
  }

  const autoBlock = renderAutoBlock(weeklyRows);
  const monthlyPath = `${config.monthlyDir}/${label}.md`;
  const content = await nextMonthPackContent(app, monthlyPath, label, weeks, autoBlock);
  const file = await writeFile(app, monthlyPath, content);
  await app.workspace.getLeaf(false).openFile(file);
};

async function readConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/sunday-note-vault.yaml");
  return {
    weeklyDir: getValue(text, "weekly", "21_每周记录"),
    monthlyDir: getValue(text, "monthly", "22_每月记录"),
  };
}

function getValue(text, key, fallback) {
  const re = new RegExp(`^\\s*${key}:\\s*"([^"]+)"\\s*$`, "m");
  const match = text.match(re);
  return match ? match[1] : fallback;
}

async function getWeeks(quickAddApi, variables, defaultWeeks) {
  const fromVars = parseWeeks(variables && variables.weeks ? String(variables.weeks) : "");
  if (fromVars.length > 0) return fromVars;
  const input = await quickAddApi.inputPrompt(
    "月度包周列表",
    "用逗号分隔，例如 2026-W17, 2026-W18",
    defaultWeeks.join(", "),
  );
  return parseWeeks(input || "");
}

async function getLabel(quickAddApi, variables, weeks) {
  const fromVars = variables && variables.label ? sanitizeFileName(String(variables.label)) : "";
  if (fromVars) return fromVars;
  const defaultLabel = `${weeks[0]}--${weeks[weeks.length - 1]}`;
  const input = await quickAddApi.inputPrompt("月度包名称", "用于 22_每月记录/ 下的文件名", defaultLabel);
  return sanitizeFileName(input || "");
}

function parseWeeks(text) {
  return text
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter((item) => /^\d{4}-W\d{2}$/.test(item));
}

function sanitizeFileName(text) {
  return text.trim().replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ");
}

function recentIsoWeeks(anchor, count) {
  const currentStart = startOfIsoWeek(anchor);
  return Array.from({ length: count }, (_, index) => {
    const weekStart = addDays(currentStart, (index - count + 1) * 7);
    return isoWeekId(weekStart);
  });
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

function isoWeekId(date) {
  const utc = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = utc.getUTCDay() || 7;
  utc.setUTCDate(utc.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(utc.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((utc - yearStart) / 86400000) + 1) / 7);
  return `${utc.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function parseWeeklyStats(text) {
  const stats = new Map();
  const lines = text.split(/\r?\n/);
  let inSection = false;
  for (const line of lines) {
    if (/^##\s+打卡统计\s*$/.test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^##\s+/.test(line)) break;
    if (!inSection) continue;
    const match = line.match(/^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|/);
    if (!match) continue;
    const item = match[1].trim();
    if (item === "项目") continue;
    stats.set(item, {
      done: Number(match[2]),
      total: Number(match[3]),
    });
  }
  return stats;
}

function renderAutoBlock(weeklyRows) {
  const links = weeklyRows
    .map((row) => `- [[${row.week}]]${row.exists ? "" : "（未创建）"}`)
    .join("\n");
  const stats = aggregateStats(weeklyRows);
  const statLines = Array.from(stats.entries()).map(([item, value]) => {
    const rate = value.total > 0 ? `${Math.round((value.done / value.total) * 100)}%` : "-";
    return `| ${item} | ${value.done} | ${value.total} | ${rate} |`;
  });
  return `<!-- SN:month-pack:auto:start -->\n\n## 周记录\n\n${links}\n\n## 打卡统计\n\n| 项目 | 完成 | 应统计 | 完成率 |\n| --- | ---: | ---: | ---: |\n${statLines.join("\n")}\n\n<!-- SN:month-pack:auto:end -->`;
}

function aggregateStats(weeklyRows) {
  const totals = new Map();
  for (const row of weeklyRows) {
    for (const [item, value] of row.stats.entries()) {
      const current = totals.get(item) || { done: 0, total: 0 };
      current.done += value.done;
      current.total += value.total;
      totals.set(item, current);
    }
  }
  return totals;
}

async function nextMonthPackContent(app, path, label, weeks, autoBlock) {
  const existing = app.vault.getAbstractFileByPath(path);
  if (!existing) {
    const weekYaml = weeks.map((week) => `  - ${week}`).join("\n");
    return `---\ntype: month-pack\nweeks:\n${weekYaml}\n---\n\n# ${label}\n\n## 个人月计划\n\n- \n\n${autoBlock}\n\n## 个人月总结\n\n- \n\n## 分析与建议\n\n- \n`;
  }
  const oldContent = await app.vault.read(existing);
  const start = "<!-- SN:month-pack:auto:start -->";
  const end = "<!-- SN:month-pack:auto:end -->";
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
