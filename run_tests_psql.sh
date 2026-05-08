#!/bin/sh
set -e

CONTAINER_NAME="pyrrha-postgres"
DB_USER="pyrrha"
DB_PASS="pyrrha"
DB_NAME="data-test"
DB_PORT="5432"

export TEST_DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASS}@localhost:${DB_PORT}/${DB_NAME}"
export TEST_DBMS="postgresql"

# --- Docker setup ---

if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
    echo "Container '${CONTAINER_NAME}' is already running."
elif docker ps -aq --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
    echo "Starting existing container '${CONTAINER_NAME}'..."
    docker start "${CONTAINER_NAME}"
else
    echo "Creating and starting PostgreSQL container '${CONTAINER_NAME}'..."
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -e POSTGRES_USER="${DB_USER}" \
        -e POSTGRES_PASSWORD="${DB_PASS}" \
        -e POSTGRES_DB="${DB_NAME}" \
        -p "${DB_PORT}:5432" \
        postgres:16-alpine
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" -q; do
    sleep 1
done
echo "PostgreSQL is ready."

# --- Run tests ---

python -m pytest "$@"
