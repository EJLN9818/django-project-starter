# Django Project Starter

A [Copier](https://copier.readthedocs.io/) template that scaffolds Django
projects with Docker, environment-based configuration and code-quality tooling
baked in.

**This template is for local/team use.** Clone the repo once and generate as many
projects as you need from your local copy — nothing is published to PyPI or
GitHub.

## Features

- **Django 5.2 LTS** with `django-extensions` and `django-environ`.
- **PostgreSQL or SQLite**, selected interactively.
- **Docker ready**: `Dockerfile`, `docker-compose.yml` with a PostgreSQL
  healthcheck, `entrypoint.sh` and `.dockerignore`.
- **Docker-only development**: `Dockerfile.dev` + `compose.dev.yml` with
  `runserver`, dev dependencies and bind-mounted source. No local Python
  installation is required.
- **Non-root container** with a fixed UID/GID.
- **Static files served by WhiteNoise** (no extra nginx needed).
- **Strong `SECRET_KEY` guard** when `DEBUG=False`.
- **Line endings normalized** with `.gitattributes` (safe on Windows clones).
- **Environment management**: `.env.example` + `.gitignore` (kept in sync via
  `copier update`). Secrets are never written to committed files.
- **Code quality**: `ruff`, `black`, `pre-commit` and `.editorconfig`.
- **Tests**: `pytest` wiring in `pyproject.toml`.
- **Git initialization** with an initial commit.

## Requirements

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9.19+ (`pip install "copier>=9.19.1"`)

## Usage (Local)

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

Copier will prompt for the project name, slug, port, database and versions.

### Generate a new project (non-interactive, great for CI/scripts)

```bash
copier copy --defaults --trust \
  -d "project_name=My Project" \
  -d "project_slug=my-project" \
  -d "port=8000" \
  -d "database=postgresql" \
  "<absolute-path-to-template>" ../my-new-project
```

Run `copier copy --help` for all available options.

## Generated project structure

```
my-project/
├── backend/                    # Django project (settings use env vars)
├── data/                       # SQLite database files
├── docs/
├── static/                     # Collected static files
├── Dockerfile                  # Production-like image (Gunicorn)
├── Dockerfile.dev              # Docker-only development image (runserver)
├── docker-compose.yml
├── compose.dev.yml             # Development overlay
├── entrypoint.sh
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── pyproject.toml              # ruff / black / pytest config
├── .pre-commit-config.yaml     # optional (include_precommit)
├── .editorconfig
├── .gitattributes
├── .env.example
├── .dockerignore
├── .gitignore
├── .copier-answers.yml
└── README.md
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
yourself. The generated project's git initialization task runs only on
`copier copy`, never on `copier update`.

### Answer file

A `.copier-answers.yml` file is committed to your project. It stores the answers
you gave during generation, including the absolute `_src_path` of the template.
**Do not delete it** — `copier update` needs it to compute the diff correctly.
If you move the template repository, update `_src_path` in the answers file or
use a git URL as the template source.

### Releases

Tag stable versions of the template (for example
`git tag v1.1.0 && git push --tags`) so `copier update` uses a deterministic
version instead of the current `HEAD`.

### Secrets

The template never writes a database password into a committed file.
`.env.example` contains placeholders; copy it to `.env` (gitignored) and set a
random `SECRET_KEY` (at least 50 characters), plus `POSTGRES_PASSWORD` and
`ALLOWED_HOSTS`, before running.

If you generated a project before this change and committed a real
`POSTGRES_PASSWORD` in `.env.example`, rotate that password and remove it from
git history. `copier update` will replace the file with placeholder values, but
it cannot rewrite existing commits.

## Development of the template itself

```bash
cd django-project-starter
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

Common tasks (GNU make; on Windows use Git Bash or WSL):

```bash
make test        # run the template test suite
make lint        # ruff + black check
make fmt         # auto-fix
make generate DEST=../my-project   # generate a project (absolute path internally)
```

Without make:

```bash
pytest
ruff check --fix .
black .
```

The test suite renders the template into a temporary directory and asserts on
the resulting files for both database backends. It also verifies that every
rendered Python file compiles and that `docker-compose.yml` and
`compose.dev.yml` are valid YAML for both database backends.
