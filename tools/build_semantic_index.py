#!/usr/bin/env python3
"""Build a deterministic JSONL semantic index from Markdown documentation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1

APP_BY_FOLDER = {
    "platform": "PlatformApp",
    "tenant": "TenantApp",
    "customer": "CustomerApp",
    "station-staff": "StationStaffApp",
    "service-staff": "ServiceStaffApp",
    "cashier": "CashierApp",
}

APP_NAMES = tuple(APP_BY_FOLDER.values())

COMMAND_RE = re.compile(r"`([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)`")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
ENDPOINT_RE = re.compile(
    r"`?\b(GET|POST|PATCH|PUT|DELETE)\b`?\s*(?:\|\s*)?`?(/api/[A-Za-z0-9_./{}:-]+)"
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True)
class Section:
    title: str
    heading_path: list[str]
    start_line: int
    end_line: int
    markdown: str


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[`*_{}\[\]()<>:|/\\]+", " ", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "root"


def normalize_module_name(filename: str) -> str | None:
    if filename == "README.md":
        return None

    stem = filename.removesuffix(".md")
    for suffix in ("-contracts", "-api"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def classify(rel_path: str) -> dict[str, Any]:
    parts = rel_path.split("/")
    meta: dict[str, Any] = {
        "layer": "documentation",
        "kind": "documentation",
        "app": None,
        "module_context": None,
        "module": None,
    }

    if rel_path == "docs/data-model.md":
        meta["layer"] = "data"
        meta["kind"] = "data_model"
        return meta

    if rel_path == "docs/documentation-roadmap.md":
        meta["kind"] = "documentation_roadmap"
        return meta

    if len(parts) < 2 or parts[0] != "docs":
        return meta

    folder = parts[1]

    if folder == "apps":
        meta["layer"] = "app"
        if len(parts) > 2 and parts[2] == "_shared":
            meta["kind"] = "app_shared"
        elif len(parts) > 2:
            meta["kind"] = "app"
            meta["app"] = APP_BY_FOLDER.get(parts[2])
        return meta

    if folder == "modules":
        meta["layer"] = "module"
        if len(parts) == 2:
            meta["kind"] = "module_index"
            return meta
        if len(parts) > 2 and parts[2] == "_shared":
            meta["kind"] = "module_shared"
            return meta
        if len(parts) > 2 and parts[2] == "module-map.md":
            meta["kind"] = "module_map"
            return meta
        if len(parts) > 2:
            meta["module_context"] = parts[2]
            filename = parts[-1]
            meta["module"] = normalize_module_name(filename)
            if filename == "README.md":
                meta["kind"] = "module_context"
            elif filename.endswith("-contracts.md"):
                meta["kind"] = "module_contract"
            elif filename.endswith("-api.md"):
                meta["kind"] = "module_api"
            else:
                meta["kind"] = "module"
        return meta

    if folder == "api":
        meta["layer"] = "api"
        meta["kind"] = "api_standard"
        return meta

    if folder == "database":
        meta["layer"] = "database"
        meta["kind"] = "database"
        return meta

    if folder == "semantic":
        meta["kind"] = "semantic_index_doc"
        return meta

    return meta


def iter_markdown_files(docs_dir: Path) -> list[Path]:
    return sorted(path for path in docs_dir.rglob("*.md") if path.is_file())


def parse_sections(markdown: str, fallback_title: str) -> list[Section]:
    lines = markdown.splitlines()
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []
    current_title: str | None = None
    current_path: list[str] = []
    current_start = 1
    current_lines: list[str] = []
    in_fence = False

    def finish(end_line: int) -> None:
        nonlocal current_title, current_lines, current_path, current_start
        if current_title is None:
            return
        body_without_heading = "\n".join(current_lines[1:]).strip()
        if body_without_heading:
            sections.append(
                Section(
                    title=current_title,
                    heading_path=list(current_path),
                    start_line=current_start,
                    end_line=end_line,
                    markdown="\n".join(current_lines).strip(),
                )
            )

    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence

        match = HEADING_RE.match(line) if not in_fence else None
        if match:
            finish(index - 1)
            level = len(match.group(1))
            title = match.group(2).strip()
            stack = [entry for entry in stack if entry[0] < level]
            stack.append((level, title))
            current_title = title
            current_path = [entry[1] for entry in stack]
            current_start = index
            current_lines = [line]
        elif current_title is not None:
            current_lines.append(line)

    finish(len(lines))

    if sections:
        return sections

    stripped = markdown.strip()
    if not stripped:
        return []

    return [
        Section(
            title=fallback_title,
            heading_path=[fallback_title],
            start_line=1,
            end_line=max(1, len(lines)),
            markdown=stripped,
        )
    ]


def extract_links(markdown: str) -> list[str]:
    return sorted({match.group(1) for match in LINK_RE.finditer(markdown)})


def extract_symbols(markdown: str) -> dict[str, list[str]]:
    code_spans = {match.group(1) for match in CODE_SPAN_RE.finditer(markdown)}
    commands = {match.group(1) for match in COMMAND_RE.finditer(markdown)}
    endpoints = {
        f"{match.group(1)} {match.group(2).rstrip('`')}"
        for match in ENDPOINT_RE.finditer(markdown)
    }
    identifiers = {
        value
        for value in code_spans
        if re.fullmatch(r"[a-z][a-z0-9_]*", value) and "_" in value
    }
    apps = {name for name in APP_NAMES if name in markdown}

    return {
        "apps": sorted(apps),
        "commands": sorted(commands),
        "endpoints": sorted(endpoints),
        "identifiers": sorted(identifiers),
    }


def build_embedding_text(record: dict[str, Any], section_markdown: str) -> str:
    meta = record["metadata"]
    parts = [
        f"Semantic ID: {record['semantic_id']}",
        f"Layer: {meta['layer']}",
        f"Kind: {meta['kind']}",
        f"App: {meta['app'] or ''}",
        f"Module context: {meta['module_context'] or ''}",
        f"Module: {meta['module'] or ''}",
        f"Heading: {' > '.join(record['heading_path'])}",
        f"Source: {record['source']['path']}:{record['source']['start_line']}",
        "",
        section_markdown,
    ]
    return "\n".join(parts).strip()


def make_record(
    repo_root: Path,
    path: Path,
    section: Section,
    id_counts: dict[str, int],
) -> dict[str, Any]:
    rel_path = path.relative_to(repo_root).as_posix()
    metadata = classify(rel_path)
    path_slug = slugify(path.with_suffix("").relative_to(repo_root).as_posix())
    heading_slug = slugify(" ".join(section.heading_path))
    base_id = f"{metadata['layer']}.{path_slug}.{heading_slug}"
    id_counts[base_id] += 1
    semantic_id = base_id if id_counts[base_id] == 1 else f"{base_id}.{id_counts[base_id]}"
    content_hash = hashlib.sha256(section.markdown.encode("utf-8")).hexdigest()

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "semantic_id": semantic_id,
        "title": section.title,
        "heading_path": section.heading_path,
        "metadata": metadata,
        "source": {
            "path": rel_path,
            "start_line": section.start_line,
            "end_line": section.end_line,
        },
        "symbols": extract_symbols(section.markdown),
        "links": extract_links(section.markdown),
        "content_hash": content_hash,
        "text": section.markdown,
    }
    record["embedding_text"] = build_embedding_text(record, section.markdown)
    record["token_estimate"] = max(1, len(record["embedding_text"]) // 4)
    return record


def build_index(repo_root: Path, docs_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    id_counts: dict[str, int] = defaultdict(int)

    for path in iter_markdown_files(docs_dir):
        markdown = path.read_text(encoding="utf-8")
        fallback_title = path.stem.replace("-", " ").title()
        for section in parse_sections(markdown, fallback_title):
            records.append(make_record(repo_root, path, section, id_counts))

    return records


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default="docs", help="Documentation directory to index.")
    parser.add_argument(
        "--output",
        default="docs/semantic/index.jsonl",
        help="Generated JSONL output path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    docs_dir = (repo_root / args.docs).resolve()
    output_path = (repo_root / args.output).resolve()

    if not docs_dir.exists():
        raise SystemExit(f"Documentation directory not found: {docs_dir}")

    records = build_index(repo_root, docs_dir)
    write_jsonl(records, output_path)
    print(f"Wrote {len(records)} semantic records to {output_path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
