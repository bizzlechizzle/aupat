"""
Tests for Docker Compose configuration

Tests:
- docker-compose.yml syntax validation
- Service definitions
- Volume mappings
- Network configuration
- Health check definitions
"""

import pytest
import yaml
from pathlib import Path


def test_docker_compose_file_exists():
    """Test that docker-compose.yml exists."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'
    assert compose_file.exists(), "docker-compose.yml not found"


def test_docker_compose_valid_yaml():
    """Test that docker-compose.yml is valid YAML."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax: {e}")

    assert config is not None
    assert 'services' in config


def test_required_services_defined():
    """Test that all required services are defined."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    required_services = [
        'aupat-core',
        'immich-server',
        'immich-machine-learning',
        'immich-postgres',
        'immich-redis',
        'archivebox'
    ]

    services = config.get('services', {})

    for service in required_services:
        assert service in services, f"Service {service} not defined"


def test_aupat_core_service_configuration():
    """Test AUPAT Core service is correctly configured."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    aupat = config['services']['aupat-core']

    # Check build configuration
    assert 'build' in aupat
    assert aupat['build']['context'] == '.'
    assert aupat['build']['dockerfile'] == 'Dockerfile'

    # Check ports
    assert '5000:5000' in aupat.get('ports', [])

    # Check restart policy
    assert aupat.get('restart') == 'unless-stopped'

    # Check health check
    assert 'healthcheck' in aupat
    assert 'test' in aupat['healthcheck']


def test_immich_services_configuration():
    """Test Immich services are correctly configured."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    # Immich Server
    immich_server = config['services']['immich-server']
    assert '2283:3001' in immich_server.get('ports', [])
    assert 'healthcheck' in immich_server

    # Immich PostgreSQL
    postgres = config['services']['immich-postgres']
    assert 'POSTGRES_DB' in postgres.get('environment', {}) or 'POSTGRES_DB' in postgres.get('environment', [])
    assert 'healthcheck' in postgres

    # Immich Redis
    redis = config['services']['immich-redis']
    assert 'healthcheck' in redis


def test_archivebox_service_configuration():
    """Test ArchiveBox service is correctly configured."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    archivebox = config['services']['archivebox']

    # Check ports
    assert '8001:8000' in archivebox.get('ports', [])

    # Check restart policy
    assert archivebox.get('restart') == 'unless-stopped'

    # Check health check
    assert 'healthcheck' in archivebox


def test_network_configuration():
    """Test that custom network is defined."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    # Check network exists
    assert 'networks' in config
    assert 'aupat-network' in config['networks']

    # Check services use the network
    for service_name, service in config['services'].items():
        networks = service.get('networks', [])
        if isinstance(networks, list):
            assert 'aupat-network' in networks, f"Service {service_name} not on aupat-network"
        elif isinstance(networks, dict):
            assert 'aupat-network' in networks, f"Service {service_name} not on aupat-network"


def test_volume_persistence():
    """Test that volumes are defined for data persistence."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    # Check AUPAT Core has data volume
    aupat = config['services']['aupat-core']
    volumes = aupat.get('volumes', [])
    assert any('./data' in str(v) for v in volumes), "AUPAT Core missing data volume"

    # Check Immich has storage volumes
    immich_server = config['services']['immich-server']
    volumes = immich_server.get('volumes', [])
    assert any('immich' in str(v).lower() for v in volumes), "Immich missing storage volume"


def test_health_check_intervals():
    """Test that health checks have reasonable intervals."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    for service_name, service in config['services'].items():
        if 'healthcheck' in service:
            hc = service['healthcheck']

            # Check interval is specified
            if 'interval' in hc:
                interval = hc['interval']
                # Should be between 10s and 60s
                if isinstance(interval, str):
                    assert '10s' in interval or '30s' in interval or '60s' in interval, \
                        f"Service {service_name} has unusual health check interval: {interval}"


def test_environment_variables_defined():
    """Test that critical environment variables are defined."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    # AUPAT Core
    aupat_env = config['services']['aupat-core'].get('environment', {})
    if isinstance(aupat_env, dict):
        assert 'IMMICH_URL' in aupat_env
        assert 'ARCHIVEBOX_URL' in aupat_env

    # Immich Server
    immich_env = config['services']['immich-server'].get('environment', {})
    if isinstance(immich_env, dict):
        assert 'DB_HOSTNAME' in immich_env or any('DB_HOSTNAME' in str(e) for e in immich_env)


def test_depends_on_configuration():
    """Test that service dependencies are correctly configured."""
    compose_file = Path(__file__).parent.parent / 'docker-compose.yml'

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    # AUPAT Core should depend on Immich and ArchiveBox
    aupat_deps = config['services']['aupat-core'].get('depends_on', [])
    if isinstance(aupat_deps, list):
        assert 'immich-server' in aupat_deps
        assert 'archivebox' in aupat_deps

    # Immich Server should depend on PostgreSQL and Redis
    immich_deps = config['services']['immich-server'].get('depends_on', [])
    if isinstance(immich_deps, list):
        assert 'immich-postgres' in immich_deps
        assert 'immich-redis' in immich_deps
