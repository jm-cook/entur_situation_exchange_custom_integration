"""Test request history tracking and logging."""
from collections import deque
from datetime import datetime


def simulate_request_history():
    """Simulate what the request history will look like when throttled."""
    
    # Simulate the rolling buffer of last 10 requests
    request_history = deque(maxlen=10)
    
    # Simulate 15 successful requests (only last 10 will be kept)
    base_time = datetime.now()
    for i in range(15):
        timestamp = base_time.replace(
            hour=0,
            minute=i,
            second=15,
            microsecond=588000
        )
        request_history.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "duration_ms": 245.3 + (i * 10),  # Simulate varying response times
            "status": "success",
            "lines_count": 24,
            "provider": "SKY",
        })
    
    # Add the final request that got throttled
    throttle_time = base_time.replace(hour=0, minute=15, second=14, microsecond=588000)
    request_history.append({
        "timestamp": throttle_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "duration_ms": 125.7,
        "status": "error_429",
        "error": "Too Many Requests",
        "provider": "SKY",
    })
    
    # Show what would be logged
    print("Simulated Log Output When Throttled:")
    print("=" * 80)
    print()
    print("WARNING: Rate limit hit (429 Too Many Requests) - throttle event #1.")
    print("WARNING: Applying 120 second back-off. Will retry after cooldown.")
    print("WARNING: Preserving last known state to keep sensors available.")
    print()
    print(f"WARNING: Request history (last {len(request_history)} requests leading to throttle):")
    for i, req in enumerate(request_history, 1):
        extra_info = (
            f" | lines={req['lines_count']}" 
            if "lines_count" in req 
            else f" | error={req.get('error', 'unknown')}"
        )
        print(
            f"WARNING:   #{i}: {req.get('timestamp', 'unknown')} | "
            f"provider={req.get('provider', '?')} | "
            f"status={req.get('status', 'unknown')} | "
            f"duration={req.get('duration_ms', '?')}ms{extra_info}"
        )
    
    print()
    print("=" * 80)
    print()
    print("Analysis from the history:")
    print(f"  - Total requests tracked: {len(request_history)}")
    print(f"  - Successful requests: {sum(1 for r in request_history if r['status'] == 'success')}")
    print(f"  - Failed requests: {sum(1 for r in request_history if r['status'].startswith('error_'))}")
    
    # Calculate timing between requests
    timestamps = [
        datetime.strptime(r['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
        for r in request_history
    ]
    
    if len(timestamps) > 1:
        intervals = [
            (timestamps[i] - timestamps[i-1]).total_seconds()
            for i in range(1, len(timestamps))
        ]
        print(f"  - Average interval between requests: {sum(intervals)/len(intervals):.1f}s")
        print(f"  - Min interval: {min(intervals):.1f}s")
        print(f"  - Max interval: {max(intervals):.1f}s")


def simulate_rapid_requests():
    """Simulate what might cause throttling - rapid requests."""
    
    request_history = deque(maxlen=10)
    
    # Simulate scenario where something triggers multiple rapid requests
    base_time = datetime.now()
    
    # Normal requests
    for i in range(5):
        timestamp = base_time.replace(minute=i, second=0, microsecond=0)
        request_history.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "duration_ms": 250.0,
            "status": "success",
            "lines_count": 24,
            "provider": "SKY",
        })
    
    # Then rapid requests (maybe from config flow validation?)
    for i in range(4):
        timestamp = base_time.replace(minute=5, second=i*2, microsecond=0)
        request_history.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "duration_ms": 180.0,
            "status": "success",
            "lines_count": 24,
            "provider": "SKY",
        })
    
    # Throttled
    timestamp = base_time.replace(minute=5, second=8, microsecond=0)
    request_history.append({
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "duration_ms": 95.0,
        "status": "error_429",
        "error": "Too Many Requests",
        "provider": "SKY",
    })
    
    print("\nScenario: Rapid requests detected")
    for i, req in enumerate(request_history, 1):
        extra_info = (
            f" | lines={req['lines_count']}" 
            if "lines_count" in req 
            else f" | error={req.get('error', 'unknown')}"
        )
        print(
            f"  #{i}: {req.get('timestamp', 'unknown')} | "
            f"provider={req.get('provider', '?')} | "
            f"status={req.get('status', 'unknown')} | "
            f"duration={req.get('duration_ms', '?')}ms{extra_info}"
        )
    
    timestamps = [
        datetime.strptime(r['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
        for r in request_history
    ]
    
    print("\nInterval analysis:")
    for i in range(1, len(timestamps)):
        interval = (timestamps[i] - timestamps[i-1]).total_seconds()
        print(f"  Request {i} -> {i+1}: {interval:.1f}s apart")


if __name__ == "__main__":
    simulate_request_history()
    print("\n\n")
    simulate_rapid_requests()
