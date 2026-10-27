"""Shared pytest fixtures for the template test suite."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


def _has_copier() -> bool:
    import importlib.util

    return importlib.util.find_spec("copier") is not None


requires_copier = pytest.mark.skipif(
    not _has_copier(),
    reason="Copier is not installed; run 'pip install -r requirements-dev.txt'.",
)


@pytest.fixture()
def template_root() -> Path:
    return TEMPLATE_ROOT


@pytest.fixture()
def copier_copy(tmp_path: Path):
    """Return a helper that renders the template into a tmp dir.

    Usage:
        dest = copier_copy({"project_name": "Demo", "database": "sqlite"})
    """

    def _copy(data: dict[str, object], *, defaults: bool = True) -> Path:
        from copier import run_copy

        dest = tmp_path / str(data.get("project_slug", "demo-project"))
        run_copy(
            str(TEMPLATE_ROOT),
            str(dest),
            data=data,
            defaults=defaults,
            unsafe=True,
            quiet=True,
            # Test the current commit, not the latest release tag.
            vcs_ref="HEAD",
        )
        return dest

    yield _copy

    # Best-effort cleanup (tmp_path is removed by pytest anyway).
    shutil.rmtree(tmp_path, ignore_errors=True)
