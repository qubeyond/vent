# Vent

Бесструктурный дамп мыслей: написал — забыл. LLM сама раскладывает записи по
темам и тегам; облако тем и статистика (топ слов, повторяющиеся цитаты) дают
рефлексию задним числом.

Хостинг: [ventout.ru](https://ventout.ru)

История версий — [docs/CHANGELOG.md](docs/CHANGELOG.md). План/бэклог —
[docs/PLAN.md](docs/PLAN.md).

## Как запустить

- Скачать конкретный релиз (`git clone --branch vX.Y.Z ...`) или
  склонировать репозиторий целиком.
- Домен должен уже указывать на сервер (A-запись) — Caddy сам получит
  сертификат Let's Encrypt при первом запуске.

```bash
git clone <repo-url> braindump && cd braindump
cp .env.prod.example .env.prod  # заполнить все поля

scripts/run.sh prod  # первый запуск попросит отредактировать .env.prod

scripts/migrate.sh prod --apply  # накатить схему БД
scripts/create_user.sh prod <username>
```

- Сервис поднимется на `https://<DOMAIN>`. Регистрации нет — только
  пользователи, заведённые вручную через `create_user.sh`.
- `scripts/run.sh prod` держит терминал занятым.
- Обновление после `git pull`: `scripts/migrate.sh prod` (проверка) ->
  `scripts/migrate.sh prod --apply` (если отстала) -> `scripts/run.sh prod`.

## Для разработки

Нужен только Docker.

```bash
cp .env.dev.example .env.dev  # заполнить ROUTERAI_API_KEY
scripts/run.sh dev  # соберёт, проверит миграции, поднимет стек
scripts/create_user.sh dev <username>  # в отдельном терминале, пока run.sh работает
```

- Фронтенд: http://localhost:5173 (Vite, hot reload)
- Backend/Swagger: http://localhost:8000/docs
- Postgres: `localhost:5432` (проброшен только на `127.0.0.1`)
- `frontend/src/shared/api/schema.ts` генерируется из бэкенда
  (`scripts/generate_types.sh dev`).

## Архитектура

- Бэкенд слоями: `domain` (сущности/интерфейсы) -> `infra` (Postgres-репозитории, HTTP-клиент RouterAI) ->
  `services` (use-cases) -> `api` (роутеры,
  composition root в `api/deps.py`).
- LLM-провайдер — [RouterAI](https://routerai.ru/docs/guides),
  OpenAI-совместимый роутер поверх множества моделей; вызовы с ретраями на
  транспортных ошибках.
- Теги раскладываются по 9 фиксированным категориям («Колесо баланса»),
  цвет/категория тега фиксируются при первом создании и не дрейфуют при
  переиспользовании.
- Caddy в проде — единственная точка входа (80/443), терминирует HTTPS,
  раздаёт фронтенд и проксирует `/api/*`; backend и Postgres наружу не
  торчат.

## Стек

FastAPI, SQLAlchemy 2.0 (async) + Alembic, Postgres + pgvector, argon2 +
JWT, React 19 + Vite + TypeScript, d3 (tag/word cloud), Docker Compose,
Caddy.

## Скрипты

- `scripts/run.sh <dev|prod> [--clear]` — поднять стек; `--clear` пошагово
  чистит контейнеры/тома/сеть/образы
- `scripts/migrate.sh <dev|prod> [--apply]` — проверить/накатить миграции
- `scripts/create_user.sh <dev|prod> <username>` — завести пользователя
- `scripts/generate_types.sh <dev|prod>` — перегенерировать типы фронтенда

## Тесты

Backend: 54 теста (`cd backend && uv run pytest`) — 18 юнит (без БД:
хэширование паролей/JWT, парсинг ответов LLM) + 36 интеграционных (реальный
Postgres, отдельная база `braindump_test`, каждый тест в своём rollback).
Линт: `uv run ruff check .`.
