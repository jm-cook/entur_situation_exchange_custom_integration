"""Test different header combinations to get JSON from SX API."""
import asyncio
import aiohttp


async def test_sx_api_headers():
    """Test different Accept headers to see which format the API returns."""
    sx_url = "https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY"
    
    test_cases = [
        {
            "name": "No Accept header",
            "headers": {}
        },
        {
            "name": "Accept: application/json",
            "headers": {"Accept": "application/json"}
        },
        {
            "name": "Accept: application/xml",
            "headers": {"Accept": "application/xml"}
        },
        {
            "name": "Accept: text/xml",
            "headers": {"Accept": "text/xml"}
        },
        {
            "name": "Content-Type: application/json",
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Accept: application/json + ET-Client-Name",
            "headers": {
                "Accept": "application/json",
                "ET-Client-Name": "homeassistant-entur-sx"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            print("\n" + "="*80)
            print(f"TEST: {test['name']}")
            print("="*80)
            
            async with session.get(sx_url, headers=test['headers']) as response:
                content_type = response.headers.get('Content-Type', 'N/A')
                print(f"Response Content-Type: {content_type}")
                
                # Check if it's JSON or XML
                if 'json' in content_type.lower():
                    print("✓ Response is JSON")
                    try:
                        data = await response.json()
                        print(f"  Successfully parsed as JSON")
                        # Check structure
                        if "Siri" in data:
                            print(f"  Has 'Siri' key - good structure")
                    except Exception as e:
                        print(f"  ✗ Failed to parse: {e}")
                elif 'xml' in content_type.lower():
                    print("✗ Response is XML")
                    text = await response.text()
                    print(f"  First 200 chars: {text[:200]}")
                else:
                    print(f"✗ Unknown content type")
                    text = await response.text()
                    print(f"  First 200 chars: {text[:200]}")


if __name__ == "__main__":
    asyncio.run(test_sx_api_headers())
