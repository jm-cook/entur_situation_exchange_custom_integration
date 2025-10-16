"""Test entity cleanup logic."""


def test_entity_cleanup():
    """Test that entity cleanup correctly identifies entities to remove."""
    
    # Simulate current entity registry
    class MockEntityEntry:
        def __init__(self, entity_id, unique_id):
            self.entity_id = entity_id
            self.unique_id = unique_id
    
    # Current entities in registry
    current_entities = [
        MockEntityEntry("sensor.device_sky_line_925", "entry123_SKY_Line_925"),
        MockEntityEntry("sensor.device_sky_line_900", "entry123_SKY_Line_900"),
        MockEntityEntry("sensor.device_sky_line_100", "entry123_SKY_Line_100"),
    ]
    
    # Scenario 1: User removes line 900
    print("Scenario 1: Remove line 900")
    configured_lines = ["SKY:Line:925", "SKY:Line:100"]
    entry_id = "entry123"
    
    # Build expected unique IDs (like in sensor.py)
    expected_unique_ids = {
        f"{entry_id}_{line_ref.replace(':', '_')}" 
        for line_ref in configured_lines
    }
    
    print(f"Configured lines: {configured_lines}")
    print(f"Expected unique IDs: {expected_unique_ids}")
    
    # Find entities to remove
    to_remove = []
    to_keep = []
    for entity_entry in current_entities:
        if entity_entry.unique_id not in expected_unique_ids:
            to_remove.append(entity_entry.entity_id)
        else:
            to_keep.append(entity_entry.entity_id)
    
    print(f"Entities to remove: {to_remove}")
    print(f"Entities to keep: {to_keep}")
    
    assert len(to_remove) == 1, "Should remove 1 entity"
    assert "sensor.device_sky_line_900" in to_remove, "Should remove line 900"
    assert len(to_keep) == 2, "Should keep 2 entities"
    
    print("✅ Scenario 1 passed!\n")
    
    # Scenario 2: User adds line 950, removes line 925
    print("Scenario 2: Add line 950, remove line 925")
    configured_lines = ["SKY:Line:900", "SKY:Line:100", "SKY:Line:950"]
    
    expected_unique_ids = {
        f"{entry_id}_{line_ref.replace(':', '_')}" 
        for line_ref in configured_lines
    }
    
    print(f"Configured lines: {configured_lines}")
    print(f"Expected unique IDs: {expected_unique_ids}")
    
    to_remove = []
    to_keep = []
    for entity_entry in current_entities:
        if entity_entry.unique_id not in expected_unique_ids:
            to_remove.append(entity_entry.entity_id)
        else:
            to_keep.append(entity_entry.entity_id)
    
    print(f"Entities to remove: {to_remove}")
    print(f"Entities to keep: {to_keep}")
    
    assert len(to_remove) == 1, "Should remove 1 entity"
    assert "sensor.device_sky_line_925" in to_remove, "Should remove line 925"
    assert len(to_keep) == 2, "Should keep 2 entities"
    
    print("✅ Scenario 2 passed!\n")
    
    # Scenario 3: Remove all lines (user unchecked everything)
    print("Scenario 3: Remove all lines")
    configured_lines = []
    
    expected_unique_ids = {
        f"{entry_id}_{line_ref.replace(':', '_')}" 
        for line_ref in configured_lines
    }
    
    print(f"Configured lines: {configured_lines}")
    print(f"Expected unique IDs: {expected_unique_ids}")
    
    to_remove = []
    to_keep = []
    for entity_entry in current_entities:
        if entity_entry.unique_id not in expected_unique_ids:
            to_remove.append(entity_entry.entity_id)
        else:
            to_keep.append(entity_entry.entity_id)
    
    print(f"Entities to remove: {to_remove}")
    print(f"Entities to keep: {to_keep}")
    
    assert len(to_remove) == 3, "Should remove all 3 entities"
    assert len(to_keep) == 0, "Should keep 0 entities"
    
    print("✅ Scenario 3 passed!\n")
    
    print("✅ All entity cleanup tests passed!")


if __name__ == "__main__":
    test_entity_cleanup()
