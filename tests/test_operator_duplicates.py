"""Test to investigate duplicate operators in the API."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"

async def investigate_operators():
    """Fetch and analyze all authorities to find duplicates."""
    
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
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            API_GRAPHQL_URL,
            json={"query": query},
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            authorities = data.get("data", {}).get("authorities", [])
            
            print(f"\nTotal authorities: {len(authorities)}")
            print("=" * 80)
            
            # Group by name to find duplicates
            by_name = {}
            for auth in authorities:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                
                if auth_name not in by_name:
                    by_name[auth_name] = []
                by_name[auth_name].append(auth_id)
            
            # Find duplicates
            print("\nAUTHORITIES WITH MULTIPLE IDs:")
            print("=" * 80)
            
            for name, ids in sorted(by_name.items()):
                if len(ids) > 1:
                    print(f"\n{name}:")
                    for auth_id in ids:
                        # Check if it has :Authority: pattern
                        has_pattern = ":Authority:" in auth_id
                        print(f"  - {auth_id} {'✓ (has :Authority:)' if has_pattern else '✗ (no pattern)'}")
            
            # Check Skyss specifically
            print("\n\nSKYSS ENTRIES SPECIFICALLY:")
            print("=" * 80)
            
            skyss_entries = [auth for auth in authorities if "skyss" in auth.get("name", "").lower()]
            for entry in skyss_entries:
                print(f"ID: {entry.get('id')}")
                print(f"Name: {entry.get('name')}")
                print(f"Has :Authority: pattern: {':Authority:' in entry.get('id', '')}")
                print("-" * 40)
            
            # Show what we WOULD include with current filter
            print("\n\nWHAT CURRENT FILTER INCLUDES:")
            print("=" * 80)
            
            filtered = []
            for auth in authorities:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                
                if not auth_id or not auth_name:
                    continue
                
                if ":Authority:" not in auth_id:
                    continue
                
                if "AMBU" in auth_name.upper() or auth_id.startswith("MOR:Authority:AM"):
                    continue
                
                filtered.append((auth_id, auth_name))
            
            print(f"Total included: {len(filtered)}")
            print("\nDuplicates by name:")
            
            name_counts = {}
            for auth_id, auth_name in filtered:
                if auth_name not in name_counts:
                    name_counts[auth_name] = []
                name_counts[auth_name].append(auth_id)
            
            for name, ids in sorted(name_counts.items()):
                if len(ids) > 1:
                    print(f"\n{name} ({len(ids)} entries):")
                    for auth_id in ids:
                        print(f"  - {auth_id}")


if __name__ == "__main__":
    asyncio.run(investigate_operators())
