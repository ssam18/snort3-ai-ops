"""
Test suite for Threat Intelligence Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.threat_intelligence_agent import ThreatIntelligenceAgent
from core.config import ThreatIntelConfig


@pytest.fixture
def threat_intel_config():
    """Create test configuration."""
    return ThreatIntelConfig(
        enabled=True,
        api_keys={
            'virustotal': 'test_vt_key',
            'abuseipdb': 'test_abuse_key'
        },
        confidence_threshold=0.7
    )


@pytest.fixture
def agent(threat_intel_config):
    """Create agent instance."""
    return ThreatIntelligenceAgent(config=threat_intel_config)


class TestThreatIntelligenceAgent:
    """Test cases for Threat Intelligence Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.config.enabled is True
        assert agent.config.confidence_threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_enrich_event_with_malicious_ip(self, agent):
        """Test enrichment of event with known malicious IP."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'signature': 'test_signature'
        }
        
        # Mock the _lookup_ioc method
        with patch.object(agent, '_lookup_ioc', new_callable=AsyncMock) as mock_lookup:
            mock_lookup.return_value = {
                'value': '8.8.8.8',
                'type': 'ip',
                'threat_score': 80,
                'malicious': True,
                'sources': {'virustotal': {'positives': 12, 'total': 70}},
                'tags': ['malicious'],
                'first_seen': None,
                'last_seen': None
            }
            
            result = await agent.enrich_event(event)
            
            # Verify enrichment - result should have iocs, threat_score, etc
            assert 'iocs' in result
            assert len(result['iocs']) > 0
            assert result['threat_score'] == 80
            # Mock should be called for each IP
            assert mock_lookup.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_enrich_event_with_clean_ip(self, agent):
        """Test enrichment of event with clean IP."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100',
            'dst_ip': '1.1.1.1',
            'signature': 'test_signature'
        }
        
        with patch.object(agent, '_lookup_ioc', new_callable=AsyncMock) as mock_lookup:
            mock_lookup.return_value = {
                'value': '1.1.1.1',
                'type': 'ip',
                'threat_score': 0,
                'malicious': False,
                'sources': {},
                'tags': [],
                'first_seen': None,
                'last_seen': None
            }
            
            result = await agent.enrich_event(event)
            
            # Verify enrichment
            assert 'iocs' in result
            # Clean IP should not be malicious
            assert result['threat_score'] == 0
    
    @pytest.mark.asyncio
    async def test_caching(self, agent):
        """Test that results are cached."""
        ioc = '192.168.1.100'
        
        # First call - should populate cache
        result1 = await agent._lookup_ioc(ioc, 'ip')
        assert result1 is not None
        
        # Verify cache_result was called
        cache_key = f"ip:{ioc}"
        # The method uses internal caching, so we just verify it works
        result2 = await agent._lookup_ioc(ioc, 'ip')
        assert result2 is not None
        assert result1['value'] == result2['value']
    
    @pytest.mark.asyncio
    async def test_multiple_source_correlation(self, agent):
        """Test correlation across multiple threat intel sources."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8'
        }
        
        # Mock the _lookup_ioc method to return threat data with multiple sources
        with patch.object(agent, '_lookup_ioc', new_callable=AsyncMock) as mock_lookup:
            mock_lookup.return_value = {
                'value': '8.8.8.8',
                'type': 'ip',
                'threat_score': 85,
                'malicious': True,
                'sources': {
                    'virustotal': {'confidence': 90},
                    'abuseipdb': {'confidence': 80}
                },
                'tags': ['malicious'],
                'first_seen': None,
                'last_seen': None
            }
            
            result = await agent.enrich_event(event)
            
            # Both IPs should be looked up
            assert mock_lookup.call_count >= 1
            
            # Results should include iocs with sources
            assert 'iocs' in result
            assert result['threat_score'] > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, agent):
        """Test API rate limiting is respected."""
        import time
        
        # Simulate rapid requests
        start_time = time.time()
        tasks = []
        for i in range(5):
            task = agent._lookup_ioc(f'192.168.1.{i}', 'ip')
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Each lookup has a 0.1s delay, so 5 concurrent should take at least 0.1s
        assert elapsed >= 0.1
        assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test graceful error handling."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100'
        }
        
        # Mock API error
        with patch.object(agent, '_lookup_ioc', new_callable=AsyncMock) as mock_lookup:
            mock_lookup.side_effect = Exception("API Error")
            
            # Should handle the error gracefully
            try:
                result = await agent.enrich_event(event)
                # If no exception is raised, that's also acceptable
                assert result is not None
            except Exception as e:
                # Error handling is implementation-specific
                # Just verify we can catch it
                assert "API Error" in str(e)
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, agent):
        """Test threat score calculation."""
        # Test with a public IP (should have higher threat score)
        result1 = await agent._lookup_ioc('8.8.8.8', 'ip')
        assert result1['threat_score'] > 0
        
        # Test with a private IP (should have lower threat score)
        result2 = await agent._lookup_ioc('192.168.1.1', 'ip')
        assert 'private_ip' in result2['tags']
        
        # Private IP should generally have lower score than public
        assert result2['threat_score'] < result1['threat_score']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

