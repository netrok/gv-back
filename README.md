# GV Back — RH Monolito Modular (Django + PostgreSQL)

## Requisitos
- Python 3.14 (o 3.13 si falta algún wheel)
- Docker Desktop (para Postgres/Redis)
- VS Code

## Primer arranque (Windows)
1. Copia `.env.example` a `.env` y ajusta si hace falta.
2. `.\scripts\win\setup.ps1`
3. `.\scripts\win\run.ps1`
4. Swagger: http://127.0.0.1:8000/api/docs/

## Primer arranque (mac/linux)
```bash
cp .env.example .env
./scripts/nix/setup.sh
./scripts/nix/run.sh
