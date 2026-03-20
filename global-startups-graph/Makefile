.PHONY: setup ingest dev clean stop

# Start all services, wait for Neo4j, then ingest data
setup:
	docker compose up -d neo4j
	@echo "Waiting for Neo4j to be ready..."
	@sleep 15
	docker compose run --rm backend python ingest.py
	docker compose up -d

# Run ingestion only (assumes Neo4j is already running)
ingest:
	docker compose run --rm backend python ingest.py

# Start all services in dev mode
dev:
	docker compose up

# Stop all services
stop:
	docker compose down

# Wipe Neo4j data and re-ingest
clean:
	docker compose down -v
	docker compose up -d neo4j
	@echo "Waiting for Neo4j..."
	@sleep 15
	docker compose run --rm backend python ingest.py
	docker compose up -d
