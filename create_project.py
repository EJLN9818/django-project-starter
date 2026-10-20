#!/usr/bin/env python3
"""Convenience wrapper around Copier for the Django Project Starter template.

It keeps the same interactive feel as the original script while delegating all
rendering to Copier, so generated projects can be updated later with
``copier update``.

Usage:
    python create_project.py                       # interactive
    python create_project.py -o ./my-project       # interactive, custom output dir
    python create_project.py --no-interactive \\
        --data project_name="My Project" --data port=8000 -o ./my-project
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent

# Minimal custom logger with clear, prefixed levels.
class Log:
    @staticmethod
    def info(message: str) -> None:
        print(f"[INFO] {message}")

    @staticmethod
    def success(message: str) -> None:
        print(f"[SUCCESS] {message}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"[WARNING] {message}", file=sys.stderr)

    @staticmethod
    def error(message: str) -> None:
        print(f"[ERROR] {message}", file=sys.stderr)


class WrapperError(Exception):
    """Raised for recoverable, user-facing errors."""


def ensure_copier() -> None:
    """Fail fast with a helpful message when Copier is not installed."""
    if importlib.util.find_spec("copier") is None:
        raise WrapperError(
            "Copier is not installed. Install it with:\n"
            "    pip install 'copier>=9.0.0'\n"
            "or run this wrapper through 'pipx run copier'."
        )


def normalize_slug(name: str) -> str:
    """Derive a valid slug from a project name."""
    import re

    slug = name.strip().lower().replace("_", "-").replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def build_data(args: argparse.Namespace) -> list[str]:
    """Collect -d/--data pairs plus convenience flags into Copier data args."""
    data: dict[str, str] = {}

    if args.name:
        data["project_name"] = args.name
        data["project_slug"] = normalize_slug(args.slug or args.name)

    if args.port is not None:
        data["port"] = str(args.port)

    if args.database:
        data["database"] = args.database

    for item in args.data or []:
        if "=" not in item:
            raise WrapperError(f"Invalid --data value (expected key=value): {item}")
        key, value = item.split("=", 1)
        data[key.strip()] = value.strip()

    return [f"{key}={value}" for key, value in data.items()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Django project from the starter template.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Destination directory for the generated project.",
    )
    parser.add_argument("-n", "--name", help="Project name (implies non-interactive for this field).")
    parser.add_argument("-s", "--slug", help="Project slug (defaults to a slugified name).")
    parser.add_argument("-p", "--port", type=int, help="Exposure port.")
    parser.add_argument(
        "-d",
        "--database",
        choices=["postgresql", "sqlite"],
        help="Database backend.",
    )
    parser.add_argument(
        "--data",
        action="append",
        metavar="KEY=VALUE",
        help="Forward any extra answer to Copier (repeatable).",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite the destination directory if it already exists.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Run Copier without prompting (all required answers must be supplied).",
    )
    return parser.parse_args()


def run_copier(args: argparse.Namespace, data: list[str]) -> int:
    destination = Path(args.output) if args.output else Path.cwd()

    # Prevent accidental overwrites.
    if destination.exists() and any(destination.iterdir()) and not args.force:
        raise WrapperError(
            f"Destination '{destination}' already exists and is not empty. "
            "Use --force to overwrite or pick another --output directory."
        )

    if args.force and destination.exists():
        Log.warning(f"Removing existing destination '{destination}' (--force).")
        shutil.rmtree(destination)

    command = [sys.executable, "-m", "copier", "copy", str(TEMPLATE_DIR), str(destination)]

    if args.no_interactive or all([args.name, args.port is not None, args.database]):
        command.append("--defaults")

    for pair in data:
        command += ["--data", pair]

    if args.force:
        command.append("--overwrite")

    Log.info(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise WrapperError(f"Could not execute Copier: {exc}") from exc

    if result.returncode != 0:
        raise WrapperError(f"Copier exited with code {result.returncode}.")

    return result.returncode


def main() -> int:
    print("=" * 60)
    print("DJANGO PROJECT STARTER")
    print("=" * 60)
    print()

    try:
        ensure_copier()
        args = parse_args()
        data = build_data(args)
        run_copier(args, data)
        Log.success("Done.")
        return 0
    except WrapperError as exc:
        Log.error(str(exc))
        return 1
    except KeyboardInterrupt:
        Log.error("Operation cancelled by user.")
        return 130
    except Exception as exc:  # pragma: no cover - defensive
        Log.error(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
