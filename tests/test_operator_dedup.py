"""Test the duplicate operator filtering logic."""
import asyncio
import aiohttp
import async_timeout

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def async_get_operators_with_dedup(session):
    """Fetch operators with deduplication logic (copied from api.py)."""
    query = """
    query {
      authorities {
        id
        name
      }
    }
    """

    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "homeassistant-entur-sx",
    }

    async with async_timeout.timeout(10):
        async with session.post(
            API_GRAPHQL_URL,
            json={"query": query},
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()

            operators = {}
            authorities = data.get("data", {}).get("authorities", [])
            
            # Track names to detect duplicates
            seen_names = {}
            
            for authority in authorities:
                authority_id = authority.get("id", "")
                authority_name = authority.get("name", "")
                
                if not authority_id or not authority_name:
                    continue
                
                # Filter out non-transit operators
                if ":Authority:" not in authority_id:
                    continue
                
                # Skip known non-transit authorities
                if "AMBU" in authority_name.upper() or authority_id.startswith("MOR:Authority:AM"):
                    continue
                
                # Handle duplicates by preferring canonical IDs
                # Canonical format: "XXX:Authority:XXX" (prefix matches suffix)
                if authority_name in seen_names:
                    existing_id = seen_names[authority_name]
                    
                    # Check if new ID is more canonical
                    parts = authority_id.split(":")
                    if len(parts) == 3 and parts[0] == parts[2]:
                        # New ID is canonical (prefix matches suffix)
                        print(f"  Replacing {existing_id} with canonical ID {authority_id} for {authority_name}")
                        del operators[existing_id]
                        operators[authority_id] = authority_name
                        seen_names[authority_name] = authority_id
                    else:
                        # Keep existing ID, skip this one
                        print(f"  Skipping duplicate {authority_id} (keeping {existing_id}) for {authority_name}")
                        continue
                else:
                    # First time seeing this name
                    operators[authority_id] = authority_name
                    seen_names[authority_name] = authority_id

            return operators


async def test_operator_deduplication():
    """Test that operators are deduplicated correctly."""
    
    async with aiohttp.ClientSession() as session:
        operators = await async_get_operators_with_dedup(session)
        
        print(f"\nTotal operators after filtering: {len(operators)}")
        print("=" * 80)
        
        # Count names to check for duplicates
        names = list(operators.values())
        name_counts = {}
        for name in names:
            name_counts[name] = name_counts.get(name, 0) + 1
        
        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        
        if duplicates:
            print("\n❌ DUPLICATES FOUND:")
            for name, count in duplicates.items():
                print(f"  {name}: {count} times")
                # Show which IDs
                matching_ids = [id for id, n in operators.items() if n == name]
                for id in matching_ids:
                    print(f"    - {id}")
        else:
            print("\n✅ NO DUPLICATES - Each operator appears exactly once!")
        
        print("\n\nFULL OPERATOR LIST:")
        print("=" * 80)
        
        for auth_id, auth_name in sorted(operators.items(), key=lambda x: x[1]):
            # Check if canonical format
            parts = auth_id.split(":")
            is_canonical = len(parts) == 3 and parts[0] == parts[2]
            marker = "✓" if is_canonical else "?"
            
            # Extract display code for label
            code = parts[-1] if len(parts) == 3 else auth_id
            
            print(f"{marker} {auth_name} ({code}) -> {auth_id}")
        
        # Specific checks
        print("\n\nSPECIFIC OPERATOR CHECKS:")
        print("=" * 80)
        
        # Check Skyss
        skyss_ids = [id for id, name in operators.items() if name == "Skyss"]
        if len(skyss_ids) == 1:
            print(f"✅ Skyss: Only 1 entry -> {skyss_ids[0]}")
        else:
            print(f"❌ Skyss: {len(skyss_ids)} entries -> {skyss_ids}")
        
        # Check Kolumbus
        kolumbus_ids = [id for id, name in operators.items() if name == "Kolumbus"]
        if len(kolumbus_ids) == 1:
            print(f"✅ Kolumbus: Only 1 entry -> {kolumbus_ids[0]}")
        else:
            print(f"❌ Kolumbus: {len(kolumbus_ids)} entries -> {kolumbus_ids}")
        
        # Check Vy
        vy_ids = [id for id, name in operators.items() if name == "Vy"]
        if len(vy_ids) == 1:
            print(f"✅ Vy: Only 1 entry -> {vy_ids[0]}")
        else:
            print(f"❌ Vy: {len(vy_ids)} entries -> {vy_ids}")
        
        print("\n" + "=" * 80)
        if not duplicates:
            print("✅ ALL TESTS PASSED - No duplicate operator names!")
        else:
            print("❌ TESTS FAILED - Duplicates still exist")


if __name__ == "__main__":
    asyncio.run(test_operator_deduplication())
