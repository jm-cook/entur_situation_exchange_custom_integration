"""Investigate the relationship between authority, operator, and lines."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def investigate_authority_vs_operator():
    """Check what authority really means and how to get the transport authority name."""
    
    # Check both SKY and SOF authorities with full details
    authorities_to_check = [
        ("SKY:Authority:SKY", "Skyss (Hordaland) - Expected"),
        ("SOF:Authority:1", "Kringom (Sogn og Fjordane) - Expected"),
    ]
    
    for auth_id, expected in authorities_to_check:
        # Get full authority details including lines
        query = f"""
        query {{
          authority(id: "{auth_id}") {{
            id
            name
            description
            url
            timezone
            lines {{
              id
              name
              publicCode
              transportMode
              authority {{
                id
                name
              }}
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
                
                print(f"\n{'=' * 100}")
                print(f"AUTHORITY: {auth_id}")
                print(f"EXPECTED: {expected}")
                print('=' * 100)
                
                print(f"\n📋 Authority Fields:")
                print(f"  id:          {authority.get('id', 'N/A')}")
                print(f"  name:        {authority.get('name', 'N/A')}")
                print(f"  description: {authority.get('description', 'N/A')}")
                print(f"  url:         {authority.get('url', 'N/A')}")
                
                lines = authority.get("lines", [])
                print(f"\n📍 Lines: {len(lines)} found")
                
                if lines:
                    print(f"\nSample lines (first 5):")
                    for line in lines[:5]:
                        line_code = line.get("publicCode", "?")
                        line_name = line.get("name", "?")
                        mode = line.get("transportMode", "?")
                        
                        # Check what authority and operator say
                        line_authority = line.get("authority", {})
                        line_operator = line.get("operator", {})
                        
                        print(f"\n  Line {line_code}: {line_name} ({mode})")
                        print(f"    Line's authority: {line_authority.get('name', 'N/A')} (ID: {line_authority.get('id', 'N/A')})")
                        print(f"    Line's operator:  {line_operator.get('name', 'N/A')} (ID: {line_operator.get('id', 'N/A')})")
                    
                    # Analyze the pattern
                    print(f"\n\n🔍 ANALYSIS:")
                    authority_names = set()
                    operator_names = set()
                    
                    for line in lines:
                        line_auth = line.get("authority", {})
                        line_op = line.get("operator", {})
                        
                        if line_auth.get("name"):
                            authority_names.add(line_auth.get("name"))
                        if line_op.get("name"):
                            operator_names.add(line_op.get("name"))
                    
                    print(f"  Unique authority names from lines: {authority_names}")
                    print(f"  Unique operator names from lines:  {operator_names}")
                    
                    print(f"\n  INTERPRETATION:")
                    if len(authority_names) == 1:
                        auth_name = list(authority_names)[0]
                        print(f"    • All lines have same authority: '{auth_name}'")
                        print(f"    • This is likely the TRANSPORT AUTHORITY (regional admin)")
                    if len(operator_names) > 1:
                        print(f"    • Multiple operators: {operator_names}")
                        print(f"    • These are the OPERATING COMPANIES running the services")


async def check_what_authorities_query_returns():
    """Check what the authorities list query actually represents."""
    
    print(f"\n\n{'=' * 100}")
    print("WHAT DOES THE 'authorities' QUERY REPRESENT?")
    print('=' * 100)
    
    query = """
    query {
      authorities {
        id
        name
        description
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
            
            # Look at SOF entries
            print("\nSOF Codespace Authorities:")
            print("-" * 100)
            
            sof_auths = [a for a in authorities if a.get("id", "").startswith("SOF:")]
            
            for auth in sof_auths:
                print(f"\nID:          {auth.get('id')}")
                print(f"Name:        {auth.get('name')}")
                print(f"Description: {auth.get('description', 'N/A')}")
            
            print(f"\n\n💡 HYPOTHESIS:")
            print("The 'name' field in the authorities list might be:")
            print("  1. The primary operator for that authority/region")
            print("  2. A legacy/incorrect field")
            print("  3. Not the regional transport authority name we need")
            print("\nWe need to find where the actual 'Kringom' name is stored...")


if __name__ == "__main__":
    asyncio.run(investigate_authority_vs_operator())
    asyncio.run(check_what_authorities_query_returns())
