const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const rollup = require(path.join(root, "automation/quickadd/rollup.js"));

function repoText(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function file(pathname) {
  return {
    path: pathname,
    basename: pathname.split("/").pop().replace(/\.md$/, ""),
  };
}

function makeApp(initialFiles) {
  const files = new Map(Object.entries(initialFiles));
  const folders = new Set();
  const opened = [];

  for (const pathname of files.keys()) {
    const parts = pathname.split("/");
    for (let index = 1; index < parts.length; index += 1) {
      folders.add(parts.slice(0, index).join("/"));
    }
  }

  const app = {
    vault: {
      adapter: {
        async read(pathname) {
          if (!files.has(pathname)) throw new Error(`missing fixture file: ${pathname}`);
          return files.get(pathname);
        },
      },
      getAbstractFileByPath(pathname) {
        if (files.has(pathname)) return file(pathname);
        return folders.has(pathname) ? { path: pathname } : null;
      },
      async read(target) {
        return files.get(target.path);
      },
      async modify(target, content) {
        files.set(target.path, content);
      },
      async create(pathname, content) {
        files.set(pathname, content);
        return file(pathname);
      },
      async createFolder(pathname) {
        folders.add(pathname);
      },
    },
    workspace: {
      getActiveFile() {
        return null;
      },
      getLeaf() {
        return {
          async openFile(target) {
            opened.push(target.path);
          },
        };
      },
    },
  };

  return { app, files, opened };
}

function baseFiles() {
  return {
    ".sunday-note-agent/config/quickadd-rollups.json": repoText("config/quickadd-rollups.json"),
    "个人模板/周记录.md": repoText("templates/周记录.md"),
    "个人模板/月记录.md": repoText("templates/月记录.md"),
    "个人模板/每日记录.md": [
      "## 打卡",
      "",
      "- [ ] 学习阅读：",
      "- [ ] 运动健身：",
    ].join("\n"),
    "20_每日记录/2026-06-29.md": "## 打卡\n\n- [x] 学习阅读：书 A\n- [ ] 运动健身：跑步",
    "20_每日记录/2026-07-05.md": "## 打卡\n\n- [ ] 学习阅读：书 B\n- [x] 临时事项 | 户外",
  };
}

async function testWeeklyRollup() {
  const fixture = makeApp(baseFiles());
  await rollup({ app: fixture.app, variables: { rollup: "weekly_checkins", week: "2026-W27" } });

  const targetPath = "21_每周记录/2026-W27.md";
  const output = fixture.files.get(targetPath);
  assert.ok(output, "missing weekly target should be created");
  assert.match(output, /# 2026-W27/);
  assert.match(output, /\| 学习阅读 \| 1 \| 2 \| 50% \|/);
  assert.match(output, /\| 运动健身 \| 0 \| 1 \| 0% \|/);
  assert.match(output, /\| 临时事项 &#124; 户外 \| 1 \| 1 \| 100% \|/);
  assert.match(output, /2026-06-30\.md\|2026-06-30\]\]（未创建）/);
  assert.match(output, /## 个人周总结/);

  fixture.files.set(targetPath, `${output}\n\n人工补充`);
  await rollup({ app: fixture.app, variables: { rollup: "weekly_checkins", week: "2026-W27" } });
  const refreshed = fixture.files.get(targetPath);
  assert.equal((refreshed.match(/SN:weekly:auto:start/g) || []).length, 1);
  assert.match(refreshed, /人工补充/);
}

async function testMonthlyRollup() {
  const files = baseFiles();
  for (const week of ["2026-W27", "2026-W28", "2026-W29", "2026-W30", "2026-W31"]) {
    files[`21_每周记录/${week}.md`] = [
      "## 打卡统计",
      "",
      "| 项目 | 完成 | 应统计 | 完成率 |",
      "| --- | ---: | ---: | ---: |",
      "| 学习阅读 | 1 | 2 | 50% |",
    ].join("\n");
  }
  const fixture = makeApp(files);
  await rollup({ app: fixture.app, variables: { rollup: "month_pack_checkins", month: "2026-07" } });

  const output = fixture.files.get("22_每月记录/2026-07.md");
  assert.ok(output, "missing month target should be created");
  assert.match(output, /\| 学习阅读 \| 4 \| 8 \| 50% \|/);
  for (const week of ["W27", "W28", "W29", "W30"]) assert.match(output, new RegExp(week));
  assert.doesNotMatch(output, /W31/);
  assert.match(output, /## 个人月总结/);
}

async function testRequiredContextStopsWithoutWriting() {
  const files = baseFiles();
  const fixture = makeApp(files);
  await rollup({
    app: fixture.app,
    variables: { rollup: "month_pack_checkins", month: "not-a-month" },
  });
  assert.equal(fixture.opened.length, 0);
  assert.equal(
    Array.from(fixture.files.keys()).some((pathname) => pathname.startsWith("22_每月记录/")),
    false,
  );
}

(async () => {
  await testWeeklyRollup();
  await testMonthlyRollup();
  await testRequiredContextStopsWithoutWriting();
  console.log("rollup fixture passed");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
