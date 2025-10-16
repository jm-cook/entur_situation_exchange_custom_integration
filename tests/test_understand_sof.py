"""Understand why SOF returns different names in different contexts."""
import asyncio
import aiohttp
import json

GRAPHQL_API = "https://api.entur.io/journey-planner/v3/graphql"


async def deep_dive_sof():
    """Deep dive into SOF codespace to understand the data."""
    
    # Get all operators with SOF codespace
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
        print("=" * 100)
        print("UNDERSTANDING SOF CODESPACE")
        print("=" * 100)
        
        # Get operators
        async with session.post(GRAPHQL_API, json={"query": query}, headers=headers) as response:
            data = await response.json()
            operators = data.get("data", {}).get("operators", [])
            
            sof_operators = [op for op in operators if op.get("id", "").startswith("SOF:")]
            
            print(f"\n1. OPERATORS with SOF codespace: {len(sof_operators)}")
            print("-" * 100)
            for op in sof_operators:
                op_id = op.get("id")
                op_name = op.get("name")
                parts = op_id.split(":")
                is_canonical = len(parts) == 3 and parts[0] == parts[2]
                marker = "⭐ CANONICAL" if is_canonical else "  "
                print(f"  {marker} {op_id:40} → {op_name}")
        
        # Get authorities
        auth_query = """
        query {
          authorities {
            id
            name
          }
        }
        """
        
        async with session.post(GRAPHQL_API, json={"query": auth_query}, headers=headers) as response:
            data = await response.json()
            authorities = data.get("data", {}).get("authorities", [])
            
            sof_authorities = [a for a in authorities if a.get("id", "").startswith("SOF:")]
            
            print(f"\n\n2. AUTHORITIES with SOF codespace: {len(sof_authorities)}")
            print("-" * 100)
            for auth in sof_authorities:
                auth_id = auth.get("id")
                auth_name = auth.get("name")
                parts = auth_id.split(":")
                is_canonical = len(parts) == 3 and parts[0] == parts[2]
                marker = "⭐ CANONICAL" if is_canonical else "  "
                print(f"  {marker} {auth_id:40} → {auth_name}")
        
        print("\n\n" + "=" * 100)
        print("ANALYSIS")
        print("=" * 100)
        print("""
From the Entur documentation:
  SOF = Kringom (Sogn og Fjordane)
  
But there's NO canonical SOF:Operator:SOF or SOF:Authority:SOF in the API!

The operators are:
  - Individual transport companies (GulenSkyss AS, etc.)
  
The authorities are:
  - Administrative entities (possibly contracts/regions)

Neither represents "the regional transport authority" in a user-friendly way.

CONCLUSION:
The API structure doesn't cleanly expose "regional transport authority" names.
The codespace documentation is the source of truth for what users understand.

OPTIONS:
1. Accept that operator names from API are what they are (company names)
2. Use codespace documentation as authoritative source
3. Just show codespace itself: "SOF" without friendly name
4. Combination: Show API name but make codespace prominent

Which makes most sense for SIRI-SX use case?
""")


async def check_what_users_need():
    """What do users actually need for SIRI-SX?"""
    
    print("\n" + "=" * 100)
    print("WHAT DO USERS ACTUALLY NEED?")
    print("=" * 100)
    print("""
For SIRI-SX (Situation Exchange), the integration needs:
  • The 3-letter CODESPACE (e.g., "SKY", "SOF")
  • This is what goes in the datasetId parameter

Users need to identify:
  • Which REGION they want to monitor
  • Examples: "Bergen area", "Sogn og Fjordane", "Oslo"

The question is: What's the best way to help users pick the right codespace?

Options:
  A. Show operator company name from API
     "GulenSkyss AS (SOF)"
     Problem: Users don't know if that's their region
  
  B. Show codespace documentation name
     "Sogn og Fjordane (SOF)"  
     Problem: Need to maintain mapping
  
  C. Show just codespace with description
     "SOF - Sogn og Fjordane regional transport"
     Problem: Still need descriptions somewhere
  
  D. Show codespace only, let users figure it out
     "SOF"
     Problem: Users won't know what it is

What would be most intuitive for a Home Assistant user?
They probably know their REGION (Bergen, Oslo, etc.) not company names.
""")


if __name__ == "__main__":
    asyncio.run(deep_dive_sof())
    asyncio.run(check_what_users_need())
