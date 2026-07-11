module.exports = async function rollup(params) {
  const { app, variables = {} } = params;
  const vaultConfig = await readVaultConfig(app);
  const rollupConfig = await readRollupConfig(app);
  const rollupName = String(variables.rollup || "").trim();
  const spec = rollupConfig.rollups && rollupConfig.rollups[rollupName];

  if (!rollupName || !spec) {
    throw new Error(`Unknown rollup: ${rollupName || "(empty)"}`);
  }

  const context = buildContext(app, variables, spec, vaultConfig);
  if (!hasRequiredContext(spec, context)) return;
  const rows = await readSourceRows(app, vaultConfig, spec, context);
  const items = await collectItems(app, vaultConfig, spec, rows);
  const stats = aggregateRows(spec, rows, items);
  const autoBlock = renderAutoBlock(spec, rows, stats, context);
  const targetPath = renderTemplate(spec.target.path, { ...vaultConfig, ...context });
  const content = await nextTargetContent(app, targetPath, spec, autoBlock, vaultConfig, context);
  const file = await writeFile(app, targetPath, content);
  await app.workspace.getLeaf(false).openFile(file);
};

function hasRequiredContext(spec, context) {
  for (const key of spec.required_context || []) {
    const value = context[key];
    if (Array.isArray(value) && value.length === 0) return false;
    if (typeof value === "string" && value.trim() === "") return false;
    if (value === undefined || value === null) return false;
  }
  return true;
}

async function readVaultConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/sunday-note-vault.yaml");
  return {
    daily: getYamlValue(text, "daily", "20_每日记录"),
    weekly: getYamlValue(text, "weekly", "21_每周记录"),
    monthly: getYamlValue(text, "monthly", "22_每月记录"),
    daily_template: getYamlValue(text, "daily_template", "个人模板/每日记录.md"),
    weekly_template: getYamlValue(text, "weekly_template", "个人模板/周记录.md"),
    monthly_template: getYamlValue(text, "monthly_template", "个人模板/月记录.md"),
  };
}

async function readRollupConfig(app) {
  const text = await app.vault.adapter.read(".sunday-note-agent/config/quickadd-rollups.json");
  return JSON.parse(text);
}

function getYamlValue(text, key, fallback) {
  const re = new RegExp(`^\\s*${key}:\\s*"([^"]+)"\\s*$`, "m");
  const match = text.match(re);
  return match ? match[1] : fallback;
}

function buildContext(app, variables, spec, vaultConfig) {
  const context = { ...variables };

  if (spec.context && spec.context.date) {
    context.date = getDateFromContext(app, variables, spec.context.date);
  }

  if (spec.context && spec.context.week) {
    context.week = getWeekFromContext(app, variables, context.date, spec.context.week);
  }

  if (spec.context && spec.context.month) {
    context.month = getMonthFromContext(app, variables, spec.context.month, vaultConfig);
  }

  if (spec.context && spec.context.weeks) {
    context.weeks = getWeeks(variables, spec.context.weeks, context);
  }

  if (spec.context && spec.context.label) {
    context.label = getLabel(app, variables, spec.context.label, vaultConfig, context);
  }

  return context;
}

function getDateFromContext(app, variables, options) {
  const variable = options.variable || "date";
  const raw = variables && variables[variable] ? String(variables[variable]).trim() : "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (active && /^\d{4}-\d{2}-\d{2}$/.test(active.basename)) return active.basename;
  return formatDate(new Date());
}

function getWeekFromContext(app, variables, dateText, options) {
  const variable = options.variable || "week";
  const raw = variables && variables[variable] ? String(variables[variable]).trim() : "";
  if (/^\d{4}-W\d{2}$/.test(raw)) return raw;
  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (active && /^\d{4}-W\d{2}$/.test(active.basename)) return active.basename;
  return isoWeekId(parseDate(dateText || formatDate(new Date())));
}

function getMonthFromContext(app, variables, options, vaultConfig) {
  const variable = options.variable || "month";
  const raw = variables && variables[variable] ? String(variables[variable]).trim() : "";
  if (raw) return normalizeMonth(raw);

  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (active && options.infer_from_active_file && activeFileInFolder(active, vaultConfig, options.active_folder)) {
    return normalizeMonth(active.basename);
  }

  if (options.default) {
    return normalizeMonth(renderTemplate(options.default, { current_month: currentMonth() }));
  }

  return "";
}

function getWeeks(variables, options, context) {
  const variable = options.variable || "weeks";
  const fromVars = parseWeeks(variables && variables[variable] ? String(variables[variable]) : "");
  if (fromVars.length > 0) return fromVars;

  if (options.from_month && context[options.from_month]) {
    return isoWeeksInMonth(context[options.from_month]);
  }

  return [];
}

function getLabel(app, variables, options, vaultConfig, context) {
  const variable = options.variable || "label";
  const fromVars = variables && variables[variable] ? sanitizeFileName(String(variables[variable])) : "";
  if (fromVars) return fromVars;

  const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
  if (
    active
    && options.infer_from_active_file
    && activeFileInFolder(active, vaultConfig, options.active_folder)
  ) {
    return sanitizeFileName(active.basename);
  }

  const defaultLabel = renderTemplate(options.default || "{month}", context);
  return sanitizeFileName(defaultLabel);
}

async function readSourceRows(app, vaultConfig, spec, context) {
  if (spec.source.type === "iso_week_days") {
    const weekStart = mondayOfIsoWeek(context.week);
    const days = Array.from({ length: 7 }, (_, index) => addDays(weekStart, index));
    return readFiles(app, days.map((day) => {
      const id = formatDate(day);
      return {
        id,
        path: `${resolvePath(vaultConfig, spec.source.folder)}/${id}.md`,
      };
    }));
  }

  if (spec.source.type === "iso_weeks") {
    return readFiles(app, context.weeks.map((week) => ({
      id: week,
      path: `${resolvePath(vaultConfig, spec.source.folder)}/${week}.md`,
    })));
  }

  throw new Error(`Unsupported source type: ${spec.source.type}`);
}

async function readFiles(app, rows) {
  const result = [];
  for (const row of rows) {
    const file = app.vault.getAbstractFileByPath(row.path);
    result.push({
      ...row,
      exists: Boolean(file),
      text: file ? await app.vault.read(file) : "",
    });
  }
  return result;
}

async function collectItems(app, vaultConfig, spec, rows) {
  if (spec.extract.type !== "checkbox_section") return [];

  const templatePath = spec.extract.template ? resolvePath(vaultConfig, spec.extract.template) : "";
  const templateDefinitions = templatePath
    ? await readTemplateCheckboxDefinitions(app, templatePath, spec.extract.heading)
    : [];
  const seen = new Set();
  const items = [];

  for (const definition of templateDefinitions) addItem(items, seen, definition.item);
  for (const row of rows) {
    row.values = parseCheckboxSection(row.text, spec.extract.heading, templateDefinitions);
    for (const item of row.values.keys()) addItem(items, seen, item);
  }
  return items;
}

function addItem(items, seen, item) {
  if (seen.has(item)) return;
  seen.add(item);
  items.push(item);
}

async function readTemplateCheckboxDefinitions(app, templatePath, heading) {
  try {
    const rawItems = parseCheckboxSection(await app.vault.adapter.read(templatePath), heading).keys();
    const definitions = [];
    const seen = new Set();
    for (const rawItem of rawItems) {
      const acceptsDetail = /[:：]\s*$/.test(rawItem);
      const item = acceptsDetail ? rawItem.replace(/[:：]\s*$/, "").trim() : rawItem;
      if (!item || seen.has(item)) continue;
      seen.add(item);
      definitions.push({ item, acceptsDetail });
    }
    return definitions;
  } catch {
    return [];
  }
}

function aggregateRows(spec, rows, items) {
  if (spec.extract.type === "checkbox_section") {
    return items.map((item) => checkboxStat(item, rows));
  }

  if (spec.extract.type === "stats_table") {
    const totals = new Map();
    for (const row of rows) {
      row.values = parseStatsTable(row.text, spec.extract.heading);
      for (const [item, value] of row.values.entries()) {
        const current = totals.get(item) || { item, done: 0, total: 0 };
        current.done += value.done;
        current.total += value.total;
        totals.set(item, current);
      }
    }
    return Array.from(totals.values()).map(withRate);
  }

  throw new Error(`Unsupported extract type: ${spec.extract.type}`);
}

function checkboxStat(item, rows) {
  let total = 0;
  let done = 0;
  for (const row of rows) {
    if (!row.values.has(item)) continue;
    total += 1;
    if (row.values.get(item).done) done += 1;
  }
  return withRate({ item, done, total });
}

function withRate(stat) {
  return {
    ...stat,
    rate: stat.total > 0 ? `${Math.round((stat.done / stat.total) * 100)}%` : "-",
  };
}

function renderAutoBlock(spec, rows, stats, context) {
  const parts = [spec.block.start, ""];
  if (spec.refresh_link) {
    const value = renderTemplate(spec.refresh_link.value, context);
    const choice = encodeURIComponent(spec.refresh_link.choice);
    parts.push(`[${spec.refresh_link.text}](obsidian://quickadd?choice=${choice}&${spec.refresh_link.param}=${value})`, "");
  }

  for (const section of spec.sections || ["links", "table"]) {
    if (section === "links" && spec.links) {
      parts.push(`## ${spec.links.heading}`, "");
      parts.push(rows.map((row) => `- [[${row.path}|${row.id}]]${row.exists ? "" : "（未创建）"}`).join("\n"), "");
    }
    if (section === "table") {
      parts.push(`## ${spec.table.heading}`, "");
      parts.push("| 项目 | 完成 | 应统计 | 完成率 |");
      parts.push("| --- | ---: | ---: | ---: |");
      parts.push(stats.map((stat) => `| ${escapeTableCell(stat.item)} | ${stat.done} | ${stat.total} | ${stat.rate} |`).join("\n"));
      parts.push("");
    }
  }
  parts.push(spec.block.end);
  return parts.join("\n");
}

async function nextTargetContent(app, path, spec, autoBlock, vaultConfig, context) {
  const existing = app.vault.getAbstractFileByPath(path);
  let oldContent;
  if (existing) {
    oldContent = await app.vault.read(existing);
  } else if (spec.target.template) {
    const templatePath = resolvePath(vaultConfig, spec.target.template);
    const template = await app.vault.adapter.read(templatePath);
    oldContent = renderTemplate(template, { ...vaultConfig, ...context });
  } else {
    throw new Error(`Rollup target does not exist: ${path}`);
  }
  return upsertAutoBlock(oldContent, spec.block, autoBlock);
}

function upsertAutoBlock(content, block, autoBlock) {
  const oldContent = String(content || "");
  if (oldContent.includes(block.start) && oldContent.includes(block.end)) {
    return oldContent.replace(
      new RegExp(`${escapeRegExp(block.start)}[\\s\\S]*?${escapeRegExp(block.end)}`),
      autoBlock,
    );
  }
  return `${autoBlock}\n\n${oldContent}`;
}

function resolvePath(vaultConfig, value) {
  return vaultConfig[value] || value;
}

function activeFileInFolder(active, vaultConfig, folderKey) {
  if (!folderKey) return true;
  const folder = resolvePath(vaultConfig, folderKey).replace(/\/+$/, "");
  return Boolean(active.path && active.path.startsWith(`${folder}/`));
}

function renderTemplate(template, context) {
  return String(template || "").replace(/\{([A-Za-z0-9_]+)\}/g, (_match, key) => {
    const value = context[key];
    if (value === undefined || value === null) return "";
    return String(value);
  });
}

function parseCheckboxSection(text, heading, templateDefinitions = []) {
  const values = new Map();
  const lines = text.split(/\r?\n/);
  let inSection = false;
  for (const line of lines) {
    if (new RegExp(`^##\\s+${escapeRegExp(heading)}\\s*$`).test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^##\s+/.test(line)) break;
    if (!inSection) continue;
    const match = line.match(/^- \[([ xX])\]\s*(.*)$/);
    if (!match) continue;
    const item = checkboxItem(match[2], templateDefinitions);
    if (!item) continue;
    values.set(item, {
      done: match[1].toLowerCase() === "x",
    });
  }
  return values;
}

function checkboxItem(text, templateDefinitions) {
  const trimmed = text.trim();
  for (const definition of templateDefinitions) {
    if (trimmed === definition.item) return definition.item;
    if (
      definition.acceptsDetail
      && (trimmed.startsWith(`${definition.item}：`) || trimmed.startsWith(`${definition.item}:`))
    ) {
      return definition.item;
    }
  }
  return trimmed;
}

function escapeTableCell(text) {
  return String(text).replace(/\|/g, "&#124;");
}

function parseStatsTable(text, heading) {
  const stats = new Map();
  const lines = text.split(/\r?\n/);
  let inSection = false;
  for (const line of lines) {
    if (new RegExp(`^##\\s+${escapeRegExp(heading)}\\s*$`).test(line)) {
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

function parseWeeks(text) {
  return text
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter((item) => /^\d{4}-W\d{2}$/.test(item));
}

function sanitizeFileName(text) {
  return text.trim().replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ");
}

function normalizeMonth(text) {
  const trimmed = String(text || "").trim();
  const match = trimmed.match(/^(\d{4})-(\d{1,2})$/);
  if (match) return `${match[1]}-${match[2].padStart(2, "0")}`;
  return "";
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

function currentMonth() {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
}

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
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

function isoWeeksInMonth(monthText) {
  const match = monthText.match(/^(\d{4})-(\d{2})$/);
  if (!match) return [];

  const year = Number(match[1]);
  const month = Number(match[2]);
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0);
  const weekIds = new Set();

  for (let day = new Date(first); day <= last; day = addDays(day, 1)) {
    if (day.getDay() !== 0) continue;
    weekIds.add(isoWeekId(day));
  }

  return Array.from(weekIds);
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function writeFile(app, path, content) {
  const existing = app.vault.getAbstractFileByPath(path);
  if (existing) {
    await app.vault.modify(existing, content);
    return existing;
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
