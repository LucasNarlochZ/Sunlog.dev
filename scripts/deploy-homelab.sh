#!/bin/bash
set -euo pipefail
cd "${DEPLOY_PATH:?DEPLOY_PATH is required}"
exec 9>.deploy.lock
flock -n 9
compose=(docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.prod.yml -f infra/docker-compose.homelab.yml -f infra/docker-compose.homelab-images.yml)
"${compose[@]}" config --quiet
/snap/bin/aws ecr get-login-password --region "${AWS_REGION:-us-east-1}" | docker login --username AWS --password-stdin "${ECR_REGISTRY:-242201312839.dkr.ecr.us-east-1.amazonaws.com}"
"${compose[@]}" pull
"${compose[@]}" up -d --wait postgres redis rabbitmq
"${compose[@]}" run --rm --no-deps -v "$PWD/backend/migrations:/app/migrations:ro" -v "$PWD/infra/migration.config.cjs:/app/migration.config.cjs:ro" api npx --no-install sequelize-cli db:migrate --config /app/migration.config.cjs --env production
"${compose[@]}" up -d --wait
"${compose[@]}" exec -T nginx wget -q -O /dev/null http://127.0.0.1/
"${compose[@]}" exec -T nginx wget -q -O /dev/null http://127.0.0.1/api
