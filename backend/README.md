# Backend — Sistema Lavadero

API REST con Django y Django REST Framework, gestionada con [`uv`](https://docs.astral.sh/uv/).

## Requisitos

- Python 3.13 o superior
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL 16 o superior (local o con Docker)

## 1. Base de datos local (PostgreSQL)

El proyecto usa Postgres también en desarrollo y en los tests, porque la regla de no superposición de turnos depende de una restricción propia de Postgres (`ExclusionConstraint`). **No sirve SQLite.**

**Opción A: con Docker** (la más rápida)

```bash
docker run --name lavadero-db -d -p 5432:5432 \
  -e POSTGRES_USER=lavadero -e POSTGRES_PASSWORD=lavadero -e POSTGRES_DB=lavadero \
  postgres:16
```

Para pararla y volver a levantarla: `docker stop lavadero-db` y `docker start lavadero-db`.

**Opción B: Postgres instalado en tu computadora.** Creá el usuario y la base desde `psql`:

```sql
CREATE ROLE lavadero LOGIN PASSWORD 'lavadero' CREATEDB;
CREATE DATABASE lavadero OWNER lavadero;
```

El permiso `CREATEDB` es necesario: `pytest` crea y borra su propia base de prueba (`test_lavadero`) en cada ejecución.

## 2. Variables de entorno

```bash
cd backend
cp .env.example .env
```

Completá el `.env` (este archivo **nunca se sube al repositorio**):

| Variable | Valor para desarrollo local |
|---|---|
| `SECRET_KEY` | Una clave aleatoria. Generala con el comando de abajo |
| `DEBUG` | `True` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` |
| `DATABASE_URL` | `postgres://lavadero:lavadero@localhost:5432/lavadero` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` |

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

En producción las mismas variables se configuran en Render, con `DEBUG=False`.

## 3. Instalar y correr

```bash
uv sync                          # instala las dependencias
uv run python manage.py migrate  # crea las tablas
uv run python manage.py runserver
```

- Health check: <http://localhost:8000/api/health/>
- Documentación interactiva (Swagger): <http://localhost:8000/api/docs/>

## 4. Tests y calidad

```bash
uv run pytest            # todos los tests
uv run pytest -k turno   # solo los que tengan "turno" en el nombre
uv run ruff check .      # linter
```

Los tests de cada app viven en `tests.py` o en archivos `test_*.py` dentro de la app.

## Problemas frecuentes

- **`KeyError: 'SECRET_KEY'`**: falta el archivo `.env`.
- **`The SECRET_KEY setting must not be empty`**: el `.env` existe pero `SECRET_KEY` quedó vacía.
- **`connection refused`**: Postgres no está levantado, o el puerto de `DATABASE_URL` no coincide.
- **`permission denied to create database`** al correr `pytest`: al usuario de Postgres le falta el permiso `CREATEDB`.