"""Test if we can get better operator names from lines."""
import asyncio
import aiohttp

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def check_lines_for_operators():
    """Check if lines give us better operator names."""
    
    # The "duplicate" Skyss operators
    operators_to_check = [
        ("SOF:Authority:1", "Kringom (Sogn og Fjordane)"),
        ("SKY:Authority:SKY", "Skyss (Hordaland)"),
        ("SOF:Authority:17", "Kringom (Sogn og Fjordane)"),
    ]
    
    for auth_id, expected_name in operators_to_check:
        query = f"""
        query {{
          authority(id: "{auth_id}") {{
            id
            name
            lines {{
              id
              name
              publicCode
              transportMode
              operator {{
                id
                name
              }}
            }}
          }}
        }}
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
                
                authority = data.get("data", {}).get("authority", {})
                lines = authority.get("lines", [])
                
                print(f"\n{'=' * 80}")
                print(f"Authority: {auth_id}")
                print(f"Expected operator: {expected_name}")
                print(f"API authority name: {authority.get('name', 'N/A')}")
                print(f"Number of lines: {len(lines)}")
                print('=' * 80)
                
                if lines:
                    print("\nChecking operator names from first 5 lines:")
                    for line in lines[:5]:
                        operator = line.get("operator", {})
                        print(f"  Line {line.get('publicCode', '?')}: operator = {operator.get('name', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(check_lines_for_operators())
