"""Verify what the API actually returns for SOF and SKY."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def main():
    """Get the raw authorities list that our code uses."""
    
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
            
            print(f"{'=' * 100}")
            print(f"WHAT DOES THE API ACTUALLY RETURN?")
            print('=' * 100)
            
            # Filter to transit authorities
            transit = [a for a in authorities if ":Authority:" in a.get("id", "")]
            
            # Find "Skyss" entries
            skyss = [a for a in transit if "Skyss" in a.get("name", "")]
            
            print(f"\n🔍 AUTHORITIES WITH 'Skyss' IN NAME: {len(skyss)}")
            print('=' * 100)
            
            for auth in skyss:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                codespace = auth_id.split(":")[0]
                
                print(f"\n  ID: {auth_id}")
                print(f"  Name: '{auth_name}'")
                print(f"  Codespace: {codespace}")
                
                if codespace == "SOF":
                    print(f"  ❌ PROBLEM: SOF should be 'Kringom', not '{auth_name}'!")
                elif codespace == "SKY":
                    print(f"  ✅ Correct: SKY is '{auth_name}'")
            
            # Check for Kringom
            print(f"\n\n🔍 AUTHORITIES WITH 'Kringom' IN NAME:")
            print('=' * 100)
            
            kringom = [a for a in transit if "Kringom" in a.get("name", "")]
            
            if kringom:
                for auth in kringom:
                    print(f"\n  ID: {auth.get('id')}")
                    print(f"  Name: '{auth.get('name')}'")
            else:
                print("\n  ❌ NONE FOUND - Kringom is missing from API!")
            
            # Show all SOF entries
            print(f"\n\n🔍 ALL SOF CODESPACE AUTHORITIES:")
            print('=' * 100)
            
            sof = [a for a in transit if a.get("id", "").startswith("SOF:")]
            
            for auth in sof:
                auth_id = auth.get("id", "")
                auth_name = auth.get("name", "")
                
                print(f"\n  ID: {auth_id}")
                print(f"  API Name: '{auth_name}'")
                print(f"  Expected: 'Kringom (Sogn og Fjordane)'")
                
                if auth_name != "Kringom":
                    print(f"  🔴 BUG CONFIRMED: API has wrong name!")


if __name__ == "__main__":
    asyncio.run(main())
