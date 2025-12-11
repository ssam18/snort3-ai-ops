"""
Test suite for Threat Intelligence Agent
"""

import pytest
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
        
        # Mock VirusTotal API response
        with patch.object(agent, '_query_virustotal', new_callable=AsyncMock) as mock_vt:
            mock_vt.return_value = {
                'malicious': True,
                'score': 85,
                'categories': ['malware', 'c2'],
                'first_seen': '2025-01-01',
                'last_seen': '2025-01-10'
            }
            
            enriched = await agent.enrich_event(event)
            
            assert 'threat_intel' in enriched
            assert enriched['threat_intel']['malicious'] is True
            assert enriched['threat_intel']['score'] == 85
            assert 'malware' in enriched['threat_intel']['categories']
    
    @pytest.mark.asyncio
    async def test_enrich_event_with_clean_ip(self, agent):
        """Test enrichment of event with clean IP."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100',
            'dst_ip': '1.1.1.1',
            'signature': 'test_signature'
        }
        
        with patch.object(agent, '_query_virustotal', new_callable=AsyncMock) as mock_vt:
            mock_vt.return_value = {
                'malicious': False,
                'score': 5,
                'categories': [],
                'first_seen': None,
                'last_seen': None
            }
            
            enriched = await agent.enrich_event(event)
            
            assert 'threat_intel' in enriched
            assert enriched['threat_intel']['malicious'] is False
            assert enriched['threat_intel']['score'] == 5
    
    @pytest.mark.asyncio
    async def test_caching(self, agent):
        """Test that results are cached."""
        ip = '192.168.1.100'
        
        # First call
        with patch.object(agent, '_query_virustotal', new_callable=AsyncMock) as mock_vt:
            mock_vt.return_value = {'malicious': True, 'score': 90}
            
            result1 = await agent._lookup_ip(ip)
            assert mock_vt.call_count == 1
            
            # Second call should use cache
            result2 = await agent._lookup_ip(ip)
            assert mock_vt.call_count == 1  # Still 1, not called again
            assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_multiple_source_correlation(self, agent):
        """Test correlation across multiple threat intel sources."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100'
        }
        
        # Mock multiple sources
        with patch.object(agent, '_query_virustotal', new_callable=AsyncMock) as mock_vt, \
             patch.object(agent, '_query_abuseipdb', new_callable=AsyncMock) as mock_abuse:
            
            mock_vt.return_value = {'score': 80, 'malicious': True}
            mock_abuse.return_value = {'score': 75, 'malicious': True}
            
            enriched = await agent.enrich_event(event)
            
            # Should have combined data from both sources
            assert enriched['threat_intel']['sources'] == ['virustotal', 'abuseipdb']
            assert enriched['threat_intel']['confidence'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, agent):
        """Test API rate limiting is respected."""
        # Simulate rapid requests
        tasks = []
        for i in range(10):
            task = agent._lookup_ip(f'192.168.1.{i}')
            tasks.append(task)
        
        # Should not raise rate limit errors
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(not isinstance(r, Exception) for r in results)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test graceful error handling."""
        event = {
            'type': 'alert',
            'src_ip': '192.168.1.100'
        }
        
        # Mock API error
        with patch.object(agent, '_query_virustotal', new_callable=AsyncMock) as mock_vt:
            mock_vt.side_effect = Exception("API Error")
            
            # Should not raise, should return partial data
            enriched = await agent.enrich_event(event)
            assert 'error' in enriched.get('threat_intel', {})
    
    def test_confidence_scoring(self, agent):
        """Test confidence score calculation."""
        # High confidence - multiple sources agree
        sources = [
            {'score': 90, 'malicious': True},
            {'score': 85, 'malicious': True},
            {'score': 80, 'malicious': True}
        ]
        confidence = agent._calculate_confidence(sources)
        assert confidence >= 0.9
        
        # Low confidence - sources disagree
        sources = [
            {'score': 90, 'malicious': True},
            {'score': 10, 'malicious': False}
        ]
        confidence = agent._calculate_confidence(sources)
        assert confidence < 0.6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
