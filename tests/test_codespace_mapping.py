"""Find authoritative codespace to name mapping from Entur APIs."""
import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET

SIRI_SX_API = "https://api.entur.io/realtime/v1/rest/sx"
GRAPHQL_API = "https://api.entur.io/journey-planner/v3/graphql"


async def get_codespaces_from_siri_sx():
    """Get all codespaces that actually have SIRI-SX data."""
    
    headers = {
        "ET-Client-Name": "homeassistant-entur-sx",
    }
    
    print("=" * 100)
    print("STEP 1: GET ALL CODESPACES FROM SIRI-SX API")
    print("=" * 100)
    print(f"\nQuerying: {SIRI_SX_API}")
    print("(This returns ALL situation exchanges for Norway)")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(SIRI_SX_API, headers=headers) as response:
            response.raise_for_status()
            xml_content = await response.text()
            
            # Parse XML to extract codespaces from IDs
            root = ET.fromstring(xml_content)
            
            # Define namespace
            ns = {'siri': 'http://www.siri.org.uk/siri'}
            
            # Find all situation elements
            situations = root.findall('.//siri:PtSituationElement', ns)
            
            print(f"\nFound {len(situations)} total situations")
            
            # Extract codespaces from SituationNumber
            codespaces = set()
            
            for situation in situations:
                sit_number = situation.find('.//siri:SituationNumber', ns)
                if sit_number is not None and sit_number.text:
                    # Format: CODESPACE:SituationNumber:XXX
                    parts = sit_number.text.split(':')
                    if len(parts) >= 1:
                        codespace = parts[0]
                        if len(codespace) == 3 and codespace.isupper():
                            codespaces.add(codespace)
            
            print(f"\n✅ Found {len(codespaces)} unique 3-letter codespaces with active SX data:")
            for cs in sorted(codespaces):
                print(f"  - {cs}")
            
            return sorted(codespaces)


async def map_codespaces_to_operators(codespaces):
    """Try to map codespaces to operator names using GraphQL."""
    
    print(f"\n\n{'=' * 100}")
    print("STEP 2: MAP CODESPACES TO OPERATOR NAMES")
    print('=' * 100)
    
    # Try querying for operators with these codespaces
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
            
            print(f"\nGraphQL returned {len(operators)} operators")
            
            # Map codespace to operator names
            codespace_map = {}
            
            for codespace in codespaces:
                # Find operators with this codespace
                matching = [op for op in operators if op.get("id", "").startswith(f"{codespace}:")]
                
                if matching:
                    # Look for canonical operator (CODESPACE:Operator:CODESPACE)
                    canonical = None
                    for op in matching:
                        op_id = op.get("id", "")
                        parts = op_id.split(":")
                        if len(parts) == 3 and parts[0] == parts[2]:
                            canonical = op
                            break
                    
                    if canonical:
                        codespace_map[codespace] = canonical.get("name")
                    else:
                        # Use first operator name
                        codespace_map[codespace] = matching[0].get("name")
                else:
                    codespace_map[codespace] = None
            
            return codespace_map


async def check_authorities_for_codespace_names(codespaces):
    """Check if authorities give us better names."""
    
    print(f"\n\n{'=' * 100}")
    print("STEP 3: CHECK AUTHORITIES FOR BETTER NAMES")
    print('=' * 100)
    
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
            GRAPHQL_API,
            json={"query": query},
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            authorities = data.get("data", {}).get("authorities", [])
            
            print(f"\nGraphQL returned {len(authorities)} authorities")
            
            # Map codespace to authority names
            auth_map = {}
            
            for codespace in codespaces:
                # Find canonical authority (CODESPACE:Authority:CODESPACE)
                canonical_id = f"{codespace}:Authority:{codespace}"
                matching = [a for a in authorities if a.get("id") == canonical_id]
                
                if matching:
                    auth_map[codespace] = matching[0].get("name")
                else:
                    # Try any authority with this codespace
                    any_match = [a for a in authorities if a.get("id", "").startswith(f"{codespace}:")]
                    if any_match:
                        auth_map[codespace] = any_match[0].get("name")
                    else:
                        auth_map[codespace] = None
            
            return auth_map


async def create_final_mapping():
    """Create the final codespace to friendly name mapping."""
    
    # Step 1: Get codespaces from SIRI-SX
    codespaces = await get_codespaces_from_siri_sx()
    
    # Step 2: Try operators
    operator_map = await map_codespaces_to_operators(codespaces)
    
    # Step 3: Try authorities
    authority_map = await check_authorities_for_codespace_names(codespaces)
    
    # Combine results
    print(f"\n\n{'=' * 100}")
    print("FINAL CODESPACE MAPPING")
    print('=' * 100)
    print("\nCodespace | From Operators API             | From Authorities API           | Recommended")
    print("-" * 120)
    
    final_map = {}
    
    for cs in codespaces:
        op_name = operator_map.get(cs) or "N/A"
        auth_name = authority_map.get(cs) or "N/A"
        
        # Choose best name - PREFER authorities over operators
        # Authorities represent regional transport bodies (what we want)
        # Operators are individual companies (less useful for regional selection)
        if auth_name and auth_name != "N/A":
            recommended = auth_name
        elif op_name and op_name != "N/A":
            recommended = op_name
        else:
            recommended = cs  # Fall back to codespace itself
        
        final_map[cs] = recommended
        
        print(f"{cs:10} | {op_name:30} | {auth_name:30} | {recommended}")
    
    # Generate Python dict for code
    print(f"\n\n{'=' * 100}")
    print("PYTHON CODE FOR INTEGRATION")
    print('=' * 100)
    
    print("\n# Codespace to friendly name mapping")
    print("# Generated from SIRI-SX API + Entur GraphQL")
    print("CODESPACE_NAMES = {")
    for cs in sorted(final_map.keys()):
        name = final_map[cs]
        print(f'    "{cs}": "{name}",')
    print("}")
    
    print("\n\n# Usage in config flow:")
    print('display_name = f"{CODESPACE_NAMES.get(codespace, codespace)} ({codespace})"')
    
    return final_map


if __name__ == "__main__":
    asyncio.run(create_final_mapping())
