#!/bin/bash

# AUPAT Docker Compose Startup Script
# Starts all services with pre-flight checks

set -e

echo "========================================="
echo "AUPAT v0.1.2 - Docker Startup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    echo "Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    echo "Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please review and customize .env file if needed"
fi

# Check disk space (warn if < 10GB free)
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    echo "WARNING: Less than 10GB free disk space"
    echo "Available: ${AVAILABLE_SPACE}GB"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create required directories
echo "Creating required directories..."
mkdir -p data/immich data/immich-postgres data/archivebox data/backups data/ingest data/archive data/ml-cache logs

# Check if user.json exists
if [ ! -f user/user.json ]; then
    echo "WARNING: user/user.json not found"
    echo "Run setup.sh first or manually create user/user.json"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Starting Docker Compose services..."
echo ""

# Use docker compose (V2) or docker-compose (V1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Pull latest images
echo "Pulling latest Docker images..."
$DOCKER_COMPOSE pull

# Build AUPAT Core
echo "Building AUPAT Core..."
$DOCKER_COMPOSE build aupat-core

# Start all services
echo "Starting all services..."
$DOCKER_COMPOSE up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
echo "(This may take 1-2 minutes on first start)"
echo ""

sleep 10

# Check service status
echo "Service Status:"
echo "---------------"
$DOCKER_COMPOSE ps

echo ""
echo "========================================="
echo "AUPAT Services Started Successfully"
echo "========================================="
echo ""
echo "Access points:"
echo "  AUPAT Core:    http://localhost:5000"
echo "  Immich:        http://localhost:2283"
echo "  ArchiveBox:    http://localhost:8001"
echo ""
echo "View logs:       $DOCKER_COMPOSE logs -f"
echo "Stop services:   $DOCKER_COMPOSE down"
echo "Restart:         $DOCKER_COMPOSE restart"
echo ""
echo "Run database migrations next:"
echo "  docker exec aupat-core python scripts/db_migrate.py"
echo ""
