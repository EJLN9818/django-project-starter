"""End-to-end tests: render the template and assert on the output tree."""

from __future__ import annotations

from conftest import requires_copier

BASE_DATA = {
    "project_name": "Demo Project",
    "project_slug": "demo-project",
    "port": 8000,
    "database": "postgresql",
    "postgres_db": "demo_project",
    "postgres_user": "demo_project",
    "postgres_password": "secret",
    "django_version": "5.1.5",
    "python_version": "3.11",
    "include_precommit": True,
    "init_git": False,
}

COMMON_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "entrypoint.sh",
    "requirements.txt",
    "pyproject.toml",
    ".editorconfig",
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
]


@requires_copier
def test_common_structure(copier_copy):
    dest = copier_copy(BASE_DATA)

    for relative in COMMON_FILES:
        assert (dest / relative).is_file(), f"missing {relative}"

    # Empty helper directories exist.
    for directory in ("docs", "data", "static"):
        assert (dest / directory).is_dir(), f"missing {directory}/"


@requires_copier
def test_postgresql_configuration(copier_copy):
    dest = copier_copy(BASE_DATA)

    settings = (dest / "backend/demo_project/settings.py").read_text()
    assert "django.db.backends.postgresql" in settings
    assert "environ.Env" in settings

    compose = (dest / "docker-compose.yml").read_text()
    assert "postgres:16-alpine" in compose
    assert "healthcheck" in compose

    requirements = (dest / "requirements.txt").read_text()
    assert "psycopg2-binary" in requirements

    env_example = (dest / ".env.example").read_text()
    assert "POSTGRES_DB=demo_project" in env_example


@requires_copier
def test_sqlite_configuration(copier_copy):
    data = {**BASE_DATA, "database": "sqlite"}
    # Drop postgres-only answers so Copier does not warn about unused ones.
    for key in ("postgres_db", "postgres_user", "postgres_password"):
        data.pop(key)

    dest = copier_copy(data)

    settings = (dest / "backend/demo_project/settings.py").read_text()
    assert "django.db.backends.sqlite3" in settings
    assert "django.db.backends.postgresql" not in settings

    compose = (dest / "docker-compose.yml").read_text()
    assert "postgres" not in compose.lower()

    requirements = (dest / "requirements.txt").read_text()
    assert "psycopg2-binary" not in requirements


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

    without = copier_copy(
        {
            **BASE_DATA,
            "project_slug": "without-precommit",
            "include_precommit": False,
        }
    )
    assert not (without / ".pre-commit-config.yaml").exists()


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
