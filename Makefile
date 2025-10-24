.PHONY: help prereqs build server up shell logs down restart rebuild ps clean

# Detect Compose command (Docker v2 preferred)
COMPOSE := $(shell if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# Default service used by logs/restart
SVC ?= mcp-server

.DEFAULT_GOAL := help

help:
	@echo "Docker Compose Quickstart (Makefile)"
	@echo ""
	@echo "Targets:"
	@echo "  make build      - Build images"
	@echo "  make server     - Start MCP server (foreground)"
	@echo "  make up         - Start MCP server (detached)"
	@echo "  make shell      - Open dev shell (interactive)"
	@echo "  make logs       - Tail logs (default: mcp-server) [SVC=name]"
	@echo "  make down       - Stop and remove containers"
	@echo "  make restart    - Restart a service (default: mcp-server) [SVC=name]"
	@echo "  make rebuild    - Rebuild images and restart server"
	@echo "  make ps         - Show container status"
	@echo "  make clean      - Down + remove volumes (data loss)"
	@echo ""
	@echo "Tips:"
	@echo "  - Put your OpenRouter key in client/fastagent.secrets.yaml or set OPENROUTER_API_KEY in .env"
	@echo "  - If brave/perplexity are enabled in client/fastagent.config.yaml, set BRAVE_API_KEY and PERPLEXITY_API_KEY"
	@echo "  - Mounted volumes reflect code edits immediately inside containers"

prereqs:
	@if [ ! -f .env ]; then \
	  echo "Warning: Missing .env at repo root (email creds, etc.). See .env.example."; \
	fi
	@if [ ! -f client/fastagent.secrets.yaml ]; then \
	  echo "Warning: Missing client/fastagent.secrets.yaml (OpenRouter key, etc.). Copy client/fastagent.secrets.yaml.example and fill values."; \
	fi

build: prereqs
	$(COMPOSE) build

server: prereqs
	@echo "Starting MCP server on http://localhost:8080/mcp (foreground)"
	$(COMPOSE) up mcp-server

up: prereqs
	@echo "Starting MCP server on http://localhost:8080/mcp (detached)"
	$(COMPOSE) up -d mcp-server

shell: prereqs
	@echo "Opening dev shell (bash)"
	$(COMPOSE) run --rm dev-shell

logs:
	$(COMPOSE) logs -f $(SVC)

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) stop $(SVC) || true
	$(COMPOSE) up -d $(SVC)

rebuild: prereqs
	$(COMPOSE) build
	$(COMPOSE) up -d mcp-server

ps:
	$(COMPOSE) ps

clean:
	@echo "Down + removing volumes (persistent data will be removed)!"
	$(COMPOSE) down -v
