# Django Project Starter

A [Copier](https://copier.readthedocs.io/) template that scaffolds production-ready
Django projects with Docker, environment-based configuration and code-quality
tooling baked in.

## Why Copier?

Unlike a one-shot shell script, Copier keeps the template and the generated
project linked. When this template evolves you can pull the changes into an
existing project with:

```bash
cd my-project
copier update
```

## Features

- **Django 5.1** with `django-extensions` and `django-environ`.
- **PostgreSQL or SQLite**, selected interactively.
- **Docker ready**: multi-stage-friendly `Dockerfile`, `docker-compose.yml` with
  a PostgreSQL healthcheck, `entrypoint.sh` and `.dockerignore`.
- **Non-root container** for safer runtime.
- **Environment management**: `.env.example` + `.gitignore` (regenerated and
  kept in sync via `copier update`).
- **Code quality**: `ruff`, `black`, `pre-commit` and `.editorconfig`.
- **Tests**: `pytest` / `pytest-django` wiring in `pyproject.toml`.
- **Git initialization** with an initial commit.

## Requirements

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9+ (`pip install copier`)

## Usage

### Recommended: Copier directly

```bash
pip install copier
copier copy gh:your_username/django-project-starter ./my-project
```

You can also copy from a local checkout:

```bash
copier copy ./django-project-starter ./my-project
```

### Convenience wrapper

The bundled `create_project.py` wraps Copier with a friendlier CLI:

```bash
python create_project.py -o ./my-project
```

Non-interactive generation (great for CI):

```bash
python create_project.py \
  --no-interactive \
  --name "My Project" \
  --port 8000 \
  --database postgresql \
  --output ./my-project
```

Run `python create_project.py --help` for all options.

## Generated project

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
├── pyproject.toml              # ruff / black / pytest
├── .pre-commit-config.yaml
├── .editorconfig
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Updating a generated project

When this template receives improvements, you can pull them into an existing
project:

```bash
cd my-project
copier update
```

Copier will show you a diff for each changed file. You can accept, reject, or
edit each hunk. After resolving conflicts, commit the changes.

### Answer file

A `.copier-answers.yml` file is committed to your project. It stores the
answers you gave during generation (except secrets). **Do not delete it** —
`copier update` needs it to compute the diff correctly.

### Secrets

Secret answers (like `postgres_password`) are **not** stored in the answers
file. If you change the database type to PostgreSQL after an update, run:

```bash
cp .env.example .env   # then fill in the secrets
```

## Development of the template itself

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

```bash
# Run the tests
pytest

# Lint and format
ruff check --fix .
ruff format .
black .
```

The test suite renders the template into a temporary directory and asserts on
the resulting files for both database backends.

## Contributions

Contributions are welcome! If you have suggestions or find a bug, please open an
issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.
