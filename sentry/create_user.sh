#!/bin/bash
docker run -it --rm \
    -e SENTRY_DB_USER=sentry \
    -e SENTRY_DB_PASSWORD=sentry \
    -e SENTRY_POSTGRES_HOST=postgres \
    -e SENTRY_REDIS_HOST=redis \
    -e SENTRY_SECRET_KEY='@q@5&^=basz_mn%pq3rso*hw3c(m!walu)z(@gts-^cl0(mvvp' \
    --link sentry_postgres_1:postgres \
    --link sentry_redis_1:redis \
    --network=sentry_default \
    sentry:9.0 upgrade
