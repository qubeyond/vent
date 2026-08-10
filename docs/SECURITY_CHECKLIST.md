# Чек-лист безопасности сервера

Для однопользовательского self-hosted сервиса. Выполнить один раз при поднятии
сервера, часть пунктов — по необходимости позже.

## 0. Получить код

### 0.1 Скачать конкретный релиз (тег)

Релизы — это git-теги вида `vX.Y.Z` на ветке `main`. Скачать код конкретного
релиза, а не последний коммит ветки:

```bash
git clone --branch v0.1.0 --depth 1 <repo-url> braindump
# или если репозиторий уже склонирован:
cd braindump && git fetch --tags && git checkout v0.1.0
```

Посмотреть список доступных тегов: `git tag -l` (локально) или на странице
Releases репозитория, если он на GitHub/GitLab.

Если репозиторий **приватный**, `git clone` по HTTPS без авторизации не
сработает — см. раздел 0.3 (SSH deploy key) ниже. Это касается и `git clone`,
и скачивания zip-архива релиза через браузер (там просто попросит залогиниться).

### 0.2 Быстрый локальный запуск (dev)

Нужен только Docker.

```bash
git clone <repo-url> braindump && cd braindump
cp .env.dev.example .env.dev
```

В `.env.dev` обязательно поменять (иначе бэкенд не стартует или стартует
небезопасно):

- `SECRET_KEY` — обязателен, не короче 32 символов. Сгенерировать:
  `openssl rand -hex 32`. Шаблонное значение из `.env.dev.example` формально
  проходит проверку длины, но для чего-то серьёзнее локальной разработки на
  своей машине — лучше сразу своё.
- `ROUTERAI_API_KEY` — без него тегирование не будет работать (заметки всё
  равно сохранятся, но с тегом-заглушкой «не разобрано»). Получить на
  https://routerai.ru/settings/keys.
- `POSTGRES_PASSWORD` — можно оставить дефолт для чистого dev на своей
  машине, но лучше поменять, если БД проброшена наружу.

Дальше:

```bash
scripts/run.sh dev             # соберёт, проверит миграции, поднимет стек (логи в форграунде)
```

В отдельном терминале, пока `run.sh dev` работает:

```bash
scripts/create_user.sh dev <username>   # завести пользователя — регистрации в приложении нет
```

Открыть http://localhost:5173 (фронтенд, Vite dev server с hot reload).
Backend/Swagger — http://localhost:8000/docs.

Полное описание скриптов и деплоя в прод — в [README.md](README.md).

### 0.3 Приватный репозиторий на VPS — нужен SSH-ключ, регистрация не нужна

Если код лежит в приватном репозитории (GitHub/GitLab), для `git clone`/
`git pull` на VPS нужен один из двух вариантов — регистрироваться отдельно
на VPS нигде не надо, это не облачный сервис, а просто git:

**Вариант А — deploy key (рекомендуется).** Отдельный SSH-ключ, который живёт
только на VPS и даёт **read-only** доступ ровно к одному репозиторию — не
твой личный ключ, компрометация VPS не даёт доступа ко всем твоим репозиториям:

```bash
# На VPS:
ssh-keygen -t ed25519 -C "vent-deploy" -f ~/.ssh/vent_deploy -N ""
cat ~/.ssh/vent_deploy.pub   # скопировать вывод
```

Добавить этот публичный ключ в настройки репозитория — GitHub:
Settings → Deploy keys → Add deploy key (галку Write access не ставить,
нужен только pull). GitLab: Settings → Repository → Deploy keys — аналогично.

```bash
# На VPS — ~/.ssh/config, чтобы git знал, каким ключом стучаться именно в этот репозиторий:
cat >> ~/.ssh/config <<'EOF'
Host github.com-vent
  HostName github.com
  User git
  IdentityFile ~/.ssh/vent_deploy
  IdentitiesOnly yes
EOF

git clone git@github.com-vent:<username>/<repo>.git braindump
```

**Вариант Б — Personal Access Token (проще, но менее изолированно).** В
GitHub/GitLab создать токен с правом только на чтение (`repo` → read-only,
или fine-grained token, ограниченный этим одним репозиторием), затем:

```bash
git clone https://<token>@github.com/<username>/<repo>.git braindump
```

Токен осядет в `.git/config` в открытом виде — если это смущает, вариант А
чище. Токен так же, как SSH-ключ, можно отозвать в любой момент со стороны
GitHub/GitLab, не трогая сервер.

**Вариант В — репозиторий публичный.** Секреты (`SECRET_KEY`,
`ROUTERAI_API_KEY`, пароли БД) никогда не попадают в git — они только в
`.env.dev`/`.env.prod`, которые в `.gitignore`. Поэтому сделать репозиторий
публичным ничего не «сливает» — единственная плата за это в том, что код
(не данные, не секреты) виден всем. Если это ок — самый простой вариант,
`git clone <https-url>` без всякой авторизации.

После первого клона обновления — просто `git pull` (см. «Обновление после
git pull» в README.md).

### 0.4 CI/CD (GitHub Actions)

`.github/workflows/ci.yml` — на каждый push/PR в `main`/`master`: backend
(`ruff check` + `pytest` против реального Postgres в service-контейнере) и
frontend (`tsc --noEmit`, `oxlint`, `vite build`) параллельно, отдельными
джобами. Ничего не деплоит — это гейт «можно мержить/тегать или нет».
Смотреть статус: вкладка Actions в репозитории или бейдж на PR.

`.github/workflows/release.yml` — срабатывает на push тега вида `vX.Y.Z`:

1. Собирает backend- и frontend-образы и пушит их в GitHub Container
   Registry: `ghcr.io/<owner>/<repo>/backend:vX.Y.Z` и `.../frontend:vX.Y.Z`
   (плюс тег `latest`).
2. Создаёт GitHub Release на этом теге с автосгенерированным списком
   изменений (`gh release create --generate-notes`).

Как выпустить релиз:

```bash
git checkout main && git pull   # или master — смотреть по фактическому дефолтному branch
# убедиться, что CI на этом коммите зелёный (вкладка Actions)
git tag -a v0.2.0 -m "краткое описание релиза"
git push origin v0.2.0
```

Дальше `release.yml` сам соберёт образы и создаст релиз — ничего вручную
собирать/пушить не нужно. Если джоба публикации в GHCR падает с
permission denied — в репозитории Settings → Actions → General → Workflow
permissions выставить «Read and write permissions» (по умолчанию иногда
стоит read-only для `GITHUB_TOKEN`).

Образы из GHCR — опциональная альтернатива сборке из исходников на VPS
(быстрее деплой, не нужен build-тулчейн на сервере), но текущий
`docker-compose.prod.yml` по умолчанию продолжает собирать из исходников
(`build: ./backend`, `build: ./frontend`) — это самый простой путь без
настройки авторизации к registry на сервере. Переключение на готовые образы
(`image: ghcr.io/...` вместо `build:`) — по желанию, не обязательно.

## 1. Firewall — открыть только 22/80/443

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (ACME challenge + редирект на HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status verbose
```

Postgres и backend в `docker-compose.prod.yml` **не публикуют** порты наружу —
они доступны только внутри docker-сети между контейнерами. Наружу торчит
только контейнер `web` (Caddy) на 80/443. Убедиться, что это так:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod ps
# в колонке PORTS у db и backend не должно быть 0.0.0.0:...
```

## 2. SSH

- Отключить вход по паролю, оставить только ключи:
  `/etc/ssh/sshd_config` → `PasswordAuthentication no`, затем
  `sudo systemctl restart sshd`.
- По возможности отключить root-логин: `PermitRootLogin no`.
- (Опционально) сменить порт SSH с 22 на нестандартный — не защита сама по
  себе, но режет автоматический шум в логах.

## 3. Fail2ban — бан за перебор

```bash
sudo apt install fail2ban
sudo systemctl enable --now fail2ban
```

Дефолтного jail'а `sshd` достаточно на старте. При желании добавить кастомный
jail на логи Caddy для бана за повторные 401 на `/api/auth/login` — не
обязательно для одного пользователя, но дёшево сделать при наличии желания.

## 4. Обновления

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 5. Секреты

- `.env.prod` — реальные значения `POSTGRES_PASSWORD`, `SECRET_KEY`,
  `ROUTERAI_API_KEY` не должны попасть в git (уже в `.gitignore`) и никуда не
  логируются.
- `SECRET_KEY` генерировать так: `openssl rand -hex 32`.
- Файл `.env.prod` держать с правами `chmod 600`.

## 6. Приложение

- Регистрации нет — единственный способ завести пользователя:
  `scripts/create_user.sh prod <username>` (пароль хешируется bcrypt, не
  хранится в открытом виде).
- Все API-эндпоинты, кроме `/api/auth/login` и `/api/health`, требуют JWT
  (`Authorization: Bearer ...`), токен живёт 14 дней.
- HTTPS обязателен и настроен из коробки (Caddy сам получает сертификат
  Let's Encrypt по домену из `DOMAIN` в `.env.prod`) — не открывать сервис по
  голому HTTP.

## 7. Бэкапы (сделать до того, как появятся данные, которые жалко потерять)

Данные лежат в docker volume `db_data`. Простой бэкап:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod \
  exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > backup-$(date +%F).sql.gz
```

Класть это в cron и хранить копии не только на самом сервере.

## 8. Мониторинг по минимуму

- `docker compose ... logs -f` — смотреть логи вручную первое время.
- `docker compose ... ps` — проверять, что все контейнеры `healthy`/`running`
  после деплоя.
