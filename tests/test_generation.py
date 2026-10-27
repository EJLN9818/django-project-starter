"""End-to-end tests: render the template and assert on the output tree."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import TEMPLATE_ROOT, requires_copier

BASE_DATA = {
    "project_name": "Demo Project",
    "project_slug": "demo-project",
    "port": 8000,
    "database": "postgresql",
    "postgres_db": "demo_project",
    "postgres_user": "demo_project",
    "django_version": "5.2.18",
    "python_version": "3.13",
    "include_precommit": True,
    "init_git": False,
}

COMMON_FILES = [
    "Dockerfile",
    "Dockerfile.dev",
    "docker-compose.yml",
    "compose.dev.yml",
    "entrypoint.sh",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    ".editorconfig",
    ".gitattributes",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    "README.md",
    "backend/manage.py",
    "backend/__init__.py",
    "backend/demo_project/__init__.py",
    "backend/demo_project/settings.py",
    "backend/demo_project/wsgi.py",
    "backend/demo_project/asgi.py",
    "backend/demo_project/urls.py",
    "backend/demo_project/test_smoke.py",
]


def _sqlite_data(**overrides):
    """BASE_DATA with the PostgreSQL-only answers removed."""
    data = {**BASE_DATA, "database": "sqlite", **overrides}
    for key in ("postgres_db", "postgres_user"):
        data.pop(key, None)
    return data


@requires_copier
def test_common_structure(copier_copy):
    dest = copier_copy(BASE_DATA)

    for relative in COMMON_FILES:
        assert (dest / relative).is_file(), f"missing {relative}"

    # Empty helper directories exist.
    for directory in ("docs", "data", "static"):
        assert (dest / directory).is_dir(), f"missing {directory}/"

    # The generated workflow uses Docker Compose directly, not make.
    assert not (dest / "Makefile").exists()


@requires_copier
def test_postgresql_configuration(copier_copy):
    dest = copier_copy(BASE_DATA)

    settings = (dest / "backend/demo_project/settings.py").read_text()
    assert "django.db.backends.postgresql" in settings
    assert "environ.Env" in settings
    assert "whitenoise.middleware.WhiteNoiseMiddleware" in settings
    assert 'default="localhost"' in settings
    assert "ImproperlyConfigured" in settings
    assert 'SECRET_KEY.startswith("django-insecure-")' in settings
    assert "len(SECRET_KEY) < 50" in settings
    assert 'encoding="utf-8-sig"' in settings

    compose = (dest / "docker-compose.yml").read_text()
    assert "postgres:16-alpine" in compose
    assert "healthcheck" in compose
    assert 'DEBUG: "False"' in compose
    assert "DB_HOST: db" in compose

    requirements = (dest / "requirements.txt").read_text()
    assert "psycopg2-binary" in requirements
    assert "whitenoise" in requirements

    env_example = (dest / ".env.example").read_text()
    assert "POSTGRES_DB=demo_project" in env_example
    assert "POSTGRES_PASSWORD=change-me" in env_example
    assert "DB_HOST=localhost" in env_example


@requires_copier
def test_sqlite_configuration(copier_copy):
    dest = copier_copy(_sqlite_data())

    settings = (dest / "backend/demo_project/settings.py").read_text()
    assert "django.db.backends.sqlite3" in settings
    assert "django.db.backends.postgresql" not in settings

    compose = (dest / "docker-compose.yml").read_text()
    assert "postgres" not in compose.lower()
    assert "DB_HOST" not in compose
    assert 'DEBUG: "False"' in compose

    requirements = (dest / "requirements.txt").read_text()
    assert "psycopg2-binary" not in requirements

    env_example = (dest / ".env.example").read_text()
    assert "POSTGRES_" not in env_example

    readme = (dest / "README.md").read_text()
    assert "POSTGRES_PASSWORD" not in readme
    assert "DB_HOST=localhost" not in readme


@requires_copier
def test_env_example_enables_debug_for_local(copier_copy):
    dest = copier_copy(BASE_DATA)
    env_example = (dest / ".env.example").read_text()
    assert "DEBUG=True" in env_example


@requires_copier
def test_env_example_does_not_leak_a_password(copier_copy):
    dest = copier_copy(BASE_DATA)
    env_example = (dest / ".env.example").read_text()
    assert "POSTGRES_PASSWORD=change-me" in env_example
    assert "POSTGRES_PASSWORD=password" not in env_example
    assert "SuperSecret" not in env_example


@requires_copier
def test_gitattributes_keeps_line_endings_stable(copier_copy):
    dest = copier_copy(BASE_DATA)
    attributes = (dest / ".gitattributes").read_text()
    assert "eol=lf" in attributes


@requires_copier
def test_answers_file_uses_absolute_src_path(copier_copy):
    yaml = pytest.importorskip("yaml")
    dest = copier_copy(BASE_DATA)

    answers = yaml.safe_load((dest / ".copier-answers.yml").read_text())
    assert Path(answers["_src_path"]).is_absolute()
    assert answers["_src_path"] != "."
    assert "postgres_password" not in answers


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
@requires_copier
def test_init_git_creates_main_branch(copier_copy, monkeypatch):
    for variable in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.setenv(variable, "Copier Test")

    dest = copier_copy({**BASE_DATA, "project_slug": "git-test", "init_git": True})
    result = subprocess.run(
        ["git", "-C", str(dest), "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "main"

    hooks_path = subprocess.run(
        ["git", "-C", str(dest), "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert hooks_path.returncode == 0, hooks_path.stderr
    assert hooks_path.stdout.strip() == ".githooks"

    hook = dest / ".githooks/pre-push"
    assert hook.is_file()
    assert "docker compose" in hook.read_text()
    assert "pre-commit" in hook.read_text()

    # The hook must be executable after cloning on Linux/macOS.
    mode = subprocess.run(
        ["git", "-C", str(dest), "ls-files", "-s", ".githooks/pre-push"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert mode.stdout.startswith("100755 "), mode.stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
@requires_copier
def test_gitattributes_keeps_lf_after_clone(copier_copy, tmp_path, monkeypatch):
    for variable in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.setenv(variable, "Copier Test")

    dest = copier_copy({**BASE_DATA, "project_slug": "lf-test", "init_git": True})
    clone = tmp_path / "lf-clone"
    subprocess.run(
        ["git", "-c", "core.autocrlf=true", "clone", "-q", str(dest), str(clone)],
        check=True,
    )

    for name in ("entrypoint.sh", ".githooks/pre-push"):
        assert b"\r\n" not in (clone / name).read_bytes(), f"{name} uses CRLF"


@requires_copier
def test_readme_uses_the_configured_port(copier_copy):
    dest = copier_copy({**BASE_DATA, "project_slug": "port-test", "port": 8123})
    readme = (dest / "README.md").read_text()
    assert "http://localhost:8123/admin/" in readme


@requires_copier
def test_no_jinja_leftovers(copier_copy):
    dest = copier_copy(BASE_DATA)

    for path in dest.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="ignore")
            assert "{{" not in text, f"unrendered template in {path}"
            assert "{%" not in text, f"unrendered template in {path}"


@requires_copier
def test_precommit_toggle(copier_copy):
    with_precommit = copier_copy({**BASE_DATA, "project_slug": "with-precommit"})
    assert (with_precommit / ".pre-commit-config.yaml").is_file()
    assert (with_precommit / ".githooks/pre-push").is_file()
    assert "pre-commit" in (with_precommit / "requirements-dev.txt").read_text()

    without = copier_copy(
        {
            **BASE_DATA,
            "project_slug": "without-precommit",
            "include_precommit": False,
        }
    )
    assert not (without / ".pre-commit-config.yaml").exists()
    assert not (without / ".githooks").exists()
    assert "pre-commit" not in (without / "requirements-dev.txt").read_text()


@requires_copier
def test_precommit_hook_runs_in_docker(copier_copy):
    dest = copier_copy(BASE_DATA)
    hook = (dest / ".githooks/pre-push").read_text()

    assert "docker compose" in hook
    assert "--entrypoint pre-commit" in hook
    assert "run --all-files" in hook
    assert "git push --no-verify" in hook
    assert "make" not in hook.lower()


@requires_copier
def test_wsgi_and_settings_paths_are_consistent(copier_copy):
    """The package name must be importable (no hyphens) and paths must match."""
    dest = copier_copy(BASE_DATA)

    settings = (dest / "backend/demo_project/settings.py").read_text()
    wsgi = (dest / "backend/demo_project/wsgi.py").read_text()
    asgi = (dest / "backend/demo_project/asgi.py").read_text()
    manage = (dest / "backend/manage.py").read_text()
    compose = (dest / "docker-compose.yml").read_text()

    module = "backend.demo_project"

    # settings.py points at the right ROOT_URLCONF / WSGI / ASGI modules.
    assert f"{module}.urls" in settings
    assert f"{module}.wsgi.application" in settings
    assert f"{module}.asgi.application" in settings

    # Entrypoints set the same DJANGO_SETTINGS_MODULE.
    for entrypoint in (wsgi, asgi, manage, compose):
        assert f"{module}.settings" in entrypoint

    # The Python package directory must not contain a hyphen.
    assert (dest / "backend/demo_project").is_dir()
    assert not (dest / "backend/demo-project").exists()


@requires_copier
def test_generated_python_compiles(copier_copy):
    """Every rendered .py file must be syntactically valid."""
    dest = copier_copy(BASE_DATA)

    py_files = list((dest / "backend").rglob("*.py"))
    assert py_files, "no Python files rendered"

    for path in py_files:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")


@pytest.mark.parametrize("database", ["postgresql", "sqlite"])
@requires_copier
def test_compose_is_valid_yaml(copier_copy, database):
    yaml = pytest.importorskip("yaml")

    if database == "sqlite":
        data = _sqlite_data(project_slug="compose-sqlite")
    else:
        data = {**BASE_DATA, "database": "postgresql", "project_slug": "compose-postgres"}

    dest = copier_copy(data)
    parsed = yaml.safe_load((dest / "docker-compose.yml").read_text())
    dev_parsed = yaml.safe_load((dest / "compose.dev.yml").read_text())

    assert "services" in parsed
    assert "web" in parsed["services"]
    assert ("db" in parsed["services"]) is (database == "postgresql")
    assert "web" in dev_parsed["services"]
    assert "precommit_cache" in dev_parsed["volumes"]


@pytest.mark.parametrize("database", ["postgresql", "sqlite"])
@requires_copier
def test_docker_dev_workflow(copier_copy, database):
    """The dev overlay must run runserver with dev dependencies and DEBUG."""
    yaml = pytest.importorskip("yaml")

    if database == "sqlite":
        data = _sqlite_data(project_slug="dev-sqlite")
    else:
        data = {**BASE_DATA, "project_slug": "dev-postgres"}
    dest = copier_copy(data)

    dockerfile = (dest / "Dockerfile.dev").read_text()
    assert "requirements-dev.txt" in dockerfile
    assert "runserver" in dockerfile
    assert "USER app" in dockerfile
    assert "git" in dockerfile.split("apt-get install", 1)[1].split("&&", 1)[0]
    assert "safe.directory /app" in dockerfile
    assert "/home/app/.cache/pre-commit" in dockerfile
    assert "chown -R app:app /app /home/app/.cache" in dockerfile

    base = yaml.safe_load((dest / "docker-compose.yml").read_text())
    base_web = base["services"]["web"]
    assert "gunicorn" in " ".join(base_web["command"])
    assert base_web["environment"]["DEBUG"] == "False"

    dev = yaml.safe_load((dest / "compose.dev.yml").read_text())
    dev_web = dev["services"]["web"]
    assert dev_web["build"]["dockerfile"] == "Dockerfile.dev"
    assert dev_web["environment"]["DEBUG"] == "True"
    assert dev_web["environment"]["PRE_COMMIT_HOME"] == "/home/app/.cache/pre-commit"
    assert "runserver" in " ".join(dev_web["command"])
    assert dev_web["restart"] == "no"
    assert ".:/app" in dev_web["volumes"]
    assert "precommit_cache:/home/app/.cache/pre-commit" in dev_web["volumes"]
    assert "precommit_cache" in dev["volumes"]

    assert not (dest / "Makefile").exists()

    readme = (dest / "README.md").read_text()
    assert "compose.dev.yml" in readme
    assert "docker compose" in readme
    assert "--entrypoint pre-commit" in readme
    assert "make dev" not in readme
    assert "Makefile" not in readme


@requires_copier
def test_development_extras_and_ruff(copier_copy):
    """Dev tools must stay out of production and Black must not be duplicated."""
    dest = copier_copy(BASE_DATA)

    runtime_requirements = (dest / "requirements.txt").read_text().lower()
    assert "django-debug-toolbar" not in runtime_requirements
    assert "factory-boy" not in runtime_requirements

    dev_requirements = (dest / "requirements-dev.txt").read_text().lower()
    assert "django-debug-toolbar==8.0.0" in dev_requirements
    assert "factory-boy==3.3.3" in dev_requirements
    assert "black" not in dev_requirements

    settings = (dest / "backend/demo_project/settings.py").read_text()
    assert 'INSTALLED_APPS.append("debug_toolbar")' in settings
    assert 'MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")' in settings
    assert "INTERNAL_IPS" in settings

    urls = (dest / "backend/demo_project/urls.py").read_text()
    assert 'path("__debug__/", include("debug_toolbar.urls"))' in urls

    pyproject = (dest / "pyproject.toml").read_text()
    assert "[tool.black]" not in pyproject
    assert "[tool.ruff.format]" in pyproject

    dockerfile = (dest / "Dockerfile.dev").read_text()
    assert "requirements-dev.txt" in dockerfile
    assert "git" in dockerfile.split("apt-get install", 1)[1].split("&&", 1)[0]

    readme = (dest / "README.md").read_text()
    assert "pre-commit" in readme
    assert "docker compose" in readme
    assert "Makefile" not in readme

    precommit = (dest / ".pre-commit-config.yaml").read_text()
    assert "psf/black" not in precommit
    assert "ruff-check" in precommit
    assert "ruff-format" in precommit
    assert "rev: v0.17.3" in precommit
    assert "rev: v6.0.0" in precommit


@requires_copier
def test_generated_project_is_ruff_clean(copier_copy):
    """The rendered project must pass the same Ruff checks used in Docker."""
    dest = copier_copy(BASE_DATA)

    for args in (["check", "."], ["format", "--check", "."]):
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *args],
            cwd=dest,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_tasks_run_only_on_copy(template_root):
    """`copier update` must not re-run the git init/commit/hook tasks."""
    copier_yml = (template_root / "copier.yml").read_text()
    assert "_copier_operation == 'copy'" in copier_yml
    assert "_copier_operation == 'update'" in copier_yml
    assert "core.hooksPath" in copier_yml
    assert ".githooks/pre-push" in copier_yml


def test_no_postgres_password_question(template_root):
    """The password is not a Copier answer, so it cannot leak into the answers file."""
    copier_yml = (template_root / "copier.yml").read_text()
    assert "postgres_password:" not in copier_yml


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
@requires_copier
def test_copier_update_does_not_rerun_copy_tasks(tmp_path, monkeypatch):
    """`copier update` applies template changes without a second initial commit."""
    from copier import run_copy, run_update

    for variable in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.setenv(variable, "Copier Test")

    # A clean template repo is required: Copier records a fake `_commit` when
    # the source has uncommitted changes, and `copier update` cannot resolve it.
    template_repo = tmp_path / "template-repo"
    template_repo.mkdir()
    shutil.copy2(TEMPLATE_ROOT / "copier.yml", template_repo / "copier.yml")
    shutil.copy2(TEMPLATE_ROOT / ".gitattributes", template_repo / ".gitattributes")
    shutil.copytree(TEMPLATE_ROOT / "template", template_repo / "template")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=template_repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=template_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "template"], cwd=template_repo, check=True)

    dest = tmp_path / "update-test"
    run_copy(
        str(template_repo),
        str(dest),
        data={
            **BASE_DATA,
            "project_slug": "update-test",
            "init_git": True,
        },
        defaults=True,
        unsafe=True,
        quiet=True,
    )

    def git_log() -> str:
        return subprocess.run(
            ["git", "-C", str(dest), "log", "--oneline"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    before = git_log()
    assert len(before.splitlines()) == 1

    readme = template_repo / "template" / "README.md.jinja"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nUpdate marker\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=template_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "update readme"], cwd=template_repo, check=True)

    run_update(str(dest), defaults=True, unsafe=True, quiet=True, overwrite=True)

    assert "Update marker" in (dest / "README.md").read_text(encoding="utf-8")
    assert git_log() == before

    branch = subprocess.run(
        ["git", "-C", str(dest), "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert branch == "main"
