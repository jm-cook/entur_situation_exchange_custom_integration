"""Quick debug test to see what the API returns."""
import asyncio
import aiohttp
import uuid

API_URL = "https://api.entur.io/realtime/v1/rest/sx"
REQUESTOR_ID = str(uuid.uuid4())

async def test():
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}?requestorId={REQUESTOR_ID}"
        print(f"URL: {url}")
        
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            text = await response.text()
            print(f"Response length: {len(text):,} chars")
            print(f"Response size: {len(text.encode('utf-8')):,} bytes")
            
            # Show first 500 chars
            print(f"\nFirst 500 chars:")
            print(text[:500])
            
            # Check if it's actually XML
            if text.strip().startswith('<'):
                print("\n⚠️  Response appears to be XML, not JSON!")
                print("The API might be returning SIRI XML format")
            elif text.strip().startswith('{'):
                print("\n✓ Response appears to be JSON")
                import json
                try:
                    data = json.loads(text)
                    print(f"JSON parsed successfully!")
                    print(f"Top-level keys: {list(data.keys())}")
                except Exception as e:
                    print(f"JSON parse failed: {e}")

asyncio.run(test())
