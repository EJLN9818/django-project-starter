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
- **Non-root container** with a fixed UID/GID.
- **Static files served by WhiteNoise** (no extra nginx needed).
- **Environment management**: `.env.example` + `.gitignore` (kept in sync via
  `copier update`).
- **Code quality**: `ruff`, `black`, `pre-commit` and `.editorconfig`.
- **Tests**: `pytest` wiring in `pyproject.toml`.
- **Git initialization** with an initial commit.

## Requirements

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9+ (`pip install copier`)

## Usage (Local)

Clone this repository once, then generate as many projects as you need:

```bash
git clone <this-repo-url> django-project-starter
cd django-project-starter
pip install copier
```

### Generate a new project (interactive)

```bash
copier copy . ../my-new-project
```

Copier will prompt for the project name, slug, port, database and versions.

### Generate a new project (non-interactive, great for CI/scripts)

```bash
copier copy --defaults --trust \
  -d "project_name=My Project" \
  -d "project_slug=my-project" \
  -d "port=8000" \
  -d "database=postgresql" \
  . ../my-new-project
```

Run `copier copy --help` for all available options.

## Generated project structure

```
my-project/
├── backend/                    # Django project (settings use env vars)
├── data/                       # SQLite database files
├── docs/
├── static/                     # Collected static files
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── pyproject.toml              # ruff / black / pytest config
├── .pre-commit-config.yaml
├── .editorconfig
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Updating a generated project

When you improve this template, pull the changes into an existing project:

```bash
cd my-project
copier update
```

Copier shows a diff for each changed file. Accept, reject, or edit each hunk,
then commit the changes.

### Answer file

A `.copier-answers.yml` file is committed to your project. It stores the answers
you gave during generation (except secrets). **Do not delete it** — `copier
update` needs it to compute the diff correctly.

### Secrets

Secret answers (like `postgres_password`) are **not** stored in the answers
file. Copy `.env.example` to `.env` and fill in the values before running.

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
make generate DEST=../my-project   # generate a project
```

Without make:

```bash
pytest
ruff check --fix .
black .
```

The test suite renders the template into a temporary directory and asserts on
the resulting files for both database backends. It also verifies that every
rendered Python file compiles and that both `docker-compose.yml` variants are
valid YAML.
