"""Show the exact API request and response for SOF:Authority:1."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def show_exact_api_call():
    """Show the exact GraphQL query and response."""
    
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
    
    print("=" * 100)
    print("EXACT API REQUEST")
    print("=" * 100)
    print(f"\nURL: {API_GRAPHQL_URL}")
    print(f"\nMethod: POST")
    print(f"\nHeaders:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nBody (JSON):")
    request_body = {"query": query}
    print(json.dumps(request_body, indent=2))
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            API_GRAPHQL_URL,
            json=request_body,
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            print("\n" + "=" * 100)
            print("API RESPONSE - FULL DATA STRUCTURE")
            print("=" * 100)
            
            # Show structure
            print(f"\nResponse status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")
            
            print(f"\n\nJSON Response structure:")
            print(f"  'data' key present: {('data' in data)}")
            
            if 'data' in data:
                authorities = data['data'].get('authorities', [])
                print(f"  'authorities' array length: {len(authorities)}")
                
                # Find SOF:Authority:1
                sof_1 = None
                for auth in authorities:
                    if auth.get('id') == 'SOF:Authority:1':
                        sof_1 = auth
                        break
                
                if sof_1:
                    print("\n" + "=" * 100)
                    print("SPECIFIC ENTRY: SOF:Authority:1")
                    print("=" * 100)
                    print("\nExact JSON for this authority:")
                    print(json.dumps(sof_1, indent=2, ensure_ascii=False))
                    
                    print("\n\n" + "=" * 100)
                    print("FIELD-BY-FIELD EXTRACTION")
                    print("=" * 100)
                    
                    auth_id = sof_1.get('id')
                    auth_name = sof_1.get('name')
                    
                    print(f"\nauthority.get('id')    = '{auth_id}'")
                    print(f"authority.get('name')  = '{auth_name}'")
                    
                    print("\n\n" + "=" * 100)
                    print("ANALYSIS")
                    print("=" * 100)
                    
                    print(f"\nCodespace (first part before ':')  = '{auth_id.split(':')[0]}'")
                    print(f"Expected operator for SOF codespace = 'Kringom (Sogn og Fjordane)'")
                    print(f"Actual name returned by API        = '{auth_name}'")
                    print(f"\n❌ MISMATCH: API returns '{auth_name}' but should return 'Kringom'")
                    
                    print("\n\nHow we handle this in our code:")
                    print("  1. Extract codespace: SOF")
                    print(f"  2. Create display name: \"{auth_name} (SOF)\"")
                    print(f"  3. Result shown to user: \"Skyss (SOF)\"")
                    print("  4. This distinguishes it from \"Skyss (SKY)\"")
                
                # Also show a few more SOF entries
                print("\n\n" + "=" * 100)
                print("OTHER SOF CODESPACE ENTRIES")
                print("=" * 100)
                
                sof_authorities = [a for a in authorities if a.get('id', '').startswith('SOF:')]
                
                print(f"\nFound {len(sof_authorities)} authorities with SOF codespace:")
                for auth in sof_authorities[:5]:  # Show first 5
                    print(f"\n  {json.dumps(auth, indent=4, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(show_exact_api_call())
