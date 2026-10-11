#!/usr/bin/env python3
"""Deterministic OfficeCLI adapter used by the final DOCX builder."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


TESTED_OFFICECLI_VERSION = "1.0.151"
OFFICECLI_DOWNLOAD_URL = "https://github.com/iOfficeAI/OfficeCLI/releases/tag/v1.0.151"
OFFICECLI_INSTALL_URL = "https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1"
OFFICECLI_INSTALL_COMMAND = f"irm {OFFICECLI_INSTALL_URL} | iex"


class OfficeCliError(RuntimeError):
    """Raised when OfficeCLI is missing or reports a failed operation."""


def resolve_officecli() -> Path | None:
    """Resolve a globally installed OfficeCLI from the current process PATH."""
    for name in ("officecli", "officecli.exe"):
        found = shutil.which(name)
        if found:
            path = Path(found)
            if path.is_file():
                return path.resolve()
    return None


def pending_windows_officecli_install() -> Path | None:
    """Return the official Windows install path when PATH has not refreshed yet."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if os.name != "nt" or not local_app_data:
        return None
    path = Path(local_app_data) / "OfficeCLI" / "officecli.exe"
    return path.resolve() if path.is_file() else None


def officecli_environment() -> dict[str, str]:
    """Return a deterministic environment for non-interactive CLI execution."""
    env = os.environ.copy()
    env["OFFICECLI_SKIP_UPDATE"] = "1"
    # Background residents can retain file handles and stdout pipes on Windows.
    # A one-shot process is slower but predictable for document generation.
    env["OFFICECLI_NO_AUTO_RESIDENT"] = "1"
    return env


def _parse_json_output(output: str) -> dict[str, Any]:
    text = output.strip()
    if not text:
        return {}
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {"raw": text}


class OfficeCli:
    def __init__(self, require_tested_version: bool = True) -> None:
        resolved = resolve_officecli()
        if resolved is None:
            raise OfficeCliError(
                "当前 Codex 进程无法调用全局 officecli。请按官方方式全局安装 OfficeCLI，"
                "然后重启 Codex 再继续："
                f"{OFFICECLI_INSTALL_COMMAND}"
            )
        self.executable = resolved
        self.version = self._read_version()
        if require_tested_version and self.version != TESTED_OFFICECLI_VERSION:
            raise OfficeCliError(
                f"OfficeCLI 版本不匹配：检测到 {self.version}，当前 skill 只验证过 "
                f"{TESTED_OFFICECLI_VERSION}。请安装固定版本，或显式使用 --allow-untested-officecli。"
            )

    def _run(
        self,
        args: list[str],
        *,
        timeout: int = 120,
        expect_json: bool = True,
        check: bool = True,
    ) -> dict[str, Any]:
        command = [str(self.executable), *args]
        completed = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            env=officecli_environment(),
        )
        combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        payload = _parse_json_output(combined) if expect_json else {"raw": combined}
        failed_payload = isinstance(payload, dict) and payload.get("success") is False
        if check and (completed.returncode != 0 or failed_payload):
            detail = payload.get("error") if isinstance(payload, dict) else None
            raise OfficeCliError(f"OfficeCLI 命令失败：{' '.join(args[:3])}\n{detail or combined}")
        payload.setdefault("returncode", completed.returncode)
        return payload

    def _read_version(self) -> str:
        result = self._run(["--version"], expect_json=False)
        raw = str(result.get("raw", "")).strip()
        match = re.search(r"\d+\.\d+\.\d+", raw)
        return match.group(0) if match else raw or "unknown"

    def _run_batch_file(self, output: Path, batch_path: Path, command_count: int) -> dict[str, Any]:
        args = ["batch", str(output), "--input", str(batch_path), "--stop-on-error", "--json"]
        timeout = max(120, min(900, 60 + command_count // 8))
        last_error: OfficeCliError | None = None
        for delay in (0.0, 0.3, 1.0):
            if delay:
                time.sleep(delay)
            try:
                return self._run(args, timeout=timeout)
            except OfficeCliError as exc:
                last_error = exc
                if "io_error" not in str(exc):
                    raise
        assert last_error is not None
        raise last_error

    def create(self, output: Path, commands: list[dict[str, Any]], *, locale: str = "zh-CN") -> dict[str, Any]:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        self._run(["create", str(output), "--force", "--locale", locale, "--json"])

        batch_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".officecli-batch.json",
                prefix=f".{output.stem}-",
                dir=output.parent,
                encoding="utf-8",
                delete=False,
            ) as handle:
                json.dump(commands, handle, ensure_ascii=False, indent=2)
                batch_path = Path(handle.name)
            return self._run_batch_file(output, batch_path, len(commands))
        finally:
            if batch_path:
                batch_path.unlink(missing_ok=True)

    def run_batch(self, output: Path, commands: list[dict[str, Any]]) -> dict[str, Any]:
        if not commands:
            return {"success": True, "data": {"summary": {"total": 0, "failed": 0}}}
        batch_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".officecli-batch.json",
                prefix=f".{output.stem}-",
                dir=output.parent,
                encoding="utf-8",
                delete=False,
            ) as handle:
                json.dump(commands, handle, ensure_ascii=False, indent=2)
                batch_path = Path(handle.name)
            return self._run_batch_file(output.resolve(), batch_path, len(commands))
        finally:
            if batch_path:
                batch_path.unlink(missing_ok=True)

    def get(self, output: Path, path: str) -> dict[str, Any]:
        return self._run(["get", str(output.resolve()), path, "--json"])

    def validate(self, output: Path) -> dict[str, Any]:
        return self._run(["validate", str(output.resolve()), "--json"], timeout=180)

    def raw(self, output: Path, part: str) -> dict[str, Any]:
        return self._run(["raw", str(output.resolve()), part, "--json"], timeout=180)

    def raw_set(self, output: Path, part: str, xpath: str, action: str, xml: str) -> dict[str, Any]:
        return self._run(
            [
                "raw-set", str(output.resolve()), part,
                "--xpath", xpath, "--action", action, "--xml", xml, "--json",
            ],
            timeout=180,
        )

    def issues(self, output: Path) -> dict[str, Any]:
        return self._run(["view", str(output.resolve()), "issues", "--json"], timeout=180)

    def stats(self, output: Path, *, native_page_count: bool = False) -> dict[str, Any]:
        # OfficeCLI only repaginates through Word on Windows; elsewhere --page-count
        # silently returns its own estimate, which must not be treated as Word's count.
        native_page_count = native_page_count and os.name == "nt"
        args = ["view", str(output.resolve()), "stats"]
        if native_page_count:
            args.append("--page-count")
        args.append("--json")
        return self._run(args, timeout=300, check=not native_page_count)

    def screenshot(self, output: Path, target: Path, *, render: str = "auto") -> dict[str, Any]:
        target.parent.mkdir(parents=True, exist_ok=True)
        return self._run(
            [
                "view",
                str(output.resolve()),
                "screenshot",
                "--grid",
                "auto",
                "--render",
                render,
                "--out",
                str(target.resolve()),
                "--json",
            ],
            timeout=300,
            expect_json=False,
        )


def json_data(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("data") if isinstance(payload, dict) else None
    return value if isinstance(value, dict) else {}


def structural_error_count(payload: dict[str, Any]) -> int:
    value = json_data(payload).get("count", 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def issue_count(payload: dict[str, Any]) -> int:
    value = json_data(payload).get("count", 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
