#!/usr/bin/env python3
"""Export Feishu cloud docs as .docx files.

The script reads credentials from environment variables and never writes
secrets to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_URL = "https://open.feishu.cn/open-apis"
DEFAULT_OUTPUT = "10_原始材料/飞书云文档导出"
DOC_TYPES = {"doc", "docx"}


class FeishuError(RuntimeError):
    pass


@dataclass
class CloudItem:
    name: str
    token: str
    type: str
    path_parts: tuple[str, ...]
    url: str = ""
    source: str = "drive"


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    token = args.access_token or get_tenant_access_token(args.app_id, args.app_secret)
    manifest_path = output_dir / "manifest.jsonl"
    roots = resolve_roots(args)

    print(f"Output: {output_dir}")
    for root in roots:
        print(f"Root {root['kind']}: {root['token']}")
    print("Mode: dry-run" if args.dry_run else "Mode: export")

    stats = {"seen": 0, "exported": 0, "skipped": 0, "failed": 0}
    with manifest_path.open("a", encoding="utf-8") as manifest:
        for item in collect_items(token, roots, args.recursive):
            stats["seen"] += 1
            if item.type not in DOC_TYPES:
                stats["skipped"] += 1
                print(f"skip unsupported type={item.type}: {'/'.join(item.path_parts + (item.name,))}")
                continue

            relative_dir = Path(*[safe_name(part) for part in item.path_parts])
            target_dir = output_dir / relative_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / ensure_suffix(safe_name(item.name), ".docx")

            record: dict[str, Any] = {
                "name": item.name,
                "token": item.token,
                "type": item.type,
                "source": item.source,
                "url": item.url,
                "path": str(target_path),
                "exported_at": now_iso(),
            }

            if args.dry_run:
                print(f"would export: {target_path}")
                manifest.write(json.dumps({**record, "status": "dry_run"}, ensure_ascii=False) + "\n")
                continue

            if target_path.exists() and not args.overwrite:
                stats["skipped"] += 1
                print(f"exists, skip: {target_path}")
                manifest.write(json.dumps({**record, "status": "exists"}, ensure_ascii=False) + "\n")
                continue

            try:
                export_docx(token, item, target_path, args.poll_interval, args.timeout)
                stats["exported"] += 1
                size = target_path.stat().st_size
                print(f"exported: {target_path} ({size} bytes)")
                manifest.write(json.dumps({**record, "status": "exported", "size": size}, ensure_ascii=False) + "\n")
            except Exception as exc:
                stats["failed"] += 1
                print(f"failed: {item.name}: {exc}", file=sys.stderr)
                manifest.write(json.dumps({**record, "status": "failed", "error": str(exc)}, ensure_ascii=False) + "\n")

    print(
        "Done: "
        f"seen={stats['seen']} exported={stats['exported']} "
        f"skipped={stats['skipped']} failed={stats['failed']}"
    )
    return 1 if stats["failed"] else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Feishu Drive folder docs to local .docx files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--app-id", default=os.getenv("FEISHU_APP_ID"), help="Feishu App ID")
    parser.add_argument("--app-secret", default=os.getenv("FEISHU_APP_SECRET"), help="Feishu App Secret")
    parser.add_argument(
        "--access-token",
        default=os.getenv("FEISHU_ACCESS_TOKEN"),
        help="Existing tenant_access_token or user_access_token. Overrides app credentials.",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("FEISHU_ROOT_URL"),
        help="Feishu folder, doc/docx, or wiki URL. Can also be a bare token.",
    )
    parser.add_argument("--folder-token", default=os.getenv("FEISHU_FOLDER_TOKEN"), help="Drive folder token")
    parser.add_argument("--wiki-node-token", default=os.getenv("FEISHU_WIKI_NODE_TOKEN"), help="Wiki node token")
    parser.add_argument("--output-dir", default=os.getenv("FEISHU_EXPORT_OUT", DEFAULT_OUTPUT))
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not enter subfolders")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .docx files")
    parser.add_argument("--dry-run", action="store_true", help="List export targets without downloading")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between export status polls")
    parser.add_argument("--timeout", type=float, default=180.0, help="Seconds to wait for each export task")
    parser.set_defaults(recursive=True)
    args = parser.parse_args()

    if not args.url and not args.folder_token and not args.wiki_node_token:
        parser.error("set --url, --folder-token, --wiki-node-token, FEISHU_ROOT_URL, FEISHU_FOLDER_TOKEN, or FEISHU_WIKI_NODE_TOKEN")
    if not args.access_token and (not args.app_id or not args.app_secret):
        parser.error("set FEISHU_APP_ID and FEISHU_APP_SECRET, or set FEISHU_ACCESS_TOKEN")
    return args


def resolve_roots(args: argparse.Namespace) -> list[dict[str, str]]:
    roots: list[dict[str, str]] = []
    if args.url:
        roots.append(parse_resource(args.url))
    if args.folder_token:
        roots.append({"kind": "folder", "token": args.folder_token})
    if args.wiki_node_token:
        roots.append({"kind": "wiki", "token": args.wiki_node_token})
    return roots


def parse_resource(value: str) -> dict[str, str]:
    text = value.strip()
    if not text:
        raise FeishuError("empty Feishu URL or token")

    parsed = urllib.parse.urlparse(text)
    parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]

    if parsed.scheme and parsed.netloc:
        for marker in ("folder", "wiki", "docx", "docs", "doc"):
            if marker in parts:
                idx = parts.index(marker)
                if idx + 1 < len(parts):
                    token = parts[idx + 1].split("?")[0].split("#")[0]
                    kind = "folder" if marker == "folder" else marker
                    kind = "doc" if kind in {"docs", "doc"} else kind
                    return {"kind": kind, "token": token}
        raise FeishuError(f"cannot find folder/doc/wiki token in URL: {text}")

    if text.startswith("fld"):
        return {"kind": "folder", "token": text}
    if text.startswith("wiki") or text.startswith("wik"):
        return {"kind": "wiki", "token": text}
    if text.startswith("docx"):
        return {"kind": "docx", "token": text}
    if text.startswith("doc"):
        return {"kind": "doc", "token": text}
    return {"kind": "docx", "token": text}


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    data = call_json(
        "POST",
        "/auth/v3/tenant_access_token/internal",
        body={"app_id": app_id, "app_secret": app_secret},
        access_token=None,
    )
    access_token = data.get("tenant_access_token")
    if not access_token:
        raise FeishuError("tenant_access_token missing in auth response")
    return access_token


def collect_items(access_token: str, roots: list[dict[str, str]], recursive: bool) -> list[CloudItem]:
    items: list[CloudItem] = []
    for root in roots:
        kind = root["kind"]
        token = root["token"]
        if kind == "folder":
            items.extend(walk_folder(access_token, token, (), recursive))
        elif kind == "wiki":
            node = get_wiki_node(access_token, token)
            items.extend(walk_wiki_node(access_token, node, (), recursive, include_self=True))
        elif kind in DOC_TYPES:
            items.extend(walk_doc_or_wiki(access_token, token, kind, recursive))
        else:
            raise FeishuError(f"unsupported root kind: {kind}")
    return items


def walk_doc_or_wiki(access_token: str, token: str, doc_type: str, recursive: bool) -> list[CloudItem]:
    try:
        node = get_wiki_node(access_token, token)
    except FeishuError:
        return [CloudItem(name=token, token=token, type=doc_type, path_parts=(), source="drive")]
    return walk_wiki_node(access_token, node, (), recursive, include_self=True)


def walk_folder(
    access_token: str,
    folder_token: str,
    path_parts: tuple[str, ...],
    recursive: bool,
) -> list[CloudItem]:
    items: list[CloudItem] = []
    for raw in list_folder(access_token, folder_token):
        item_type = str(raw.get("type", "")).strip()
        token = str(raw.get("token", "")).strip()
        name = str(raw.get("name", token or "untitled")).strip() or token or "untitled"
        url = str(raw.get("url", "")).strip()

        shortcut = raw.get("shortcut_info") or {}
        if shortcut:
            item_type = str(shortcut.get("target_type") or item_type).strip()
            token = str(shortcut.get("target_token") or token).strip()

        if item_type == "folder":
            if recursive:
                next_parts = path_parts + (name,)
                items.extend(walk_folder(access_token, token, next_parts, recursive))
            continue

        items.append(CloudItem(name=name, token=token, type=item_type, path_parts=path_parts, url=url, source="drive"))
    return items


def get_wiki_node(access_token: str, token: str) -> dict[str, Any]:
    data = call_json("GET", "/wiki/v2/spaces/get_node", query={"token": token}, access_token=access_token)
    node = data.get("node") or data
    if not isinstance(node, dict) or not node.get("node_token"):
        raise FeishuError(f"not a wiki node or cannot resolve wiki node: {token}")
    return node


def walk_wiki_node(
    access_token: str,
    node: dict[str, Any],
    path_parts: tuple[str, ...],
    recursive: bool,
    include_self: bool,
) -> list[CloudItem]:
    items: list[CloudItem] = []
    title = str(node.get("title") or node.get("node_token") or "untitled").strip()
    obj_type = str(node.get("obj_type") or "").strip()
    obj_token = str(node.get("obj_token") or "").strip()
    node_token = str(node.get("node_token") or "").strip()
    space_id = str(node.get("space_id") or node.get("origin_space_id") or "").strip()

    current_parts = path_parts + (title,) if include_self and title else path_parts
    if include_self and obj_token:
        items.append(CloudItem(name=title, token=obj_token, type=obj_type, path_parts=path_parts, source="wiki"))

    if recursive and space_id and node_token and bool(node.get("has_child")):
        for child in list_wiki_children(access_token, space_id, node_token):
            items.extend(walk_wiki_node(access_token, child, current_parts, recursive, include_self=True))
    return items


def list_wiki_children(access_token: str, space_id: str, parent_node_token: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    page_token = ""
    while True:
        query = {"page_size": 50, "parent_node_token": parent_node_token}
        if page_token:
            query["page_token"] = page_token
        data = call_json(
            "GET",
            f"/wiki/v2/spaces/{urllib.parse.quote(space_id, safe='')}/nodes",
            query=query,
            access_token=access_token,
        )
        nodes.extend(data.get("items") or [])

        page_token = str(data.get("page_token") or "").strip()
        has_more = bool(data.get("has_more"))
        if not has_more or not page_token:
            break
    return nodes


def list_folder(access_token: str, folder_token: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page_token = ""
    while True:
        query = {"folder_token": folder_token, "page_size": 200}
        if page_token:
            query["page_token"] = page_token
        data = call_json("GET", "/drive/v1/files", query=query, access_token=access_token)
        files.extend(data.get("files") or [])

        page_token = str(data.get("next_page_token") or data.get("page_token") or "").strip()
        has_more = bool(data.get("has_more"))
        if not has_more or not page_token:
            break
    return files


def export_docx(
    access_token: str,
    item: CloudItem,
    target_path: Path,
    poll_interval: float,
    timeout: float,
) -> None:
    data = call_json(
        "POST",
        "/drive/v1/export_tasks",
        body={"file_extension": "docx", "token": item.token, "type": item.type},
        access_token=access_token,
    )
    ticket = data.get("ticket")
    if not ticket:
        raise FeishuError("export ticket missing")

    deadline = time.monotonic() + timeout
    last_status = ""
    while time.monotonic() < deadline:
        result_data = call_json(
            "GET",
            f"/drive/v1/export_tasks/{urllib.parse.quote(str(ticket), safe='')}",
            query={"token": item.token},
            access_token=access_token,
        )
        result = result_data.get("result") or {}
        file_token = result.get("file_token")
        job_status = result.get("job_status")
        job_error = result.get("job_error_msg") or ""
        last_status = f"job_status={job_status} {job_error}".strip()
        if file_token:
            download_export_file(access_token, str(file_token), target_path)
            return
        if job_error and str(job_error).lower() not in {"success", "ok"}:
            raise FeishuError(last_status)
        time.sleep(poll_interval)

    raise FeishuError(f"export timeout: ticket={ticket} {last_status}")


def download_export_file(access_token: str, file_token: str, target_path: Path) -> None:
    path = f"/drive/v1/export_tasks/file/{urllib.parse.quote(file_token, safe='')}/download"
    request = urllib.request.Request(
        BASE_URL + path,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    file.write(chunk)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise FeishuError(f"download failed HTTP {exc.code}: {body}") from exc


def call_json(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    access_token: str | None,
) -> dict[str, Any]:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query)

    payload = None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if body is not None:
        payload = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        raise FeishuError(f"HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise FeishuError(f"network error: {exc.reason}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FeishuError(f"non-json response: {raw[:200]}") from exc

    code = parsed.get("code", 0)
    if code != 0:
        raise FeishuError(f"Feishu API error {code}: {parsed.get('msg') or parsed}")
    data = parsed.get("data")
    return data if isinstance(data, dict) else parsed


def safe_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:180] or "untitled"


def ensure_suffix(name: str, suffix: str) -> str:
    if name.lower().endswith(suffix):
        return name
    return name + suffix


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


if __name__ == "__main__":
    raise SystemExit(main())
