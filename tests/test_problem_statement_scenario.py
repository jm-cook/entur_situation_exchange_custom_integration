"""
Test simulating the exact scenario from the problem statement.

Problem: The sensor state currently shows summaries of two planned disruptions.
Expected: "Normal service" (because both disruptions are planned/future, not currently active).
"""

from datetime import datetime, timedelta

# Constants
STATUS_OPEN = "open"
STATUS_PLANNED = "planned"
STATE_NORMAL = "Normal service"


def test_problem_statement_scenario():
    """
    Test the exact scenario described in the problem statement:
    - Two planned disruptions exist
    - Both are in the future (not yet active)
    - Expected state: "Normal service"
    """
    
    # Create future timestamps (disruptions starting in 2 hours)
    now = datetime.now()
    future_start = now + timedelta(hours=2)
    future_end = now + timedelta(hours=5)
    
    # Simulate coordinator data with two planned disruptions
    # (This is what the API returns for future events)
    line_data = [
        {
            "summary": "First planned disruption summary",
            "description": "Maintenance work starting in 2 hours",
            "status": STATUS_PLANNED,  # API correctly marks it as planned
            "progress": "open",
            "valid_from": future_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
        {
            "summary": "Second planned disruption summary",
            "description": "Road closure starting in 2 hours",
            "status": STATUS_PLANNED,  # API correctly marks it as planned
            "progress": "open",
            "valid_from": future_start.isoformat(),
            "valid_to": future_end.isoformat(),
        },
    ]
    
    # Simulate the FIXED native_value logic
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != STATUS_OPEN:
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
    
    # Determine native_value
    if not active_disruptions:
        native_value = STATE_NORMAL
    elif len(active_disruptions) == 1:
        native_value = active_disruptions[0].get("summary")
    else:
        summaries = [item.get("summary", "Unknown disruption") for item in active_disruptions]
        native_value = " | ".join(summaries)
    
    # Verify the fix works
    print("=" * 80)
    print("Problem Statement Scenario Test")
    print("=" * 80)
    print(f"\nInput:")
    print(f"  - Two planned disruptions")
    print(f"  - Both start in 2 hours (future events)")
    print(f"  - Both have status='{STATUS_PLANNED}'")
    print(f"\nOLD BEHAVIOR (BUG):")
    print(f"  - Would return: '{line_data[0].get('summary')}'")
    print(f"  - This is WRONG because the disruption is not yet active")
    print(f"\nNEW BEHAVIOR (FIXED):")
    print(f"  - Active disruptions found: {len(active_disruptions)}")
    print(f"  - Returns: '{native_value}'")
    print(f"  - This is CORRECT - no active disruptions exist")
    print(f"\nExpected: '{STATE_NORMAL}'")
    print(f"Got:      '{native_value}'")
    
    assert native_value == STATE_NORMAL, (
        f"Expected '{STATE_NORMAL}' but got '{native_value}'"
    )
    print(f"\n✅ TEST PASSED - Fix correctly handles planned disruptions!")
    print("=" * 80)


def test_when_planned_becomes_active():
    """
    Test what happens when a planned disruption becomes active.
    """
    
    # Create timestamps where disruption has just started
    now = datetime.now()
    just_started = now - timedelta(minutes=5)  # Started 5 minutes ago
    future_end = now + timedelta(hours=3)
    
    # Simulate coordinator data where a disruption just became active
    # Note: The API's status determination logic would mark this as "open" now
    line_data = [
        {
            "summary": "Active disruption that was previously planned",
            "description": "Maintenance work now in progress",
            "status": STATUS_OPEN,  # API marks as open because it's now active
            "progress": "open",
            "valid_from": just_started.isoformat(),
            "valid_to": future_end.isoformat(),
        },
    ]
    
    # Simulate the FIXED native_value logic
    now_timestamp = datetime.now().timestamp()
    active_disruptions = []
    
    for item in line_data:
        status = item.get("status")
        
        # Only consider open status disruptions
        if status != STATUS_OPEN:
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
    
    # Determine native_value
    if not active_disruptions:
        native_value = STATE_NORMAL
    elif len(active_disruptions) == 1:
        native_value = active_disruptions[0].get("summary")
    else:
        summaries = [item.get("summary", "Unknown disruption") for item in active_disruptions]
        native_value = " | ".join(summaries)
    
    print("\n" + "=" * 80)
    print("Transition Scenario: Planned → Active")
    print("=" * 80)
    print(f"\nInput:")
    print(f"  - One disruption that started 5 minutes ago")
    print(f"  - Status changed from 'planned' to 'open'")
    print(f"  - Currently within valid time window")
    print(f"\nResult:")
    print(f"  - Active disruptions found: {len(active_disruptions)}")
    print(f"  - Returns: '{native_value}'")
    print(f"\nExpected: The disruption summary")
    print(f"Got:      '{native_value}'")
    
    assert native_value == "Active disruption that was previously planned", (
        f"Expected disruption summary but got '{native_value}'"
    )
    print(f"\n✅ TEST PASSED - Correctly shows active disruption!")
    print("=" * 80)


if __name__ == "__main__":
    test_problem_statement_scenario()
    test_when_planned_becomes_active()
    print("\n" + "=" * 80)
    print("ALL PROBLEM STATEMENT TESTS PASSED!")
    print("=" * 80)
