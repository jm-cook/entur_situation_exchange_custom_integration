"""
Test Entur Organisations API v3 to get codespace information.

According to https://developer.entur.org/organisations-api-v3
there should be an API to get all codespaces.

Let's try to access it and see what we can get.
"""

import asyncio
import aiohttp
import json


async def test_organisations_api():
    """Test various endpoints of the Organisations API."""
    
    base_url = "https://api.entur.io/organisations/v3"
    
    async with aiohttp.ClientSession() as session:
        print("=" * 100)
        print("TESTING ENTUR ORGANISATIONS API V3")
        print("=" * 100)
        
        # Try to get the OpenAPI spec first
        print("\n1. Getting API documentation...")
        print("-" * 100)
        try:
            async with session.get(f"{base_url}/api-docs") as response:
                if response.status == 200:
                    api_docs = await response.json()
                    print(f"✅ Got API docs!")
                    print(f"\nAvailable paths:")
                    if 'paths' in api_docs:
                        for path in api_docs['paths'].keys():
                            methods = list(api_docs['paths'][path].keys())
                            print(f"  {path} [{', '.join(methods).upper()}]")
                else:
                    print(f"❌ Status: {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Try common REST endpoints for getting codespaces
        endpoints_to_try = [
            "/codespaces",
            "/code-spaces", 
            "/organisations",
            "/organisations/codespaces",
            "/authorities",
            "/operators",
        ]
        
        print("\n\n2. Trying common endpoint patterns...")
        print("-" * 100)
        for endpoint in endpoints_to_try:
            try:
                url = f"{base_url}{endpoint}"
                print(f"\nTrying: {url}")
                async with session.get(url) as response:
                    print(f"  Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ SUCCESS! Got data:")
                        print(f"  Type: {type(data)}")
                        if isinstance(data, list):
                            print(f"  Count: {len(data)}")
                            if len(data) > 0:
                                print(f"  First item: {json.dumps(data[0], indent=4)}")
                        elif isinstance(data, dict):
                            print(f"  Keys: {list(data.keys())}")
                            print(f"  Sample: {json.dumps(data, indent=4)[:500]}...")
                    elif response.status == 404:
                        print(f"  ❌ Not found")
                    else:
                        print(f"  ❌ Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}")
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        
        # Try with ET-Client-Name header (might be required)
        print("\n\n3. Trying with ET-Client-Name header...")
        print("-" * 100)
        headers = {
            "ET-Client-Name": "ha-entur-sx-testing"
        }
        for endpoint in ["/codespaces", "/organisations"]:
            try:
                url = f"{base_url}{endpoint}"
                print(f"\nTrying: {url}")
                async with session.get(url, headers=headers) as response:
                    print(f"  Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ SUCCESS! Got data:")
                        print(f"  Type: {type(data)}")
                        if isinstance(data, list):
                            print(f"  Count: {len(data)}")
                            if len(data) > 0:
                                print(f"  First item: {json.dumps(data[0], indent=4)}")
                                if len(data) > 1:
                                    print(f"  Second item: {json.dumps(data[1], indent=4)}")
                        break  # If we find something, stop
            except Exception as e:
                print(f"  ❌ Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_organisations_api())
