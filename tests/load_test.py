"""
Load Test for Snort3-AI-Ops
Simulates high-volume event processing to test system performance
"""

import argparse
import asyncio
import time
import zmq
import zmq.asyncio
import msgpack
import random
from datetime import datetime
from typing import List
import statistics


class LoadTestGenerator:
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555"):
        self.endpoint = endpoint
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(endpoint)
        time.sleep(1)  # Give time for socket to bind
        
    def generate_event(self, event_id: int) -> dict:
        """Generate a realistic security event"""
        event_types = ["alert", "flow", "stats"]
        severities = ["low", "medium", "high", "critical"]
        protocols = ["TCP", "UDP", "ICMP"]
        
        event = {
            "type": random.choice(event_types),
            "timestamp": datetime.now().isoformat(),
            "event_id": event_id,
            "source_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "destination_ip": f"10.0.{random.randint(0, 255)}.{random.randint(1, 255)}",
            "protocol": random.choice(protocols),
            "severity": random.choice(severities),
            "signature": f"Test Signature {random.randint(1, 100)}",
            "packet_length": random.randint(64, 1500),
            "threat_score": random.uniform(0.1, 1.0)
        }
        
        if event["type"] == "alert":
            event["sid"] = random.randint(1000, 9999)
            event["classification"] = random.choice([
                "attempted-recon", "attempted-dos", "trojan-activity",
                "network-scan", "suspicious-filename-detect"
            ])
        
        return event
    
    async def send_event(self, event: dict):
        """Send event via ZeroMQ"""
        packed = msgpack.packb(event)
        await self.socket.send(packed)
    
    async def send_events_batch(self, events: List[dict]):
        """Send a batch of events"""
        for event in events:
            await self.send_event(event)
    
    def close(self):
        """Close the socket"""
        self.socket.close()
        self.context.term()


class LoadTestMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.events_sent = 0
        self.batch_times: List[float] = []
        self.errors = 0
    
    def record_batch(self, count: int, duration: float):
        """Record metrics for a batch"""
        self.events_sent += count
        self.batch_times.append(duration)
    
    def get_stats(self) -> dict:
        """Calculate statistics"""
        elapsed = time.time() - self.start_time
        eps = self.events_sent / elapsed if elapsed > 0 else 0
        
        return {
            "total_events": self.events_sent,
            "duration_seconds": elapsed,
            "events_per_second": eps,
            "avg_batch_time": statistics.mean(self.batch_times) if self.batch_times else 0,
            "min_batch_time": min(self.batch_times) if self.batch_times else 0,
            "max_batch_time": max(self.batch_times) if self.batch_times else 0,
            "errors": self.errors
        }
    
    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("LOAD TEST RESULTS")
        print("="*70)
        print(f"Total Events Sent:      {stats['total_events']:,}")
        print(f"Test Duration:          {stats['duration_seconds']:.2f} seconds")
        print(f"Events Per Second:      {stats['events_per_second']:.2f}")
        print(f"Avg Batch Time:         {stats['avg_batch_time']*1000:.2f} ms")
        print(f"Min Batch Time:         {stats['min_batch_time']*1000:.2f} ms")
        print(f"Max Batch Time:         {stats['max_batch_time']*1000:.2f} ms")
        print(f"Errors:                 {stats['errors']}")
        print("="*70)
        
        # Performance assessment
        if stats['events_per_second'] >= 5000:
            print("✅ EXCELLENT: System handling high load efficiently")
        elif stats['events_per_second'] >= 1000:
            print("✓ GOOD: System performing well under load")
        elif stats['events_per_second'] >= 100:
            print("⚠ MODERATE: System handling load with some limitations")
        else:
            print("❌ POOR: System struggling with load")
        print("="*70 + "\n")


async def run_load_test(
    events_per_second: int,
    duration: int,
    batch_size: int = 100,
    endpoint: str = "tcp://127.0.0.1:5555"
):
    """Run the load test"""
    print(f"\n🚀 Starting Load Test")
    print(f"   Target Rate: {events_per_second:,} events/second")
    print(f"   Duration: {duration} seconds")
    print(f"   Batch Size: {batch_size}")
    print(f"   Endpoint: {endpoint}\n")
    
    generator = LoadTestGenerator(endpoint)
    metrics = LoadTestMetrics()
    
    # Calculate timing
    batches_per_second = events_per_second / batch_size
    sleep_between_batches = 1.0 / batches_per_second if batches_per_second > 0 else 0
    
    event_id = 0
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < duration:
            # Generate batch
            batch_start = time.time()
            events = [generator.generate_event(event_id + i) for i in range(batch_size)]
            
            # Send batch
            try:
                await generator.send_events_batch(events)
                batch_duration = time.time() - batch_start
                metrics.record_batch(batch_size, batch_duration)
                event_id += batch_size
                
                # Progress indicator
                if event_id % (events_per_second * 10) == 0:
                    elapsed = time.time() - start_time
                    current_rate = metrics.events_sent / elapsed
                    print(f"Progress: {metrics.events_sent:,} events sent | "
                          f"Rate: {current_rate:.0f} eps | "
                          f"Elapsed: {elapsed:.1f}s")
                
            except Exception as e:
                print(f"Error sending batch: {e}")
                metrics.errors += 1
            
            # Rate limiting
            if sleep_between_batches > 0:
                await asyncio.sleep(sleep_between_batches)
    
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
    
    finally:
        generator.close()
        metrics.print_stats()


def main():
    parser = argparse.ArgumentParser(description="Load test for Snort3-AI-Ops")
    parser.add_argument(
        "--events-per-second",
        type=int,
        default=1000,
        help="Target events per second (default: 1000)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Events per batch (default: 100)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="tcp://127.0.0.1:5555",
        help="ZeroMQ endpoint (default: tcp://127.0.0.1:5555)"
    )
    
    args = parser.parse_args()
    
    # Run the test
    asyncio.run(run_load_test(
        events_per_second=args.events_per_second,
        duration=args.duration,
        batch_size=args.batch_size,
        endpoint=args.endpoint
    ))


if __name__ == "__main__":
    main()
