#!/usr/bin/env python3
"""Extract real source code and create Markdown draft pages."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import COPYRIGHT_CODE_EXTS, FRONTEND_EXTS, ensure_dir, is_known_config_file, iter_project_files, looks_binary, read_json, read_text, rel, safe_filename, write_json


LINES_PER_PAGE = 50
SPLIT_THRESHOLD_PAGES = 60


def category_weight(path: Path, project: Path) -> tuple[int, str]:
    r = rel(path, project).lower()
    name = path.name.lower()
    priority = 80
    if name in {"main.ts", "main.js", "main.tsx", "main.jsx", "app.vue", "app.tsx"} or r in {
        "src/app/page.tsx",
        "src/app/layout.tsx",
        "app/page.tsx",
        "app/layout.tsx",
    } or r.endswith("/src/app/page.tsx") or r.endswith("/src/app/layout.tsx"):
        priority = 0
    elif path.suffix.lower() in {".css", ".scss", ".sass", ".less"}:
        priority = 90
    elif "/router/" in r or "/routes/" in r or "router." in r or "routes." in r:
        priority = 10
    elif "/pages/" in r or "/views/" in r or "/app/" in r or "/screens/" in r:
        priority = 20
    elif "/api/" in r or "/apis/" in r or "/services/" in r or "request." in r:
        priority = 30
    elif "/store/" in r or "/stores/" in r or "/pinia/" in r or "/redux/" in r:
        priority = 40
    elif "/components/" in r:
        priority = 50
    elif "/utils/" in r or "/lib/" in r or "/hooks/" in r or "/composables/" in r:
        priority = 60
    elif path.suffix.lower() not in FRONTEND_EXTS:
        if any(part in r for part in ("/backend/app/", "/server/", "/api/", "/services/", "/models/", "/schemas/", "/workers/")):
            priority = 70
        elif name in {"docker-compose.yml", "docker-compose.yaml", "pyproject.toml"} or path.suffix.lower() in {".toml", ".yml", ".yaml"}:
            priority = 95
        else:
            priority = 100
    return priority, r


def should_skip_file(path: Path) -> bool:
    if path.suffix.lower() not in COPYRIGHT_CODE_EXTS:
        return True
    if is_known_config_file(path):
        return True
    if looks_binary(path):
        return True
    try:
        size = path.stat().st_size
    except OSError:
        return True
    if size <= 0 or size > 800_000:
        return True
    try:
        sample = read_text(path, limit=20_000)
    except Exception:
        return True
    lines = sample.splitlines()
    if any(len(line) > 3000 for line in lines[:80]):
        return True
    return False


def selected_line_estimate(item: dict[str, Any]) -> int:
    try:
        total = int(item.get("line_count") or 0)
    except (TypeError, ValueError):
        total = 0
    return total + 2 if total > 0 else 0


def available_pages_from_selection(selection_path: Path | None, lines_per_page: int) -> tuple[int, int, int]:
    if selection_path is None or not selection_path.exists():
        return 0, 0, 0
    data = read_json(selection_path)
    items = data.get("files") if isinstance(data, dict) else []
    if not isinstance(items, list):
        return 0, 0, 0
    available_lines = sum(selected_line_estimate(item) for item in items if isinstance(item, dict))
    unselected = sum(1 for item in items if isinstance(item, dict) and not item.get("selected") and selected_line_estimate(item) > 0)
    pages = (available_lines + lines_per_page - 1) // lines_per_page if available_lines else 0
    return available_lines, pages, unselected


def marker_for(path: Path, project: Path) -> str:
    return f"// File: {rel(path, project)}"


def load_selected_files(project: Path, selection_path: Path | None) -> list[dict[str, Any]]:
    if selection_path is None:
        raise SystemExit(
            "STOP_FOR_USER\n"
            "NEXT_ACTION: 代码抽取必须先使用 propose_code_selection.py 生成并确认 草稿/代码文件选择.json。"
        )

    data = read_json(selection_path)
    if isinstance(data, dict) and data.get("selection_required") and not data.get("user_confirmed"):
        raise SystemExit(
            "STOP_FOR_USER\n"
            "NEXT_ACTION: 代码文件选择尚未确认。请先确认或修改 草稿/代码文件选择.json，"
            "再运行 `python3 <SKILL_DIR>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage code-selection --note \"<用户确认内容>\"`。"
        )
    items = data.get("files") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise SystemExit(f"Invalid selection file: {selection_path}")

    selected = []
    for item in items:
        if not isinstance(item, dict) or not item.get("selected"):
            continue
        path_value = item.get("path")
        if not path_value:
            continue
        selected.append(
            {
                "path": str(path_value),
                "selected": True,
            }
        )
    return selected


def collect_code_lines(project: Path, selection_path: Path | None) -> tuple[list[str], list[dict[str, Any]]]:
    selected_items = load_selected_files(project, selection_path)
    all_lines: list[str] = []
    manifest_files: list[dict[str, Any]] = []

    for item in selected_items:
        path = (project / item["path"]).resolve()
        try:
            path.relative_to(project.resolve())
        except ValueError:
            raise SystemExit(f"Selected file is outside project: {path}")
        if should_skip_file(path):
            continue
        text = read_text(path)
        source_lines = text.splitlines()
        selected_lines = source_lines
        start = len(all_lines) + 1
        marker = marker_for(path, project)
        all_lines.append(marker)
        all_lines.extend(selected_lines)
        all_lines.append("")
        end = len(all_lines)
        source_end_line = len(source_lines)
        manifest_files.append(
            {
                "path": rel(path, project),
                "source_line_count": len(source_lines),
                "selected_line_start": 1,
                "selected_line_end": source_end_line,
                "selected_line_count": len(selected_lines),
                "material_line_start": start,
                "material_line_end": end,
            }
        )
    return all_lines, manifest_files


def paginate(lines: list[str], lines_per_page: int) -> list[list[str]]:
    return [lines[i : i + lines_per_page] for i in range(0, len(lines), lines_per_page)]


def write_pages_md(path: Path, title: str, software_name: str, version: str, pages: list[tuple[int, list[str]]]) -> None:
    chunks = [f"# {title}", "", f"软件名称：{software_name}", f"版本号：{version}", ""]
    for page_no, page_lines in pages:
        chunks.extend([f"## 第 {page_no} 页", "", "```text"])
        chunks.extend(page_lines)
        chunks.extend(["```", ""])
    path.write_text("\n".join(chunks), encoding="utf-8")


def write_manifest_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# 代码提取清单",
        "",
        f"- 软件名称：{manifest['software_name']}",
        f"- 版本号：{manifest['version']}",
        f"- 项目目录：{manifest['project_root']}",
        f"- 源码文件数：{manifest['file_count']}",
        f"- 材料代码行数：{manifest['material_line_count']}",
        f"- 每页行数：{manifest['lines_per_page']}",
        f"- 总页数：{manifest['total_pages']}",
        f"- 目标页数：{manifest['target_pages']}",
        f"- 候选源码可生成页数：{manifest['available_candidate_pages']}",
        f"- 补充状态：{manifest['supplement_status']}",
        f"- 输出模式：{manifest['mode']}",
        "",
        "## 文件来源",
        "",
        "| 文件 | 源码行数 | 抽取源码范围 | 抽取行数 | 材料行范围 |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for item in manifest["files"]:
        lines.append(
            f"| `{item['path']}` | {item['source_line_count']} | "
            f"{item['selected_line_start']}-{item['selected_line_end']} | "
            f"{item['selected_line_count']} | "
            f"{item['material_line_start']}-{item['material_line_end']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract(project: Path, out_dir: Path, software_name: str, version: str, lines_per_page: int, selection_path: Path | None) -> dict[str, Any]:
    ensure_dir(out_dir)
    code_lines, files = collect_code_lines(project, selection_path)
    if not code_lines:
        raise SystemExit("No selected frontend source code files found for extraction.")

    pages = paginate(code_lines, lines_per_page)
    total_pages = len(pages)
    available_lines, available_pages, unselected_count = available_pages_from_selection(selection_path, lines_per_page)
    if total_pages < SPLIT_THRESHOLD_PAGES and available_pages >= SPLIT_THRESHOLD_PAGES and unselected_count > 0:
        raise SystemExit(
            "STOP_FOR_USER\n"
            f"NEXT_ACTION: 当前已选代码只有 {total_pages} 页，但候选源码足够补齐到 {SPLIT_THRESHOLD_PAGES} 页。"
            "请在 草稿/代码文件选择.json 中继续选择补充文件，重新记录 code-selection 门禁后再抽取。"
        )
    outputs: list[str] = []

    if total_pages >= SPLIT_THRESHOLD_PAGES:
        front = list(enumerate(pages[:30], start=1))
        back = [(31 + i, page) for i, page in enumerate(pages[-30:])]
        front_path = out_dir / "代码-前30页.md"
        back_path = out_dir / "代码-后30页.md"
        write_pages_md(front_path, "代码材料（前30页）", software_name, version, front)
        write_pages_md(back_path, "代码材料（后30页）", software_name, version, back)
        outputs.extend([front_path.name, back_path.name])
        mode = "front30_back30"
    else:
        all_path = out_dir / "代码-全部.md"
        all_pages = list(enumerate(pages, start=1))
        write_pages_md(all_path, "代码材料（全部）", software_name, version, all_pages)
        outputs.append(all_path.name)
        mode = "all_under_60_pages"
    supplement_status = (
        "候选源码可达到前30页/后30页要求"
        if available_pages >= SPLIT_THRESHOLD_PAGES
        else "候选源码不足60页，按全部代码材料生成"
    )

    manifest = {
        "software_name": software_name,
        "version": version,
        "project_root": str(project.resolve()),
        "file_count": len(files),
        "material_line_count": len(code_lines),
        "source_line_count": sum(item["source_line_count"] for item in files),
        "selected_source_line_count": sum(item["selected_line_count"] for item in files),
        "lines_per_page": lines_per_page,
        "total_pages": total_pages,
        "target_pages": SPLIT_THRESHOLD_PAGES,
        "available_candidate_line_count": available_lines,
        "available_candidate_pages": available_pages,
        "supplement_status": supplement_status,
        "mode": mode,
        "selection_file": str(selection_path) if selection_path else None,
        "outputs": outputs,
        "files": files,
        "safe_software_filename": safe_filename(software_name),
    }
    write_json(out_dir / "代码提取清单.json", manifest)
    write_manifest_md(out_dir / "代码提取清单.md", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--analysis", help="Optional project analysis JSON; retained for workflow traceability")
    parser.add_argument("--software-name", required=True)
    parser.add_argument("--version", default="V1.0")
    parser.add_argument("--out-dir", default="软件著作权申请资料/草稿")
    parser.add_argument("--lines-per-page", type=int, default=LINES_PER_PAGE)
    parser.add_argument("--selection", help="Editable JSON file created by propose_code_selection.py")
    args = parser.parse_args()

    project = Path(args.project)
    if not project.exists():
        raise SystemExit(f"Project not found: {project}")
    if args.analysis and not Path(args.analysis).exists():
        raise SystemExit(f"Analysis JSON not found: {args.analysis}")

    selection = Path(args.selection) if args.selection else None
    if selection and not selection.exists():
        raise SystemExit(f"Selection JSON not found: {selection}")

    manifest = extract(project, Path(args.out_dir), args.software_name, args.version, args.lines_per_page, selection)
    print(f"OK code drafts: {args.out_dir}")
    print(f"Selected files: {manifest['file_count']}")
    print(f"Mode: {manifest['mode']}")
    print(f"Total pages: {manifest['total_pages']}")
    print(f"Outputs: {', '.join(manifest['outputs'])}")


if __name__ == "__main__":
    main()
