"""Snort3 Event Stream connector using ZeroMQ."""

import asyncio
import json
from typing import AsyncIterator, Dict, Any, Optional

import zmq
import zmq.asyncio
import structlog
import msgpack

logger = structlog.get_logger(__name__)


class Snort3EventStream:
    """Connector for receiving events from Snort3 via ZeroMQ."""
    
    def __init__(
        self, 
        endpoint: str = 'tcp://127.0.0.1:5555',
        buffer_size: int = 10000,
        timeout: int = 5000
    ):
        """
        Initialize the Snort3 event stream connector.
        
        Args:
            endpoint: ZeroMQ endpoint URL
            buffer_size: Maximum buffer size for messages
            timeout: Receive timeout in milliseconds
        """
        self.endpoint = endpoint
        self.buffer_size = buffer_size
        self.timeout = timeout
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.connected = False
        
        self.stats = {
            'events_received': 0,
            'events_dropped': 0,
            'errors': 0
        }
        
        logger.info(
            "Snort3 Event Stream initialized",
            endpoint=endpoint,
            buffer_size=buffer_size
        )
    
    async def connect(self) -> None:
        """Establish connection to Snort3 event stream."""
        try:
            self.context = zmq.asyncio.Context()
            self.socket = self.context.socket(zmq.PULL)
            
            # Set socket options
            self.socket.setsockopt(zmq.RCVHWM, self.buffer_size)
            self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
            self.socket.setsockopt(zmq.LINGER, 0)
            
            # Connect to endpoint
            self.socket.connect(self.endpoint)
            self.connected = True
            
            logger.info("Connected to Snort3 event stream", endpoint=self.endpoint)
        
        except Exception as e:
            logger.error(
                "Failed to connect to Snort3 event stream",
                endpoint=self.endpoint,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Snort3 event stream."""
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.context:
            self.context.term()
            self.context = None
        
        self.connected = False
        
        logger.info(
            "Disconnected from Snort3 event stream",
            stats=self.stats
        )
    
    async def stream(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream events from Snort3.
        
        Yields:
            Event dictionaries
        """
        if not self.connected:
            raise RuntimeError("Not connected to event stream. Call connect() first.")
        
        logger.info("Starting event stream processing")
        
        try:
            while self.connected:
                try:
                    # Receive message
                    message = await self.socket.recv()
                    
                    # Deserialize event
                    event = self._deserialize_event(message)
                    
                    if event:
                        self.stats['events_received'] += 1
                        
                        # Add reception metadata
                        event['_received_at'] = asyncio.get_event_loop().time()
                        
                        yield event
                    else:
                        self.stats['events_dropped'] += 1
                        logger.warning("Failed to deserialize event")
                
                except zmq.Again:
                    # Timeout - continue
                    await asyncio.sleep(0.1)
                    continue
                
                except asyncio.CancelledError:
                    logger.info("Event stream cancelled")
                    break
                
                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(
                        "Error receiving event",
                        error=str(e),
                        exc_info=True
                    )
                    await asyncio.sleep(1)  # Back off on errors
        
        finally:
            logger.info("Event stream processing stopped", stats=self.stats)
    
    def _deserialize_event(self, message: bytes) -> Optional[Dict[str, Any]]:
        """
        Deserialize event message.
        
        Args:
            message: Raw message bytes
        
        Returns:
            Deserialized event dictionary or None if failed
        """
        try:
            # Try MessagePack first (more efficient)
            try:
                event = msgpack.unpackb(message, raw=False)
                return event
            except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackException):
                pass
            
            # Fall back to JSON
            try:
                event = json.loads(message.decode('utf-8'))
                return event
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            
            logger.warning("Failed to deserialize message with both msgpack and json")
            return None
        
        except Exception as e:
            logger.error(
                "Unexpected error deserializing event",
                error=str(e),
                exc_info=True
            )
            return None
    
    async def send_control_command(self, command: Dict[str, Any]) -> bool:
        """
        Send a control command to Snort3 (future enhancement).
        
        Args:
            command: Control command dictionary
        
        Returns:
            True if successful, False otherwise
        """
        # This would use a separate ZeroMQ socket for control
        # Placeholder for future implementation
        logger.info("Control command (not implemented)", command=command)
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get connection statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
