#!/usr/bin/env python3
"""
Test script to verify WebSocket functionality with multiple connections.
Run this while Django server is running to test concurrent WebSocket connections.
"""

import asyncio
import websockets
import json
import time

async def test_websocket_connection(connection_id, message):
    """Test a single WebSocket connection."""
    uri = "ws://localhost:8000/ws/chat/"
    
    try:
        print(f"Connection {connection_id}: Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            print(f"Connection {connection_id}: Connected successfully")
            
            # Send a chat message
            await websocket.send(json.dumps({
                'type': 'chat',
                'message': f"{message} (from connection {connection_id})"
            }))
            print(f"Connection {connection_id}: Message sent")
            
            # Listen for responses for 10 seconds
            timeout = 10
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    print(f"Connection {connection_id}: Received {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'error':
                        print(f"Connection {connection_id}: ERROR - {data.get('message')}")
                        return False
                    elif data.get('type') == 'response_complete':
                        print(f"Connection {connection_id}: Response completed successfully")
                        return True
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(f"Connection {connection_id}: Connection closed unexpectedly")
                    return False
            
            print(f"Connection {connection_id}: Timeout reached")
            return False
            
    except Exception as e:
        print(f"Connection {connection_id}: Error - {e}")
        return False

async def test_concurrent_connections():
    """Test multiple concurrent WebSocket connections."""
    print("Starting concurrent WebSocket test...")
    print("=" * 50)
    
    # Create multiple concurrent connections
    tasks = []
    for i in range(3):  # Test with 3 concurrent connections
        task = test_websocket_connection(i+1, f"Hello from test {i+1}")
        tasks.append(task)
    
    # Run all connections concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("=" * 50)
    print("Test Results:")
    successful = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Connection {i+1}: FAILED with exception - {result}")
        elif result:
            print(f"Connection {i+1}: SUCCESS")
            successful += 1
        else:
            print(f"Connection {i+1}: FAILED")
    
    print(f"\nOverall: {successful}/{len(results)} connections successful")
    
    if successful == len(results):
        print("🎉 All WebSocket connections worked correctly!")
    else:
        print("❌ Some WebSocket connections failed")

if __name__ == "__main__":
    print("WebSocket Concurrent Test")
    print("Make sure Django server is running on localhost:8000")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(test_concurrent_connections())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")