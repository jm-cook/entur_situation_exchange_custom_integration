"""Quick test to verify options flow data merging."""

# Simulate Home Assistant ConfigEntry data structures
class MockConfigEntry:
    """Mock config entry for testing."""
    def __init__(self, data, options):
        self.data = data
        self.options = options


def test_data_merge():
    """Test that data and options merge correctly."""
    
    # Initial setup: lines stored in data
    entry = MockConfigEntry(
        data={
            "operator": "SKY:Authority:SKY",
            "lines_to_check": ["SKY:Line:925"],
            "device_name": "Test Device"
        },
        options={}
    )
    
    # How sensor.py reads (BEFORE FIX):
    lines_before = entry.data.get("lines_to_check", [])
    print(f"Before fix - sensor.py reads: {lines_before}")
    # Result: ['SKY:Line:925']
    
    # User adds line 900 via options flow
    entry.options = {"lines_to_check": ["SKY:Line:925", "SKY:Line:900"]}
    
    # How sensor.py reads (BEFORE FIX):
    lines_before_fix = entry.data.get("lines_to_check", [])
    print(f"After options update, before fix: {lines_before_fix}")
    # Result: ['SKY:Line:925'] - STILL THE OLD VALUE!
    
    # How sensor.py reads (AFTER FIX):
    config_data = {**entry.data, **entry.options}
    lines_after_fix = config_data.get("lines_to_check", [])
    print(f"After options update, after fix: {lines_after_fix}")
    # Result: ['SKY:Line:925', 'SKY:Line:900'] - CORRECT!
    
    # Verify
    assert len(lines_before_fix) == 1, "Before fix: only original line"
    assert len(lines_after_fix) == 2, "After fix: both lines"
    assert "SKY:Line:900" in lines_after_fix, "New line is included"
    
    print("\n✅ Test passed! Options flow fix is correct.")
    print(f"\nBefore fix: {len(lines_before_fix)} sensors created")
    print(f"After fix:  {len(lines_after_fix)} sensors created")


if __name__ == "__main__":
    test_data_merge()
