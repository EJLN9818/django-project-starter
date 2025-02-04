#!/usr/bin/env python3
import os
import subprocess
import re

# Constantes
DEFAULT_PORT = "8000"
DEFAULT_DB_PASSWORD = "password"
DEFAULT_DB_CHOICE = "1"

def prompt_project_details():
    """Prompts the user for project details and returns a dictionary with the input values."""
    project_name = input("Ingrese el nombre del proyecto: ").strip()
    if not project_name:
        print("El nombre del proyecto es obligatorio.")
        exit(1)
    
    slug = input("Ingrese el slug del proyecto (dejar en blanco para generar a partir del nombre): ").strip()
    if not slug:
        slug = project_name.lower().replace(" ", "-")
    
    port = input(f"Ingrese el puerto de exposición (default {DEFAULT_PORT}): ").strip() or DEFAULT_PORT
    
    print("Seleccione el tipo de base de datos:")
    print("1) PostgreSQL")
    print("2) SQLite")
    db_choice = input(f"Opción (default {DEFAULT_DB_CHOICE}): ").strip() or DEFAULT_DB_CHOICE
    
    if db_choice == "1":
        db_type = "postgresql"
        db_name = input(f"Ingrese el nombre de la base de datos (default: {slug}): ").strip() or slug
        db_user = input(f"Ingrese el usuario de la base de datos (default: {slug}): ").strip() or slug
        db_password = input(f"Ingrese la contraseña de la base de datos (default: {DEFAULT_DB_PASSWORD}): ").strip() or DEFAULT_DB_PASSWORD
    else:
        db_type = "sqlite"
        db_name = ""
        db_user = ""
        db_password = ""
    
    return {
        "project_name": project_name,
        "slug": slug,
        "port": port,
        "db_type": db_type,
        "db_name": db_name,
        "db_user": db_user,
        "db_password": db_password,
        "requirements": [
            "Django==5.1.5",
            "asgiref==3.8.1",
            "sqlparse==0.5.3",
            "pytz==2025.1",
            "django-extensions==3.2.3",
            "psycopg2-binary==2.9.9",
            "jsonschema==4.23.0",
            "requests==2.32.3",
            "pytest==8.3.4",
            "pytest-django==4.9.0",
            "gunicorn==21.2.0",
        ]
    }

def create_folder_structure(config):
    """Creates the project folder structure based on the provided configuration."""
    project_folder = config["slug"]
    os.makedirs(project_folder, exist_ok=True)
    os.makedirs(os.path.join(project_folder, "backend"), exist_ok=True)
    os.makedirs(os.path.join(project_folder, "docs"), exist_ok=True)
    os.makedirs(os.path.join(project_folder, "data"), exist_ok=True)
    return project_folder

def create_requirements_txt(config, folder):
    """Creates the requirements.txt file with the specified dependencies."""
    requirements_path = os.path.join(folder, "requirements.txt")
    with open(requirements_path, "w") as f:
        f.write("\n".join(config["requirements"]))
    print(f"Archivo requirements.txt creado en {requirements_path}")

def create_docker_compose(config, folder):
    """Creates the docker-compose.yml file based on the database type."""
    if config["db_type"] == "postgresql":
        content = f"""
version: "3.8"

services:
  web:
    build: .
    command: bash -c "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn {config['slug']}.wsgi:application --bind 0.0.0.0:{config['port']}"
    volumes:
      - ./backend:/app/backend
      - ./static:/app/static
    ports:
      - "{config['port']}:{config['port']}"
    environment:
      - PYTHONUNBUFFERED=1
      - DJANGO_SETTINGS_MODULE={config['slug']}.settings
    depends_on:
      - db
  shell:
    build: .
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE={config['slug']}.settings
    command: ["python", "manage.py", "shell_plus"]

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: {config['db_name']}
      POSTGRES_USER: {config['db_user']}
      POSTGRES_PASSWORD: {config['db_password']}
    volumes:
      - postgres_data:/var/lib/postgresql/data/

volumes:
  postgres_data:
"""
    else:
        content = f"""
version: "3.8"

services:
  web:
    build: .
    command: gunicorn {config['slug']}.wsgi:application --bind 0.0.0.0:{config['port']}
    volumes:
      - .:/app
    ports:
      - "{config['port']}:{config['port']}"
"""
    compose_path = os.path.join(folder, "docker-compose.yml")
    with open(compose_path, "w") as f:
        f.write(content)
    print(f"Archivo docker-compose.yml creado en {compose_path}")

def create_dockerfile(config, folder):
    """Creates the Dockerfile for the project."""
    content = f"""
FROM python:3.11

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo el backend
COPY backend /app/backend

WORKDIR /app/backend

RUN python manage.py collectstatic --noinput

EXPOSE {config['port']}

CMD ["gunicorn", "backend.{config['slug']}.wsgi:application", "--bind", "0.0.0.0:{config['port']}"]
"""
    dockerfile_path = os.path.join(folder, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(content)
    print(f"Archivo Dockerfile creado en {dockerfile_path}")

def create_readme(config, folder):
    """Creates the README.md file with project details."""
    content = f"""
# {config['project_name']}

Este es un proyecto base generado automáticamente.

## Configuración

- **Nombre del Proyecto:** {config['project_name']}
- **Slug:** {config['slug']}
- **Puerto:** {config['port']}
- **Base de Datos:** {config['db_type']}
"""
    readme_path = os.path.join(folder, "README.md")
    with open(readme_path, "w") as f:
        f.write(content)
    print(f"Archivo README.md creado en {readme_path}")

def update_settings_py(config, folder):
    """Updates the settings.py file to include django-extensions and configure the database."""
    settings_path = os.path.join(folder, "backend", config["slug"], "settings.py")
    
    # Verificar si el archivo existe
    if not os.path.exists(settings_path):
        print(f"El archivo {settings_path} no existe.")
        return

    try:
        with open(settings_path, "r") as f:
            settings_content = f.read()
    except IOError as e:
        print(f"Error al leer el archivo {settings_path}: {e}")
        return

    # Verificar si INSTALLED_APPS ya está presente
    if "INSTALLED_APPS" not in settings_content:
        print(f"El archivo {settings_path} no contiene INSTALLED_APPS.")
        return

    # Verificar si django_extensions ya está en INSTALLED_APPS
    if "django_extensions" in settings_content:
        print("django_extensions ya está en INSTALLED_APPS.")
        return

    # Reemplazar el bloque de INSTALLED_APPS
    installed_apps_pattern = re.compile(r"(INSTALLED_APPS = \[.*?\])", re.DOTALL)
    match = installed_apps_pattern.search(settings_content)
    
    if match:
        original_installed_apps = match.group(1)
        
        new_installed_apps = f"""
APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_APPS = [
    'django_extensions',
]

INSTALLED_APPS = APPS + THIRD_APPS
"""
        
        settings_content = settings_content.replace(original_installed_apps, new_installed_apps)
    else:
        print(f"No se encontró el bloque de INSTALLED_APPS en {settings_path}.")
        return

    # Configurar la base de datos
    if config["db_type"] == "postgresql":
        settings_content = settings_content.replace(
            "        'ENGINE': 'django.db.backends.sqlite3',",
            "        'ENGINE': 'django.db.backends.postgresql',"
        )
        
        settings_content = settings_content.replace(
            "        'NAME': BASE_DIR / 'db.sqlite3',",
            f"        'NAME': '{config['db_name']}',\n"        
            f"        'USER': '{config['db_user']}',\n"
            f"        'PASSWORD': '{config['db_password']}',\n"
            "        'HOST': 'db',\n"
            f"        'PORT': 5432"
        )

    # Actualizar WSGI_APPLICATION
    settings_content = settings_content.replace(
        f"WSGI_APPLICATION = '{config['slug']}.wsgi.application'",
        f"WSGI_APPLICATION = 'backend.{config['slug']}.wsgi.application'",
    )
    
    # Actualizar STATIC_ROOT
    settings_content = settings_content.replace(
        "STATIC_URL = 'static/'",
        "STATIC_URL = 'static/'\nSTATIC_ROOT = '/app/static'"
    )

    try:
        with open(settings_path, "w") as f:
            f.write(settings_content)
    except IOError as e:
        print(f"Error al escribir en el archivo {settings_path}: {e}")
        return

    print(f"Archivo settings.py actualizado en {settings_path}")

def update_wsgi_py(config, folder):
    """Updates the wsgi.py file to set the correct DJANGO_SETTINGS_MODULE."""
    wsgi_path = os.path.join(folder, "backend", config["slug"], "wsgi.py")
    with open(wsgi_path, "r") as f:
        wsgi_content = f.read()
    
    wsgi_content = wsgi_content.replace(
        f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{config['slug']}.settings')",
        f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.{config['slug']}.settings')"
    )
    
    with open(wsgi_path, "w") as f:
        f.write(wsgi_content)
    print(f"Archivo wsgi.py actualizado en {wsgi_path}")

def update_asgi_py(config, folder):
    """Updates the asgi.py file to set the correct DJANGO_SETTINGS_MODULE."""
    asgi_path = os.path.join(folder, "backend", config["slug"], "asgi.py")
    with open(asgi_path, "r") as f:
        asgi_content = f.read()
    
    asgi_content = asgi_content.replace(
        f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{config['slug']}.settings')",
        f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.{config['slug']}.settings')"
    )
    
    with open(asgi_path, "w") as f:
        f.write(asgi_content)
    print(f"Archivo asgi.py actualizado en {asgi_path}")

def create_django_project(config, folder):
    """Creates the Django project using django-admin."""
    backend_folder = os.path.join(folder, "backend")
    os.makedirs(backend_folder, exist_ok=True)
    subprocess.run(["django-admin", "startproject", config["slug"], backend_folder])
    print(f"Proyecto Django creado en {backend_folder}")

def main():
    """Main function to orchestrate the project creation process."""
    config = prompt_project_details()
    project_folder = create_folder_structure(config)
    create_django_project(config, project_folder)
    create_requirements_txt(config, project_folder)
    update_settings_py(config, project_folder)
    update_wsgi_py(config, project_folder)
    update_asgi_py(config, project_folder)
    create_docker_compose(config, project_folder)
    create_dockerfile(config, project_folder)
    create_readme(config, project_folder)
    
    print("Proyecto base creado con éxito en la carpeta:", project_folder)

if __name__ == "__main__":
    main()