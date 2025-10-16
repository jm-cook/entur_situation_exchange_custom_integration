"""Explore the GraphQL schema to understand available fields."""
import asyncio
import aiohttp
import json

API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"


async def explore_schema():
    """Use GraphQL introspection to see what fields are available."""
    
    # First, let's try to get more fields from authorities
    query = """
    query {
      authorities {
        id
        name
        description
        url
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
            print("AUTHORITIES QUERY WITH MORE FIELDS")
            print("=" * 100)
            
            # Show SOF entries
            sof = [a for a in authorities if a.get("id", "").startswith("SOF:")]
            
            print(f"\nSOF Authorities (found {len(sof)}):")
            for auth in sof[:3]:  # Show first 3
                print(f"\n{json.dumps(auth, indent=2, ensure_ascii=False)}")
            
            # Show SKY
            sky = [a for a in authorities if a.get("id", "") == "SKY:Authority:SKY"]
            if sky:
                print(f"\n\nSKY:Authority:SKY:")
                print(json.dumps(sky[0], indent=2, ensure_ascii=False))


async def check_operators_query():
    """Check if there's a separate operators query."""
    
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
    
    print(f"\n\n{'=' * 100}")
    print("TRYING 'operators' QUERY")
    print('=' * 100)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                API_GRAPHQL_URL,
                json={"query": query},
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if "errors" in data:
                    print("\n❌ Operators query failed:")
                    print(json.dumps(data.get("errors"), indent=2))
                else:
                    operators = data.get("data", {}).get("operators", [])
                    print(f"\n✅ Found {len(operators)} operators")
                    
                    # Check for SOF
                    sof_ops = [o for o in operators if "SOF" in o.get("id", "")]
                    print(f"\nSOF operators: {len(sof_ops)}")
                    for op in sof_ops[:3]:
                        print(json.dumps(op, indent=2))
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def check_lines_for_authority_name():
    """Check if we can get authority name from the lines query."""
    
    query = """
    query {
      lines(authorities: ["SOF:Authority:1"]) {
        id
        name
        publicCode
        authority {
          id
          name
        }
        operator {
          id
          name
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "homeassistant-entur-sx",
    }
    
    print(f"\n\n{'=' * 100}")
    print("CHECKING LINES FOR SOF:Authority:1")
    print('=' * 100)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                API_GRAPHQL_URL,
                json={"query": query},
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if "errors" in data:
                    print("\n❌ Query failed:")
                    print(json.dumps(data.get("errors"), indent=2))
                else:
                    lines = data.get("data", {}).get("lines", [])
                    print(f"\n✅ Found {len(lines)} lines for SOF:Authority:1")
                    
                    if lines:
                        print("\nFirst line:")
                        print(json.dumps(lines[0], indent=2, ensure_ascii=False))
                        
                        # What does authority.name say?
                        auth = lines[0].get("authority", {})
                        print(f"\n\nLine's authority.name: '{auth.get('name')}'")
                        print(f"Line's authority.id:   '{auth.get('id')}'")
                        
                        op = lines[0].get("operator", {})
                        print(f"\nLine's operator.name: '{op.get('name')}'")
                        print(f"Line's operator.id:   '{op.get('id')}'")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(explore_schema())
    asyncio.run(check_operators_query())
    asyncio.run(check_lines_for_authority_name())
