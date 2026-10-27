# Django Project Starter

A [Copier](https://copier.readthedocs.io/) template that creates Django projects
with Docker, environment-based configuration and code-quality tooling included.

The generated project is **Docker-only for daily work**: no local Python,
virtualenv or database server is required. Docker Compose runs Django,
PostgreSQL/SQLite, pytest, Ruff and pre-commit.

This template is maintained as a local/team repository. It is not published to
PyPI; `origin` is only the source repository.

## Features

- **Django 5.2 LTS** with `django-extensions` and `django-environ`.
- **PostgreSQL or SQLite**, selected interactively.
- **Docker ready**: production-like `Dockerfile` with Gunicorn and a
  development `Dockerfile.dev` with `runserver`, test tools and bind-mounted
  source.
- **Docker Compose overlays**: `docker-compose.yml` for the base stack and
  `compose.dev.yml` for development. No local `make` required.
- **Non-root containers** with a fixed UID/GID.
- **WhiteNoise** serves static files without an extra nginx container.
- **Strong `SECRET_KEY` guard** when `DEBUG=False`.
- **Line endings normalized** with `.gitattributes` (safe on Windows clones).
- **Environment management**: `.env.example` plus `.gitignore`; secrets stay out
  of committed files.
- **Code quality**: Ruff for linting and formatting, pre-commit and
  `.editorconfig`.
- **Pre-commit in Docker**: a tracked `.githooks/pre-push` hook runs the checks
  inside the development container before each push.
- **Tests**: pytest wiring in `pyproject.toml`.
- **Development extras**: `django-debug-toolbar` and `factory_boy`, installed
  only in development.
- **Git initialization** with an initial commit and the Docker pre-push hook
  configured.

## Requirements

To generate or update a project:

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9.19+ (`pip install "copier>=9.19.1"`)

To work on a generated project:

- Docker Desktop, or Docker Engine with Compose v2
- Git

Python is not needed for the generated project's daily workflow.

## Usage (local template)

Clone this repository once, then generate as many projects as you need:

```bash
git clone <this-repo-url> django-project-starter
cd django-project-starter
pip install "copier>=9.19.1"
```

### Generate a new project (interactive)

Use an **absolute path** to the template. Copier stores that path in
`.copier-answers.yml`; with `copier copy . ...` it would store `_src_path: .`
and `copier update` would look for the template inside the generated project.

```bash
# macOS / Linux (from the template repository)
copier copy "$(pwd)" ../my-new-project

# Windows PowerShell (from the template repository)
copier copy (Get-Location).Path ..\my-new-project
```

Copier prompts for the project name, slug, port, database and versions. If Git
initialization and pre-commit are enabled, it also configures
`core.hooksPath=.githooks` so the Docker pre-push hook is active.

### Generate a new project (non-interactive)

```bash
copier copy --defaults --trust \
  -d "project_name=My Project" \
  -d "project_slug=my-project" \
  -d "port=8000" \
  -d "database=postgresql" \
  "<absolute-path-to-template>" ../my-new-project
```

Run `copier copy --help` for all available options.

## Generated project workflow

The generated README has the complete command reference. The short version:

```bash
# First time
cp .env.example .env                # edit SECRET_KEY (and POSTGRES_PASSWORD)
docker compose -f docker-compose.yml -f compose.dev.yml up --build

# Daily
docker compose -f docker-compose.yml -f compose.dev.yml run --rm web pytest
docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps --entrypoint ruff web check .
docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps --entrypoint pre-commit web run --all-files
```

No `make` targets are generated. All commands are Docker Compose commands.

## Generated project structure

```text
my-project/
|-- backend/                    # Django project (settings use env vars)
|-- data/                       # SQLite database files
|-- docs/
|-- static/                     # Collected static files
|-- Dockerfile                  # Production-like image (Gunicorn)
|-- Dockerfile.dev              # Development image (runserver + dev tools)
|-- docker-compose.yml
|-- compose.dev.yml             # Development overlay
|-- entrypoint.sh
|-- requirements.txt
|-- requirements-dev.txt
|-- pyproject.toml              # Ruff / pytest config
|-- .pre-commit-config.yaml     # optional (include_precommit)
|-- .githooks/pre-push          # optional Docker pre-push hook
|-- .editorconfig
|-- .gitattributes
|-- .env.example
|-- .dockerignore
|-- .gitignore
|-- .copier-answers.yml
`-- README.md
```

## Pre-commit inside Docker

The generated development image contains Git and pre-commit. The manual command
is:

```bash
docker compose -f docker-compose.yml -f compose.dev.yml run --rm --no-deps \
  --entrypoint pre-commit web run --all-files --show-diff-on-failure
```

If pre-commit is enabled, the generated project also includes a tracked
`.githooks/pre-push` hook. It calls the same Docker command before every
`git push`. The first run downloads hook environments into a Docker volume;
subsequent runs reuse the cache. There is no need to install pre-commit on the
host.

Existing projects created before this hook was added can enable it with:

```bash
git add .githooks/pre-push
git update-index --chmod=+x .githooks/pre-push
git config core.hooksPath .githooks
```

## Updating a generated project

Commit (and ideally tag) your template changes first. `copier update` uses the
recorded commit/tag, not uncommitted changes. Do not generate a project from a
dirty template: Copier records a temporary tree hash that `copier update`
cannot resolve later. Then, in the generated project:

```bash
cd my-project
copier update
```

Review the resulting diff and resolve any conflicts, then commit the changes
yourself. The generated project's Git initialization and hook configuration
tasks run only on `copier copy`, never on `copier update`.

### Answer file

A `.copier-answers.yml` file is committed to your project. It stores the answers
you gave during generation, including the absolute `_src_path` of the template.
**Do not delete it** - `copier update` needs it to compute the diff correctly.
If you move the template repository, update `_src_path` in the answers file or
use a Git URL as the template source.

### Releases

Tag stable versions of the template (for example
`git tag v1.3.0 && git push origin main --follow-tags`) so `copier update` uses
a deterministic version instead of the current `HEAD`.

### Secrets

The template never writes a database password into a committed file.
`.env.example` contains placeholders; copy it to `.env` (gitignored) and set a
random `SECRET_KEY` (at least 50 characters), plus `POSTGRES_PASSWORD` and
`ALLOWED_HOSTS`, before running.

If you generated a project before this change and committed a real
`POSTGRES_PASSWORD` in `.env.example`, rotate that password and remove it from
Git history. `copier update` will replace the file with placeholder values, but
it cannot rewrite existing commits.

## Development of the template itself

The template repository itself is maintained with Python, Copier and pre-commit.
This is separate from generated projects, which do not need Python on the host.

```bash
cd django-project-starter
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

Common tasks, without a Makefile:

```bash
python -m pytest                # template test suite
ruff check .                    # lint
ruff format --check .           # formatting check
ruff check --fix .              # auto-fix
ruff format .                   # format
copier copy "$(pwd)" ../my-project
```

On Windows PowerShell, use `(Get-Location).Path` for the template path and
`.venv\Scripts\activate` for the virtual environment.

The test suite renders the template into a temporary directory and asserts on
the resulting files for both database backends. It also verifies that every
rendered Python file compiles, that the Compose files are valid YAML, and that
the generated project passes Ruff.

## Intentionally not included

The starter stays small on purpose. Add these only when a project actually needs
them:

- CI/CD pipelines and cloud deployment manifests.
- A custom user model or API layer.
- Celery, Redis, DRF, allauth, CORS or Sentry.

## License

No license is declared. Add one before distributing a generated project.
