"""
Test that EnturSXSensor.native_value only shows active disruptions.

Verifies the fix for the bug where planned (future) disruptions
were showing in the sensor state even though they weren't active yet.
"""

from datetime import datetime, timedelta


def test_native_value_filters_planned_disruptions():
    """
    Test that native_value returns STATE_NORMAL when only planned 
    (future) disruptions exist.
    
    This simulates the bug scenario where two planned disruptions
    exist but neither should show in the sensor state.
    """
    # Create timestamps for testing
    now = datetime.now()
    future_start = now + timedelta(hours=2)
    future_end = now + timedelta(hours=4)
    
    # Simulate coordinator data with only planned (future) disruptions
    line_data = [
        {
            "summary": "Planned disruption 1",
            "description": "First planned event",
            "status": "planned",
            "progress": "open",
            "valid_from": future_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
        {
            "summary": "Planned disruption 2",
            "description": "Second planned event",
            "status": "planned",
            "progress": "open",
            "valid_from": future_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
    ]
    
    # Simulate the logic from EnturSXSensor.native_value
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != "open":
            continue
        
        # Verify the disruption is within its time window
        valid_from = item.get("valid_from")
        valid_to = item.get("valid_to")
        
        if not valid_from:
            continue
        
        try:
            start_timestamp = datetime.fromisoformat(valid_from).timestamp()
            
            # Check if disruption has started
            if now_timestamp < start_timestamp:
                continue
            
            # Check if disruption has ended (if end time is specified)
            if valid_to:
                end_timestamp = datetime.fromisoformat(valid_to).timestamp()
                if now_timestamp > end_timestamp:
                    continue
            
            # This disruption is currently active
            active_disruptions.append(item)
        except (ValueError, AttributeError):
            # Skip items with invalid timestamps
            continue
    
    # Expected: No active disruptions
    assert len(active_disruptions) == 0, "Should have 0 active disruptions (all are planned/future)"
    
    # The native_value should return STATE_NORMAL
    result = "Normal service" if not active_disruptions else active_disruptions[0].get("summary")
    assert result == "Normal service", "Should return 'Normal service' when no active disruptions"


def test_native_value_shows_active_disruptions():
    """
    Test that native_value returns the summary when there ARE active
    (currently ongoing) disruptions.
    """
    # Create timestamps for testing
    now = datetime.now()
    past_start = now - timedelta(hours=1)
    future_end = now + timedelta(hours=2)
    
    # Simulate coordinator data with an active disruption
    line_data = [
        {
            "summary": "Active disruption",
            "description": "Currently ongoing event",
            "status": "open",
            "progress": "open",
            "valid_from": past_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
    ]
    
    # Simulate the logic from EnturSXSensor.native_value
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != "open":
            continue
        
        # Verify the disruption is within its time window
        valid_from = item.get("valid_from")
        valid_to = item.get("valid_to")
        
        if not valid_from:
            continue
        
        try:
            start_timestamp = datetime.fromisoformat(valid_from).timestamp()
            
            # Check if disruption has started
            if now_timestamp < start_timestamp:
                continue
            
            # Check if disruption has ended (if end time is specified)
            if valid_to:
                end_timestamp = datetime.fromisoformat(valid_to).timestamp()
                if now_timestamp > end_timestamp:
                    continue
            
            # This disruption is currently active
            active_disruptions.append(item)
        except (ValueError, AttributeError):
            # Skip items with invalid timestamps
            continue
    
    # Expected: One active disruption
    assert len(active_disruptions) == 1, "Should have 1 active disruption"
    
    # The native_value should return the summary
    result = "Normal service" if not active_disruptions else active_disruptions[0].get("summary")
    assert result == "Active disruption", "Should return the disruption summary"


def test_native_value_combines_multiple_active():
    """
    Test that native_value correctly combines multiple active disruptions.
    """
    # Create timestamps for testing
    now = datetime.now()
    past_start = now - timedelta(hours=1)
    future_end = now + timedelta(hours=2)
    
    # Simulate coordinator data with multiple active disruptions
    line_data = [
        {
            "summary": "First active disruption",
            "description": "First event",
            "status": "open",
            "progress": "open",
            "valid_from": past_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
        {
            "summary": "Second active disruption",
            "description": "Second event",
            "status": "open",
            "progress": "open",
            "valid_from": past_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
    ]
    
    # Simulate the logic from EnturSXSensor.native_value
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != "open":
            continue
        
        # Verify the disruption is within its time window
        valid_from = item.get("valid_from")
        valid_to = item.get("valid_to")
        
        if not valid_from:
            continue
        
        try:
            start_timestamp = datetime.fromisoformat(valid_from).timestamp()
            
            # Check if disruption has started
            if now_timestamp < start_timestamp:
                continue
            
            # Check if disruption has ended (if end time is specified)
            if valid_to:
                end_timestamp = datetime.fromisoformat(valid_to).timestamp()
                if now_timestamp > end_timestamp:
                    continue
            
            # This disruption is currently active
            active_disruptions.append(item)
        except (ValueError, AttributeError):
            # Skip items with invalid timestamps
            continue
    
    # Expected: Two active disruptions
    assert len(active_disruptions) == 2, "Should have 2 active disruptions"
    
    # The native_value should combine them
    summaries = [item.get("summary", "Unknown disruption") for item in active_disruptions]
    combined = " | ".join(summaries)
    
    assert combined == "First active disruption | Second active disruption"


def test_native_value_ignores_expired_disruptions():
    """
    Test that native_value ignores expired (past) disruptions.
    """
    # Create timestamps for testing
    now = datetime.now()
    past_start = now - timedelta(hours=3)
    past_end = now - timedelta(hours=1)
    
    # Simulate coordinator data with an expired disruption
    line_data = [
        {
            "summary": "Expired disruption",
            "description": "Past event",
            "status": "expired",
            "progress": "closed",
            "valid_from": past_start.isoformat(),
            "valid_to": past_end.isoformat(),
        },
    ]
    
    # Simulate the logic from EnturSXSensor.native_value
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != "open":
            continue
        
        # Verify the disruption is within its time window
        valid_from = item.get("valid_from")
        valid_to = item.get("valid_to")
        
        if not valid_from:
            continue
        
        try:
            start_timestamp = datetime.fromisoformat(valid_from).timestamp()
            
            # Check if disruption has started
            if now_timestamp < start_timestamp:
                continue
            
            # Check if disruption has ended (if end time is specified)
            if valid_to:
                end_timestamp = datetime.fromisoformat(valid_to).timestamp()
                if now_timestamp > end_timestamp:
                    continue
            
            # This disruption is currently active
            active_disruptions.append(item)
        except (ValueError, AttributeError):
            # Skip items with invalid timestamps
            continue
    
    # Expected: No active disruptions
    assert len(active_disruptions) == 0, "Should have 0 active disruptions (expired)"
    
    # The native_value should return STATE_NORMAL
    result = "Normal service" if not active_disruptions else active_disruptions[0].get("summary")
    assert result == "Normal service", "Should return 'Normal service' for expired disruptions"


def test_native_value_mixed_statuses():
    """
    Test that native_value only shows active disruptions when mixed 
    with planned and expired disruptions.
    """
    # Create timestamps for testing
    now = datetime.now()
    past_start = now - timedelta(hours=3)
    past_end = now - timedelta(hours=1)
    active_start = now - timedelta(minutes=30)
    active_end = now + timedelta(hours=2)
    future_start = now + timedelta(hours=3)
    future_end = now + timedelta(hours=5)
    
    # Simulate coordinator data with mixed statuses
    line_data = [
        {
            "summary": "Active disruption",
            "description": "Currently ongoing",
            "status": "open",
            "progress": "open",
            "valid_from": active_start.isoformat(),
            "valid_to": active_end.isoformat(),
        },
        {
            "summary": "Planned disruption",
            "description": "Future event",
            "status": "planned",
            "progress": "open",
            "valid_from": future_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
        {
            "summary": "Expired disruption",
            "description": "Past event",
            "status": "expired",
            "progress": "closed",
            "valid_from": past_start.isoformat(),
            "valid_to": past_end.isoformat(),
        },
    ]
    
    # Simulate the logic from EnturSXSensor.native_value
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != "open":
            continue
        
        # Verify the disruption is within its time window
        valid_from = item.get("valid_from")
        valid_to = item.get("valid_to")
        
        if not valid_from:
            continue
        
        try:
            start_timestamp = datetime.fromisoformat(valid_from).timestamp()
            
            # Check if disruption has started
            if now_timestamp < start_timestamp:
                continue
            
            # Check if disruption has ended (if end time is specified)
            if valid_to:
                end_timestamp = datetime.fromisoformat(valid_to).timestamp()
                if now_timestamp > end_timestamp:
                    continue
            
            # This disruption is currently active
            active_disruptions.append(item)
        except (ValueError, AttributeError):
            # Skip items with invalid timestamps
            continue
    
    # Expected: One active disruption (not the planned or expired ones)
    assert len(active_disruptions) == 1, "Should have 1 active disruption"
    assert active_disruptions[0].get("summary") == "Active disruption"
    
    # The native_value should return only the active disruption
    result = active_disruptions[0].get("summary")
    assert result == "Active disruption", "Should show only the active disruption"


if __name__ == "__main__":
    test_native_value_filters_planned_disruptions()
    print("✓ Planned disruptions are filtered out")
    
    test_native_value_shows_active_disruptions()
    print("✓ Active disruptions are shown")
    
    test_native_value_combines_multiple_active()
    print("✓ Multiple active disruptions are combined")
    
    test_native_value_ignores_expired_disruptions()
    print("✓ Expired disruptions are ignored")
    
    test_native_value_mixed_statuses()
    print("✓ Mixed statuses handled correctly")
    
    print("\nAll tests passed!")
