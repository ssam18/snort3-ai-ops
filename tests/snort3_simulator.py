"""
Snort3 Event Simulator
Simulates Snort3 events over ZeroMQ for testing AI-Ops integration
"""

import zmq
import msgpack
import time
import random
import json
from datetime import datetime, UTC
from typing import Dict, Any

class Snort3EventSimulator:
    """Simulates Snort3 events for testing purposes."""
    
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555"):
        """Initialize the simulator."""
        self.endpoint = endpoint
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        
    def connect(self):
        """Connect to ZeroMQ endpoint."""
        self.socket.bind(self.endpoint)
        print(f"✓ Simulator bound to {self.endpoint}")
        time.sleep(1)  # Allow subscribers to connect
        
    def generate_alert_event(self) -> Dict[str, Any]:
        """Generate a simulated Snort alert event."""
        malicious_ips = [
            "45.142.212.100",  # Known malicious
            "185.220.101.50",  # Tor exit node
            "192.42.116.200",  # C2 server
        ]
        
        clean_ips = [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "192.168.1.50",  # Internal
        ]
        
        # 30% chance of malicious IP
        if random.random() < 0.3:
            src_ip = random.choice(malicious_ips)
            signature = random.choice([
                "ET MALWARE Possible C2 Beacon",
                "ET TROJAN Known Malware C2",
                "SURICATA HTTP suspicious User-Agent",
                "ET EXPLOIT Attempted SQL Injection",
            ])
            severity = random.choice(['critical', 'high'])
        else:
            src_ip = random.choice(clean_ips)
            signature = random.choice([
                "ET INFO DNS Query",
                "ET INFO HTTP Request",
                "ICMP Echo Request",
                "TCP SYN scan",
            ])
            severity = random.choice(['low', 'medium'])
        
        return {
            'type': 'alert',
            'timestamp': datetime.now(UTC).isoformat(),
            'src_ip': src_ip,
            'dst_ip': '192.168.1.100',
            'src_port': random.randint(1024, 65535),
            'dst_port': random.choice([80, 443, 22, 3389, 445]),
            'protocol': random.choice(['tcp', 'udp', 'icmp']),
            'signature': signature,
            'severity': severity,
            'gid': 1,
            'sid': random.randint(2000000, 2999999),
            'rev': 1,
            'classification': 'Attempted Information Leak',
            'priority': random.randint(1, 3),
        }
    
    def generate_flow_event(self) -> Dict[str, Any]:
        """Generate a simulated flow statistics event."""
        return {
            'type': 'flow',
            'timestamp': datetime.now(UTC).isoformat(),
            'src_ip': f"192.168.1.{random.randint(1, 255)}",
            'dst_ip': f"10.0.0.{random.randint(1, 255)}",
            'src_port': random.randint(1024, 65535),
            'dst_port': random.choice([80, 443, 22, 3389]),
            'protocol': 'tcp',
            'packets': random.randint(10, 1000),
            'bytes': random.randint(1000, 1000000),
            'duration': random.uniform(0.1, 60.0),
            'flags': random.choice(['SF', 'S0', 'REJ', 'RSTO']),
        }
    
    def generate_stats_event(self) -> Dict[str, Any]:
        """Generate Snort statistics event."""
        return {
            'type': 'stats',
            'timestamp': datetime.now(UTC).isoformat(),
            'packets_received': random.randint(1000, 10000),
            'packets_analyzed': random.randint(900, 9900),
            'packets_dropped': random.randint(0, 100),
            'alerts_generated': random.randint(0, 50),
            'memory_usage_mb': random.randint(100, 500),
            'cpu_usage_percent': random.uniform(5.0, 80.0),
        }
    
    def send_event(self, event: Dict[str, Any], use_msgpack: bool = True):
        """Send event over ZeroMQ."""
        if use_msgpack:
            data = msgpack.packb(event)
        else:
            data = json.dumps(event).encode()
        
        self.socket.send(data)
        
    def simulate(self, duration: int = 60, events_per_second: float = 2.0):
        """
        Run simulation for specified duration.
        
        Args:
            duration: How long to simulate in seconds
            events_per_second: Rate of event generation
        """
        print(f"\n🚀 Starting Snort3 Event Simulation")
        print(f"Duration: {duration}s")
        print(f"Event Rate: {events_per_second} events/sec")
        print(f"Expected Events: ~{int(duration * events_per_second)}\n")
        
        self.connect()
        
        start_time = time.time()
        event_count = 0
        
        try:
            while time.time() - start_time < duration:
                # Determine event type (70% alerts, 20% flows, 10% stats)
                rand = random.random()
                if rand < 0.7:
                    event = self.generate_alert_event()
                elif rand < 0.9:
                    event = self.generate_flow_event()
                else:
                    event = self.generate_stats_event()
                
                self.send_event(event)
                event_count += 1
                
                # Print progress
                if event_count % 10 == 0:
                    print(f"✓ Sent {event_count} events [{event['type']}] - "
                          f"Last: {event.get('signature', event['type'])[:50]}")
                
                # Sleep to maintain event rate
                time.sleep(1.0 / events_per_second)
                
        except KeyboardInterrupt:
            print("\n⚠ Simulation interrupted by user")
        finally:
            elapsed = time.time() - start_time
            print(f"\n📊 Simulation Complete:")
            print(f"   Total Events: {event_count}")
            print(f"   Duration: {elapsed:.1f}s")
            print(f"   Actual Rate: {event_count/elapsed:.2f} events/sec")
            
    def cleanup(self):
        """Cleanup resources."""
        self.socket.close()
        self.context.term()
        print("✓ Simulator cleanup complete")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Snort3 Event Simulator')
    parser.add_argument('--endpoint', default='tcp://127.0.0.1:5555',
                        help='ZeroMQ endpoint (default: tcp://127.0.0.1:5555)')
    parser.add_argument('--duration', type=int, default=60,
                        help='Simulation duration in seconds (default: 60)')
    parser.add_argument('--rate', type=float, default=2.0,
                        help='Events per second (default: 2.0)')
    
    args = parser.parse_args()
    
    simulator = Snort3EventSimulator(args.endpoint)
    try:
        simulator.simulate(duration=args.duration, events_per_second=args.rate)
    finally:
        simulator.cleanup()
