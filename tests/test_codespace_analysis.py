"""Analyze operators using official codespace documentation."""
import asyncio
import aiohttp

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"

# Official codespace mapping from Entur documentation (2025-01-03)
# Source: https://enturas.atlassian.net/wiki/spaces/PUBLIC/pages/637370434/List+of+current+Codespaces
CODESPACE_TO_OPERATOR = {
    "AKT": "Agder kollektivtrafikk",
    "ATB": "AtB (Trøndelag)",
    "BRA": "Brakar (Buskerud)",
    "FIN": "Snelandia (Finnmark)",
    "FLB": "Flåmsbana",  # Part of Vy-group now
    "FLT": "Flytoget",
    "GOA": "Go Ahead",
    "INN": "Innlandet",
    "KOL": "Kolumbus (Rogaland)",
    "MOR": "Fram (Møre og Romsdal)",
    "NOR": "Nordland fylkeskommune",
    "OST": "Østfold kollektivtrafikk",
    "RUT": "Ruter (Oslo & Akershus)",
    "SJN": "SJ NORD",
    "SJV": "SJ",
    "SKY": "Skyss (Hordaland)",
    "SOF": "Kringom (Sogn og Fjordane)",  # Different from SKY!
    "TEL": "Farte (Telemark)",
    "TID": "Tide",
    "TRO": "Troms fylkestrafikk",
    "UNI": "Unibuss",
    "VKT": "VKT (Vestfold)",
    "VYG": "Vy-group",  # Parent company, replaces NSB/GJB/FLB/TAG
    "VYB": "Vy Buss AB",
    "VYX": "Vy Buss AS",
}


async def analyze_with_codespaces():
    """Analyze operators based on official codespace documentation."""
    
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
            
            print("=" * 100)
            print("ANALYZING OPERATORS WITH OFFICIAL CODESPACE DOCUMENTATION")
            print("=" * 100)
            
            # Group by name to find "duplicates"
            by_name = {}
            for auth in authorities:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                
                if ":Authority:" not in auth_id:
                    continue
                    
                if auth_name not in by_name:
                    by_name[auth_name] = []
                by_name[auth_name].append(auth_id)
            
            # Analyze cases with multiple IDs
            duplicates = {name: ids for name, ids in by_name.items() if len(ids) > 1}
            
            print(f"\nFound {len(duplicates)} operator names with multiple authority IDs:\n")
            
            for name in sorted(duplicates.keys()):
                ids = duplicates[name]
                print(f"\n{'=' * 80}")
                print(f"OPERATOR NAME IN API: '{name}' ({len(ids)} authority IDs)")
                print('=' * 80)
                
                # Analyze each authority ID
                for auth_id in ids:
                    parts = auth_id.split(":")
                    codespace = parts[0] if len(parts) >= 1 else "?"
                    suffix = parts[-1] if len(parts) >= 3 else "?"
                    
                    # Look up official operator for this codespace
                    official_operator = CODESPACE_TO_OPERATOR.get(codespace, "UNKNOWN")
                    
                    # Check format
                    is_canonical = len(parts) == 3 and parts[0] == parts[2]
                    
                    print(f"\n  Authority ID: {auth_id}")
                    print(f"    Codespace: {codespace}")
                    print(f"    Official Operator: {official_operator}")
                    print(f"    Format: {'Canonical' if is_canonical else 'Non-canonical'}")
                    
                    # Analysis
                    if official_operator == "UNKNOWN":
                        print(f"    ⚠️  WARNING: Codespace not found in official documentation!")
                    elif official_operator.lower() not in name.lower() and name.lower() not in official_operator.lower():
                        print(f"    🔴 MISMATCH: API name '{name}' doesn't match official operator '{official_operator}'")
                        print(f"       This suggests the API name is incorrect or misleading!")
                    else:
                        print(f"    ✅ MATCH: API name matches official codespace operator")
            
            print("\n\n" + "=" * 100)
            print("ANALYSIS & RECOMMENDATIONS")
            print("=" * 100)
            
            for name in sorted(duplicates.keys()):
                ids = duplicates[name]
                print(f"\n{name}:")
                print("-" * 80)
                
                # Analyze codespaces
                codespace_info = []
                for auth_id in ids:
                    parts = auth_id.split(":")
                    codespace = parts[0]
                    official = CODESPACE_TO_OPERATOR.get(codespace, "UNKNOWN")
                    is_canonical = len(parts) == 3 and parts[0] == parts[2]
                    
                    name_matches = official.lower() in name.lower() or name.lower() in official.lower()
                    
                    codespace_info.append({
                        "id": auth_id,
                        "codespace": codespace,
                        "official": official,
                        "canonical": is_canonical,
                        "name_matches": name_matches
                    })
                
                # Check if codespaces point to different operators
                unique_officials = set(info["official"] for info in codespace_info if info["official"] != "UNKNOWN")
                
                if len(unique_officials) > 1:
                    print(f"  🔴 DIFFERENT OPERATORS! The codespaces belong to:")
                    for official in unique_officials:
                        print(f"     - {official}")
                    print(f"  ")
                    print(f"  ❌ DO NOT DEDUPLICATE - These are separate companies/regions!")
                    print(f"  💡 Recommendation: Display codespace or region in UI to distinguish them")
                    print()
                    for info in codespace_info:
                        print(f"     {info['id']}")
                        print(f"       Should display as: \"{info['official']} ({info['codespace']})\"")
                else:
                    print(f"  ✅ SAME OPERATOR - Safe to deduplicate")
                    # Find preferred ID
                    preferred = None
                    for info in codespace_info:
                        if info["canonical"] and info["name_matches"]:
                            preferred = info["id"]
                            break
                    if not preferred:
                        preferred = codespace_info[0]["id"]
                    
                    print(f"     KEEP: {preferred}")
                    for info in codespace_info:
                        if info["id"] != preferred:
                            print(f"     REMOVE: {info['id']}")
            
            print("\n\n" + "=" * 100)
            print("SUMMARY")
            print("=" * 100)
            print("\nKey Findings:")
            print("• Some 'duplicate' names actually represent different operators in different regions")
            print("• The API name field can be misleading - codespace is the source of truth")
            print("• Example: 'Skyss' name might include both SKY (Skyss) and SOF (Kringom) codespaces")
            print("\nRecommendation:")
            print("• DO NOT deduplicate by name alone")
            print("• Use codespace to determine if truly the same operator")
            print("• Consider adding region/codespace info to operator display names")
            print("=" * 100)


if __name__ == "__main__":
    asyncio.run(analyze_with_codespaces())
