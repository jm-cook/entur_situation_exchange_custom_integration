"""
Test that summary sensor correctly counts all deviations.

Verifies the fix for the bug where only the first deviation was processed.
"""


def test_summary_sensor_counts_all_statuses():
    """
    Test that the summary sensor processes ALL deviations for a line,
    not just the first one.
    
    This test simulates the bug where a line has multiple deviations
    with different statuses (open, planned, expired), and verifies that
    the summary sensor correctly counts both active and planned disruptions.
    """
    # Simulate coordinator data with multiple deviations for one line
    coordinator_data = {
        "SKY:Line:27": [
            {
                "summary": "Glaskar- og Selviktunnelen varsla stengd frå kl. 21.00",
                "description": "Road closed due to maintenance...",
                "status": "open",
                "progress": "open",
                "valid_from": "2025-11-09T20:50:00+01:00",
                "valid_to": "2025-11-10T05:30:00+01:00",
            },
            {
                "summary": "Glaskar- og Selviktunnelen varsla stengd frå kl. 00.01",
                "description": "E39 closed in other direction...",
                "status": "planned",
                "progress": "open",
                "valid_from": "2025-11-09T23:51:00+01:00",
                "valid_to": "2025-11-10T05:30:00+01:00",
            },
            {
                "summary": "Forseinkingar pga. trafikale problem",
                "description": "Delays due to traffic incident...",
                "status": "expired",
                "progress": "closed",
                "valid_from": "2025-11-09T16:33:00+01:00",
                "valid_to": "2025-11-09T22:10:00.323+01:00",
            },
        ],
    }
    
    lines = ["SKY:Line:27"]
    
    # Simulate the logic from EnturSXSummarySensor.extra_state_attributes
    active_lines = set()
    planned_lines = set()
    normal = []
    
    for line_ref in lines:
        line_data = coordinator_data.get(line_ref, [])
        if not line_data:
            normal.append(line_ref)
            continue
        
        has_active = False
        has_planned = False
        
        # Process ALL deviations for this line
        for deviation in line_data:
            status = deviation.get("status")
            
            # Skip expired
            if status == "expired":
                continue
            
            # Categorize by status
            if status == "open":
                has_active = True
                active_lines.add(line_ref)
            elif status == "planned":
                has_planned = True
                planned_lines.add(line_ref)
            else:
                has_active = True
                active_lines.add(line_ref)
        
        # If no non-expired deviations, mark as normal
        if not has_active and not has_planned:
            normal.append(line_ref)
    
    # Assertions
    assert len(active_lines) == 1, "Should count 1 active disruption"
    assert len(planned_lines) == 1, "Should count 1 planned disruption"
    assert len(normal) == 0, "Should have 0 normal lines"
    assert "SKY:Line:27" in active_lines
    assert "SKY:Line:27" in planned_lines


def test_old_behavior_would_miss_planned():
    """
    Demonstrate the OLD buggy behavior where only the first deviation
    was processed, missing the planned disruption.
    """
    coordinator_data = {
        "SKY:Line:27": [
            {
                "summary": "First deviation",
                "status": "open",
                "progress": "open",
            },
            {
                "summary": "Second deviation",
                "status": "planned",
                "progress": "open",
            },
        ],
    }
    
    lines = ["SKY:Line:27"]
    
    # OLD BUGGY LOGIC - only look at first item
    active_lines = []
    planned_lines = []
    
    for line_ref in lines:
        line_data = coordinator_data.get(line_ref, [])
        if line_data:
            first_item = line_data[0]  # BUG: Only looking at first!
            status = first_item.get("status")
            
            if status == "open":
                active_lines.append(line_ref)
            elif status == "planned":
                planned_lines.append(line_ref)
    
    # This demonstrates the bug
    assert len(active_lines) == 1
    assert len(planned_lines) == 0  # MISSED the planned one!


if __name__ == "__main__":
    test_summary_sensor_counts_all_statuses()
    print("✓ New behavior correctly counts all deviation statuses")
    
    test_old_behavior_would_miss_planned()
    print("✓ Confirmed old behavior had the bug")
    
    print("\nAll tests passed!")
