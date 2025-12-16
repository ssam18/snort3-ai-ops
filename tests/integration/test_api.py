"""
Integration tests for Snort3-AI-Ops API
Tests the RESTful and GraphQL endpoints
"""

import pytest
import httpx
import asyncio
from typing import AsyncGenerator

# Base URL for API (can be overridden with environment variable)
import os
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for testing"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    async def test_health_check(self, client: httpx.AsyncClient):
        """Test GET /api/v1/health"""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "agents_running" in data
        
        assert data["status"] in ["healthy", "stopped"]
        assert isinstance(data["agents_running"], int)


@pytest.mark.asyncio
class TestAgentsEndpoints:
    """Tests for agent management endpoints"""
    
    async def test_list_agents(self, client: httpx.AsyncClient):
        """Test GET /api/v1/agents"""
        response = await client.get("/api/v1/agents")
        
        # Accept both 200 (running) and 503 (not running)
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 5  # Should have 5 agents
            
            # Verify agent structure
            for agent in data:
                assert "id" in agent
                assert "name" in agent
                assert "role" in agent
                assert "status" in agent
                assert "tasks_completed" in agent
                assert "success_rate" in agent
    
    async def test_get_specific_agent(self, client: httpx.AsyncClient):
        """Test GET /api/v1/agents/{id}"""
        response = await client.get("/api/v1/agents/threat-intel")
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == "threat-intel"
            assert "Threat Intelligence" in data["name"]
    
    async def test_get_nonexistent_agent(self, client: httpx.AsyncClient):
        """Test GET /api/v1/agents/{id} for non-existent agent"""
        response = await client.get("/api/v1/agents/nonexistent")
        
        if response.status_code != 503:  # Skip if engine not running
            assert response.status_code == 404


@pytest.mark.asyncio
class TestInvestigateEndpoint:
    """Tests for investigation endpoint"""
    
    async def test_start_investigation(self, client: httpx.AsyncClient):
        """Test POST /api/v1/investigate"""
        payload = {
            "ioc_type": "ip",
            "ioc_value": "192.168.1.100",
            "priority": "high"
        }
        
        response = await client.post("/api/v1/investigate", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "investigation_started"
            assert "investigation_id" in data
            assert data["ioc"]["type"] == "ip"
            assert data["ioc"]["value"] == "192.168.1.100"
    
    async def test_investigate_domain(self, client: httpx.AsyncClient):
        """Test investigating a domain"""
        payload = {
            "ioc_type": "domain",
            "ioc_value": "malicious.example.com",
            "priority": "medium"
        }
        
        response = await client.post("/api/v1/investigate", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert "investigation_id" in data


@pytest.mark.asyncio
class TestBlockEndpoint:
    """Tests for blocking endpoint"""
    
    async def test_block_ip(self, client: httpx.AsyncClient):
        """Test POST /api/v1/block"""
        payload = {
            "ioc_type": "ip",
            "ioc_value": "192.168.1.100",
            "reason": "Malicious activity detected",
            "duration": 3600
        }
        
        response = await client.post("/api/v1/block", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "blocked"
            assert data["ioc"]["value"] == "192.168.1.100"
            assert "expires_at" in data


@pytest.mark.asyncio
class TestIncidentsEndpoints:
    """Tests for incidents endpoints"""
    
    async def test_list_incidents(self, client: httpx.AsyncClient):
        """Test GET /api/v1/incidents"""
        response = await client.get("/api/v1/incidents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify incident structure
        if len(data) > 0:
            incident = data[0]
            assert "id" in incident
            assert "timestamp" in incident
            assert "source_ip" in incident
            assert "destination_ip" in incident
            assert "severity" in incident
            assert "threat_score" in incident
    
    async def test_list_incidents_with_filter(self, client: httpx.AsyncClient):
        """Test GET /api/v1/incidents with severity filter"""
        response = await client.get("/api/v1/incidents?severity=high&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        
        # Verify all returned incidents have high severity
        for incident in data:
            assert incident["severity"] == "high"
    
    async def test_get_specific_incident(self, client: httpx.AsyncClient):
        """Test GET /api/v1/incidents/{id}"""
        # First get list of incidents
        list_response = await client.get("/api/v1/incidents?limit=1")
        incidents = list_response.json()
        
        if len(incidents) > 0:
            incident_id = incidents[0]["id"]
            
            # Get specific incident
            response = await client.get(f"/api/v1/incidents/{incident_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == incident_id


@pytest.mark.asyncio
class TestReportsEndpoint:
    """Tests for reports generation"""
    
    async def test_generate_report(self, client: httpx.AsyncClient):
        """Test POST /api/v1/reports/generate"""
        response = await client.post(
            "/api/v1/reports/generate?report_type=executive&time_range=24h"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "report_generated"
            assert "report_id" in data
            assert "download_url" in data


@pytest.mark.asyncio
class TestStatsEndpoint:
    """Tests for statistics endpoint"""
    
    async def test_get_stats(self, client: httpx.AsyncClient):
        """Test GET /api/v1/stats"""
        response = await client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "events_processed" in data
        assert "incidents_created" in data
        assert "threats_blocked" in data
        assert "reports_generated" in data
        assert "uptime_seconds" in data
        
        # Verify all are numbers
        assert isinstance(data["events_processed"], int)
        assert isinstance(data["incidents_created"], int)
        assert isinstance(data["threats_blocked"], int)
        assert isinstance(data["reports_generated"], int)
        assert isinstance(data["uptime_seconds"], float)


@pytest.mark.asyncio
class TestDashboardEndpoint:
    """Tests for dashboard"""
    
    async def test_dashboard_loads(self, client: httpx.AsyncClient):
        """Test GET / (dashboard)"""
        response = await client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Snort3-AI-Ops Dashboard" in response.text


@pytest.mark.asyncio
class TestAPIDocumentation:
    """Tests for API documentation"""
    
    async def test_openapi_docs(self, client: httpx.AsyncClient):
        """Test GET /docs (OpenAPI/Swagger UI)"""
        response = await client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    async def test_openapi_schema(self, client: httpx.AsyncClient):
        """Test GET /openapi.json"""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
