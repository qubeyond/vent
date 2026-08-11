.PHONY: dev prod migrate-dev migrate-prod migrate-dev-apply migrate-prod-apply \
	test lint types user-dev user-prod deploy-prod

dev:
	scripts/run.sh dev

prod:
	scripts/run.sh prod

migrate-dev:
	scripts/migrate.sh dev

migrate-prod:
	scripts/migrate.sh prod

migrate-dev-apply:
	scripts/migrate.sh dev --apply

migrate-prod-apply:
	scripts/migrate.sh prod --apply

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

types:
	scripts/generate_types.sh dev

user-dev:
	scripts/create_user.sh dev $(username)

user-prod:
	scripts/create_user.sh prod $(username)

deploy-prod: migrate-prod-apply
	docker compose -p braindump-prod -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build
