#!/usr/bin/env python3
"""Convert .docx files to Markdown with extracted local images."""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    docx_files = find_docx_files(source)
    output_dir = Path(args.output_dir) if args.output_dir else None
    converted = 0

    for docx_path in docx_files:
        md_path = markdown_path(docx_path, source, output_dir)
        if md_path.exists() and not args.overwrite:
            print(f"exists, skip: {md_path}")
            continue

        DocxConverter(docx_path, md_path, args.assets_dir).convert()
        converted += 1
        print(f"converted: {docx_path} -> {md_path}")

    print(f"Done: found={len(docx_files)} converted={converted}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one .docx file or a directory of .docx files to Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("source", help="A .docx file or a directory to scan recursively")
    parser.add_argument("-o", "--output-dir", help="Directory for generated Markdown")
    parser.add_argument(
        "--assets-dir",
        default="assets/figures",
        help="Image directory relative to the current working directory",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing Markdown files")
    return parser.parse_args()


def find_docx_files(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".docx":
        return [source]
    if source.is_dir():
        return sorted(source.rglob("*.docx"))
    raise SystemExit(f"source is not a .docx file or directory: {source}")


def markdown_path(docx_path: Path, source: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return docx_path.with_suffix(".md")
    if source.is_file():
        return output_dir / docx_path.with_suffix(".md").name
    return output_dir / docx_path.relative_to(source).with_suffix(".md")


class DocxConverter:
    def __init__(self, docx_path: Path, md_path: Path, assets_dir: str) -> None:
        self.docx_path = docx_path
        self.md_path = md_path
        self.assets_dir = Path(assets_dir.strip("/\\") or "assets/figures")
        self.asset_root = self.assets_dir / slug(docx_path.stem)
        self.image_count = 0
        self.archive: zipfile.ZipFile
        self.relationships: dict[str, str] = {}

    def convert(self) -> None:
        self.md_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.docx_path) as archive:
            self.archive = archive
            self.relationships = self.read_relationships()
            body = ET.fromstring(archive.read("word/document.xml")).find("w:body", NS)
            if body is None:
                raise RuntimeError(f"docx has no body: {self.docx_path}")

            lines: list[str] = []
            for child in body:
                if tag_name(child) == "p":
                    block = self.paragraph(child)
                    if block:
                        lines.extend([block, ""])
                elif tag_name(child) == "tbl":
                    table = self.table(child)
                    if table:
                        lines.extend(table + [""])

        self.md_path.write_text(clean_markdown(lines), encoding="utf-8")

    def read_relationships(self) -> dict[str, str]:
        rels_path = "word/_rels/document.xml.rels"
        if rels_path not in self.archive.namelist():
            return {}
        root = ET.fromstring(self.archive.read(rels_path))
        return {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in root.findall("rel:Relationship", NS)
            if rel.attrib.get("Id") and rel.attrib.get("Target")
        }

    def paragraph(self, paragraph: ET.Element) -> str:
        text = self.inline_markdown(paragraph).strip()
        if not text:
            return ""

        heading = heading_level(paragraph)
        if heading:
            return f"{'#' * heading} {text}"
        if paragraph.find("w:pPr/w:numPr", NS) is not None:
            return f"- {text}"
        return text

    def table(self, table: ET.Element) -> list[str]:
        rows: list[list[str]] = []
        for row in table.findall("w:tr", NS):
            cells = [
                "<br>".join(
                    block.replace("\n", "<br>")
                    for paragraph in cell.findall("w:p", NS)
                    if (block := self.paragraph(paragraph))
                )
                for cell in row.findall("w:tc", NS)
            ]
            if cells:
                rows.append(cells)

        if not rows:
            return []

        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        return [
            "| " + " | ".join(escape_cell(cell) for cell in rows[0]) + " |",
            "| " + " | ".join("---" for _ in rows[0]) + " |",
            *("| " + " | ".join(escape_cell(cell) for cell in row) + " |" for row in rows[1:]),
        ]

    def inline_markdown(self, element: ET.Element) -> str:
        parts: list[str] = []
        for node in element.iter():
            name = tag_name(node)
            if name == "t" and node.text:
                parts.append(node.text)
            elif name == "tab":
                parts.append(" ")
            elif name == "br":
                parts.append("\n")
            elif name == "blip" and (image := self.extract_image(node)):
                parts.append(image)
        return "".join(parts)

    def extract_image(self, node: ET.Element) -> str:
        rid = node.attrib.get(f"{{{NS['r']}}}embed") or node.attrib.get(f"{{{NS['r']}}}link")
        source = word_target(self.relationships.get(rid or ""))
        if not source or source not in self.archive.namelist():
            return ""

        self.image_count += 1
        image_name = f"image-{self.image_count:03d}{Path(source).suffix or '.png'}"
        self.asset_root.mkdir(parents=True, exist_ok=True)
        image_path = self.asset_root / image_name
        with self.archive.open(source) as src, image_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        return f"![{Path(source).stem}]({relative_link(self.md_path.parent, image_path)})"


def word_target(target: str) -> str:
    if not target:
        return ""
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("word", target))


def relative_link(from_dir: Path, target: Path) -> str:
    return os.path.relpath(target, from_dir).replace(os.sep, "/")


def heading_level(paragraph: ET.Element) -> int:
    style = paragraph.find("w:pPr/w:pStyle", NS)
    value = style.attrib.get(f"{{{NS['w']}}}val", "") if style is not None else ""
    match = re.search(r"heading([1-6])|标题([1-6])", value, re.IGNORECASE)
    return int(next(group for group in match.groups() if group)) if match else 0


def tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def slug(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value).strip(" .-")
    return re.sub(r"-+", "-", value)[:120] or "untitled"


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|")


def clean_markdown(lines: list[str]) -> str:
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return text.strip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
