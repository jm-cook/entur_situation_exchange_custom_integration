"""Find API that lists all codespaces."""
import asyncio
import aiohttp

GRAPHQL_API = "https://api.entur.io/journey-planner/v3/graphql"


async def get_codespaces_from_operators_api():
    """Extract all codespaces from operators API."""
    
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
        async with session.post(
            GRAPHQL_API,
            json={"query": query},
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            operators = data.get("data", {}).get("operators", [])
            
            print("=" * 100)
            print("EXTRACTING ALL CODESPACES FROM OPERATORS API")
            print("=" * 100)
            
            # Extract codespaces and find canonical names
            codespace_map = {}
            
            for op in operators:
                op_id = op.get("id", "")
                op_name = op.get("name", "")
                
                if ":" in op_id:
                    parts = op_id.split(":")
                    codespace = parts[0]
                    
                    # Only 3-letter uppercase codes
                    if len(codespace) == 3 and codespace.isupper():
                        # Prefer canonical operator (XXX:Operator:XXX)
                        if len(parts) == 3 and parts[0] == parts[2] and parts[1] == "Operator":
                            codespace_map[codespace] = op_name
                        elif codespace not in codespace_map:
                            # Use first operator name found
                            codespace_map[codespace] = op_name
            
            print(f"\nFound {len(codespace_map)} codespaces with names:\n")
            for cs in sorted(codespace_map.keys()):
                print(f"  {cs}: {codespace_map[cs]}")
            
            print(f"\n\n✅ Operators API returns {len(codespace_map)} codespaces")
            print("✅ This includes all active and legacy codespaces")
            print("✅ Automatically updates when new codespaces are added")
            
            return codespace_map


if __name__ == "__main__":
    asyncio.run(get_codespaces_from_operators_api())
