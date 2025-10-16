"""Deep dive into what the API actually returns for each authority."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def investigate_api_response():
    """Get the raw API response to see exactly what Entur returns."""
    
    # The three "Skyss" authority IDs
    authorities_to_check = [
        "SOF:Authority:1",
        "SKY:Authority:SKY",
        "SOF:Authority:17",
    ]
    
    for authority_id in authorities_to_check:
        query = f"""
        query {{
          authority(id: "{authority_id}") {{
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
                
                print(f"\n{'=' * 100}")
                print(f"AUTHORITY ID: {authority_id}")
                print('=' * 100)
                
                authority = data.get("data", {}).get("authority", {})
                
                print("\n📋 RAW API RESPONSE FOR AUTHORITY:")
                print(json.dumps(authority, indent=2, ensure_ascii=False))
                
                # Extract key fields
                api_name = authority.get("name", "N/A")
                api_desc = authority.get("description", "N/A")
                api_url = authority.get("url", "N/A")
                
                print(f"\n\n🔍 EXTRACTED FIELDS:")
                print(f"  ID: {authority_id}")
                print(f"  Name from API: '{api_name}'")
                print(f"  Description: '{api_desc}'")
                print(f"  URL: '{api_url}'")
                
                # Check codespace
                codespace = authority_id.split(":")[0]
                print(f"\n  Codespace: {codespace}")
                
                if codespace == "SOF":
                    print(f"  ⚠️  According to Entur docs, SOF = Kringom (Sogn og Fjordane)")
                    print(f"  ⚠️  But API returns name: '{api_name}'")
                    if api_name != "Kringom":
                        print(f"  🔴 MISMATCH! API name does not match official codespace operator!")
                elif codespace == "SKY":
                    print(f"  ✅ According to Entur docs, SKY = Skyss (Hordaland)")
                    print(f"  ✅ API returns name: '{api_name}' - CORRECT")
                
                # Check operators from lines
                lines = authority.get("lines", [])
                print(f"\n  Number of lines: {len(lines)}")
                
                if lines:
                    print(f"\n  📍 Checking operator names from first 10 lines:")
                    operator_names = set()
                    for line in lines[:10]:
                        operator = line.get("operator")
                        if operator:
                            op_name = operator.get("name", "Unknown")
                            operator_names.add(op_name)
                            print(f"    Line {line.get('publicCode', '?'):6} ({line.get('transportMode', '?'):10}): operator = '{op_name}'")
                        else:
                            print(f"    Line {line.get('publicCode', '?'):6} ({line.get('transportMode', '?'):10}): operator = NULL")
                    
                    print(f"\n  Unique operator names found: {operator_names}")


async def check_all_authorities():
    """Check ALL authorities to see the full picture."""
    
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
            
            print(f"\n\n{'=' * 100}")
            print(f"ALL AUTHORITIES NAMED 'Skyss' IN THE API:")
            print('=' * 100)
            
            skyss_authorities = [a for a in authorities if "Skyss" in a.get("name", "")]
            
            for auth in skyss_authorities:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                auth_desc = auth.get("description", "")
                
                if ":Authority:" in auth_id:
                    codespace = auth_id.split(":")[0]
                    
                    print(f"\nID: {auth_id}")
                    print(f"  Name: '{auth_name}'")
                    print(f"  Description: '{auth_desc}'")
                    print(f"  Codespace: {codespace}")
                    
                    if codespace == "SOF":
                        print(f"  ⚠️  PROBLEM: Codespace SOF = Kringom, but API says '{auth_name}'")
                    elif codespace == "SKY":
                        print(f"  ✅ OK: Codespace SKY = Skyss, API correctly says '{auth_name}'")


if __name__ == "__main__":
    print("INVESTIGATION: What does the Entur API actually return?")
    print("=" * 100)
    
    asyncio.run(investigate_api_response())
    asyncio.run(check_all_authorities())
