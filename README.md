# Vent

Бесструктурный дамп мыслей: написал — забыл. LLM сама раскладывает записи по
темам и тегам; облако тем и статистика (топ слов, повторяющиеся цитаты) дают
рефлексию задним числом.

- Хостинг: [ventout.ru](https://ventout.ru)
- История версий — [docs/CHANGELOG.md](docs/CHANGELOG.md)
- План/бэклог — [docs/PLAN.md](docs/PLAN.md)

## Как запустить (прод)

- Домен уже указывает на сервер (A-запись) — Caddy сам получит сертификат
  Let's Encrypt при первом запуске.
- Регистрации нет — только пользователи, заведённые вручную.
- `make prod` держит терминал занятым.

```bash
git clone --branch vX.Y.Z <repo-url> braindump && cd braindump
cp .env.prod.example .env.prod   # заполнить все поля

make prod                        # первый запуск попросит отредактировать .env.prod
make migrate-prod-apply          # накатить схему БД
make user-prod username=<name>
```

- Обновление после `git pull`: `make migrate-prod` (проверка) ->
  `make migrate-prod-apply` (если отстала) -> `make prod`.

## Для разработки

- Нужен только Docker.
- Фронтенд: http://localhost:5173 (Vite, hot reload)
- Backend/Swagger: http://localhost:8000/docs
- Postgres: `localhost:5432` (проброшен только на `127.0.0.1`)
- `frontend/src/shared/api/schema.ts` генерируется из бэкенда (`make types`)

```bash
cp .env.dev.example .env.dev   # заполнить ROUTERAI_API_KEY
make dev                       # соберёт, проверит миграции, поднимет стек
make user-dev username=<name>  # в отдельном терминале, пока make dev работает
```

## Таргеты Makefile

- `make dev` / `make prod` — поднять стек
- `make migrate-dev` / `make migrate-prod` — проверить миграции
- `make migrate-dev-apply` / `make migrate-prod-apply` — накатить миграции
- `make user-dev username=<name>` / `make user-prod username=<name>` — завести пользователя
- `make types` — перегенерировать типы фронтенда из OpenAPI-схемы бэкенда
- `make test` — прогнать backend-тесты
- `make lint` — ruff
- `make deploy-prod` — миграция + пересборка и рестарт прод-контейнеров (используется в CI)

## Архитектура

- Бэкенд слоями: `domain` (сущности/интерфейсы) -> `infra` (Postgres-репозитории, HTTP-клиент RouterAI) -> `services` (use-cases) -> `api` (роутеры, composition root в `api/deps.py`)
- LLM-провайдер — [RouterAI](https://routerai.ru/docs/guides), OpenAI-совместимый роутер поверх множества моделей; вызовы с ретраями на транспортных ошибках
- Теги раскладываются по 9 фиксированным категориям («Колесо баланса»), цвет/категория тега фиксируются при первом создании и не дрейфуют при переиспользовании
- Тегирование и правка текста — асинхронные фоновые задачи; статус записи (`processing`/`ready`) и этап обработки опрашиваются с фронта
- Caddy в проде — единственная точка входа (80/443), терминирует HTTPS, раздаёт фронтенд и проксирует `/api/*`; backend и Postgres наружу не торчат

## Стек

- Backend: FastAPI, SQLAlchemy 2.0 (async) + Alembic, argon2 + JWT
- БД: Postgres + pgvector
- Frontend: React 19 + Vite + TypeScript, d3 (tag/word cloud)
- Инфра: Docker Compose, Caddy, GitHub Actions (CI + ручной деплой)

## Тесты

- Backend: 64 теста (`make test`) — 20 юнит + 44 интеграционных
- Линт: `make lint`
