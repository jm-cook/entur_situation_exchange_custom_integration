"""Investigate operator duplicates in detail to understand the differences."""
import asyncio
import aiohttp
import async_timeout

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def investigate_duplicates_in_depth():
    """Get detailed information about duplicate operators."""
    
    # Query for more details including lines
    query = """
    query {
      authorities {
        id
        name
        lines {
          id
          name
          publicCode
          transportMode
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "homeassistant-entur-sx",
    }
    
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(30):
            async with session.post(
                API_GRAPHQL_URL,
                json={"query": query},
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                authorities = data.get("data", {}).get("authorities", [])
                
                # Filter to those with :Authority: pattern
                filtered = []
                for auth in authorities:
                    auth_id = auth.get("id", "")
                    if ":Authority:" in auth_id:
                        auth["line_count"] = len(auth.get("lines", []))
                        filtered.append(auth)
                
                # Group by name
                by_name = {}
                for auth in filtered:
                    name = auth.get("name", "")
                    if name not in by_name:
                        by_name[name] = []
                    by_name[name].append(auth)
                
                # Analyze duplicates
                print("=" * 100)
                print("DETAILED DUPLICATE ANALYSIS")
                print("=" * 100)
                
                for name, auths in sorted(by_name.items()):
                    if len(auths) > 1:
                        print(f"\n{'=' * 100}")
                        print(f"OPERATOR: {name} ({len(auths)} entries)")
                        print(f"{'=' * 100}")
                        
                        for i, auth in enumerate(auths, 1):
                            auth_id = auth.get("id", "")
                            lines = auth.get("lines", [])
                            line_count = len(lines)
                            
                            # Parse ID format
                            parts = auth_id.split(":")
                            prefix = parts[0] if len(parts) > 0 else ""
                            suffix = parts[2] if len(parts) > 2 else ""
                            is_canonical = prefix == suffix if len(parts) == 3 else False
                            
                            print(f"\n  Entry {i}: {auth_id}")
                            print(f"    Canonical: {'YES ✓' if is_canonical else 'NO'}")
                            print(f"    Lines: {line_count}")
                            
                            if line_count > 0:
                                # Show sample lines
                                sample_lines = lines[:5]
                                print(f"    Sample lines:")
                                for line in sample_lines:
                                    line_id = line.get("id", "")
                                    line_name = line.get("name", "")
                                    public_code = line.get("publicCode", "")
                                    mode = line.get("transportMode", "")
                                    print(f"      - {public_code}: {line_name} ({mode}) [{line_id}]")
                                
                                if line_count > 5:
                                    print(f"      ... and {line_count - 5} more")
                            else:
                                print(f"    ⚠️  NO LINES FOUND")
                        
                        # Recommendation
                        print(f"\n  ANALYSIS:")
                        
                        # Check if any have lines
                        with_lines = [a for a in auths if len(a.get("lines", [])) > 0]
                        without_lines = [a for a in auths if len(a.get("lines", [])) == 0]
                        
                        if with_lines and without_lines:
                            print(f"    ⚠️  Some entries have lines, some don't!")
                            print(f"    Entries WITH lines: {[a['id'] for a in with_lines]}")
                            print(f"    Entries WITHOUT lines: {[a['id'] for a in without_lines]}")
                            print(f"    RECOMMENDATION: Keep entries with lines, remove empty ones")
                        
                        # Check if lines differ
                        if len(with_lines) > 1:
                            line_ids_by_auth = {}
                            for auth in with_lines:
                                auth_id = auth.get("id", "")
                                line_ids = set(line.get("id", "") for line in auth.get("lines", []))
                                line_ids_by_auth[auth_id] = line_ids
                            
                            # Compare
                            all_same = len(set(frozenset(ids) for ids in line_ids_by_auth.values())) == 1
                            
                            if all_same:
                                print(f"    ✓ All entries have SAME lines - safe to dedupe")
                                # Suggest canonical
                                canonical = [a for a in auths if a['id'].split(":")[0] == a['id'].split(":")[2]]
                                if canonical:
                                    print(f"    RECOMMENDATION: Keep canonical {canonical[0]['id']}")
                            else:
                                print(f"    ⚠️  Entries have DIFFERENT lines!")
                                for auth_id, line_ids in line_ids_by_auth.items():
                                    print(f"      {auth_id}: {len(line_ids)} lines")
                                print(f"    RECOMMENDATION: Keep ALL entries - they serve different lines!")
                
                # Summary
                print(f"\n\n{'=' * 100}")
                print("SUMMARY")
                print(f"{'=' * 100}")
                
                duplicates = {name: auths for name, auths in by_name.items() if len(auths) > 1}
                
                safe_to_dedupe = []
                unsafe_to_dedupe = []
                
                for name, auths in duplicates.items():
                    with_lines = [a for a in auths if len(a.get("lines", [])) > 0]
                    
                    if len(with_lines) <= 1:
                        # Only one has lines, or none have lines
                        safe_to_dedupe.append(name)
                    else:
                        # Multiple have lines - need to check if they're the same
                        line_ids_by_auth = {}
                        for auth in with_lines:
                            auth_id = auth.get("id", "")
                            line_ids = frozenset(line.get("id", "") for line in auth.get("lines", []))
                            line_ids_by_auth[auth_id] = line_ids
                        
                        all_same = len(set(line_ids_by_auth.values())) == 1
                        
                        if all_same:
                            safe_to_dedupe.append(name)
                        else:
                            unsafe_to_dedupe.append(name)
                
                print(f"\nSafe to deduplicate ({len(safe_to_dedupe)}):")
                for name in safe_to_dedupe:
                    print(f"  ✓ {name}")
                
                if unsafe_to_dedupe:
                    print(f"\n⚠️  UNSAFE to deduplicate ({len(unsafe_to_dedupe)}):")
                    for name in unsafe_to_dedupe:
                        print(f"  ✗ {name} - Different lines per authority ID!")


if __name__ == "__main__":
    asyncio.run(investigate_duplicates_in_depth())
