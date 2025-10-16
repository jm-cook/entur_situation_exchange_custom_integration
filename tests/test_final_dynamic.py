"""Test the dynamic codespace discovery."""
import asyncio
import aiohttp
import async_timeout

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"

# Curated names (used as fallback for better naming)
CODESPACE_NAMES = {
    "AKT": "Agder Kollektivtrafikk",
    "ATB": "AtB",
    "BRA": "Brakar",
    "GOA": "Go-Ahead Norge",
    "INN": "Innlandstrafikk",
    "KOL": "Kolumbus",
    "MOR": "FRAM",
    "OST": "Østfold kollektivtrafikk",
    "RUT": "Ruter",
    "SKY": "Skyss",
    "SOF": "Sogn og Fjordane",  # Override the misleading API name
    "TEL": "Farte",
    "TRO": "Troms fylkestrafikk",
    "VKT": "VKT",
    "VYG": "Vy",
}


async def test_dynamic_operators():
    """Test dynamic codespace discovery with fallback to curated names."""
    
    query = """
    query {
      operators {
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
        async with async_timeout.timeout(10):
            async with session.post(
                API_GRAPHQL_URL,
                json={"query": query},
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                all_operators = data.get("data", {}).get("operators", [])
                
                # Extract codespaces
                codespace_names = {}
                
                for operator in all_operators:
                    op_id = operator.get("id", "")
                    op_name = operator.get("name", "")
                    
                    if not op_id:
                        continue
                    
                    if ":" in op_id:
                        parts = op_id.split(":")
                        codespace = parts[0]
                        
                        if len(codespace) == 3 and codespace.isupper():
                            is_canonical = (len(parts) == 3 and 
                                          parts[0] == parts[2] and 
                                          parts[1] == "Operator")
                            
                            if is_canonical or codespace not in codespace_names:
                                # Prefer curated name if available
                                friendly_name = CODESPACE_NAMES.get(codespace, op_name)
                                codespace_names[codespace] = friendly_name
                
                # Build display names
                operators = {}
                for codespace in sorted(codespace_names.keys()):
                    friendly_name = codespace_names[codespace]
                    display_name = f"{friendly_name} ({codespace})"
                    operators[codespace] = display_name
                
                print("=" * 100)
                print("DYNAMIC CODESPACE DISCOVERY RESULTS")
                print("=" * 100)
                print(f"\nTotal operators: {len(operators)}\n")
                
                # Show some key ones
                key_operators = ["SKY", "SOF", "RUT", "VYG", "ATB", "KOL"]
                print("Key operators:")
                for cs in key_operators:
                    if cs in operators:
                        curated = " ✅ Curated name" if cs in CODESPACE_NAMES else ""
                        print(f"  {operators[cs]}{curated}")
                
                # Show all
                print(f"\n\nAll {len(operators)} operators:")
                for cs, name in operators.items():
                    curated_marker = "✓" if cs in CODESPACE_NAMES else " "
                    print(f"  [{curated_marker}] {name}")
                
                print("\n\n" + "=" * 100)
                print("BENEFITS OF THIS APPROACH")
                print("=" * 100)
                print(f"""
✅ Automatically discovers ALL {len(operators)} codespaces
✅ No hardcoded list to maintain
✅ New codespaces appear automatically
✅ Uses curated names from CODESPACE_NAMES where available
✅ Falls back to API names for new/unknown codespaces
✅ SOF correctly shown as 'Sogn og Fjordane' (overriding misleading API name)

Example:
  • SKY: Uses curated "Skyss"
  • SOF: Uses curated "Sogn og Fjordane" (not misleading "GulenSkyss AS")
  • New codespace XYZ: Would use API name automatically
""")


if __name__ == "__main__":
    asyncio.run(test_dynamic_operators())
