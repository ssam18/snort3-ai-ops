"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture
def config_path():
    """Return path to test configuration."""
    return Path(__file__).parent.parent / 'config' / 'config.example.yaml'


@pytest.fixture
def sample_event():
    """Return a sample security event."""
    return {
        'id': 'test-event-001',
        'type': 'alert',
        'timestamp': '2025-12-11T10:00:00Z',
        'src_ip': '192.168.1.100',
        'dst_ip': '10.0.0.50',
        'src_port': 54321,
        'dst_port': 80,
        'protocol': 'tcp',
        'signature': 'Test Signature: Suspicious Activity',
        'severity': 75,
        'bytes_sent': 1024,
        'bytes_recv': 2048,
        'packet_count': 10,
        'duration': 5.5
    }


@pytest.fixture
def sample_flow_event():
    """Return a sample flow event."""
    return {
        'id': 'test-flow-001',
        'type': 'flow',
        'timestamp': '2025-12-11T10:00:00Z',
        'src_ip': '192.168.1.100',
        'dst_ip': '10.0.0.50',
        'src_port': 54321,
        'dst_port': 443,
        'protocol': 'tcp',
        'bytes_sent': 5000,
        'bytes_recv': 50000,
        'packet_count': 100,
        'duration': 30.0
    }


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
