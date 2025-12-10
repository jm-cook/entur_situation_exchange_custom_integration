"""Quick test to trigger MoreData flag with small maxSize.

This tests what happens when maxSize limits the response.
"""
import asyncio
import aiohttp
import json
import uuid

API_URL = "https://api.entur.io/realtime/v1/rest/sx"

async def test_max_size(max_size: int):
    """Test API with specific maxSize value."""
    requestor_id = str(uuid.uuid4())
    url = f"{API_URL}?requestorId={requestor_id}&maxSize={max_size}"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"Testing maxSize={max_size}")
    print(f"{'='*80}")
    print(f"URL: {url}\n")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            data = json.loads(text)
            
            # Extract key info
            service_delivery = data.get("Siri", {}).get("ServiceDelivery", {})
            more_data = service_delivery.get("MoreData", False)
            
            sx_delivery = service_delivery.get("SituationExchangeDelivery", [])
            situation_count = 0
            if sx_delivery:
                situations = sx_delivery[0].get("Situations", {})
                elements = situations.get("PtSituationElement", [])
                situation_count = len(elements)
            
            response_size = len(text.encode('utf-8'))
            
            print(f"Response size: {response_size:,} bytes ({response_size/1024:.1f} KB)")
            print(f"Situations returned: {situation_count}")
            print(f"MoreData flag: {more_data}")
            
            if more_data:
                print(f"\n⚠️  TRUNCATED - More data exists but was not returned!")
                print(f"   maxSize={max_size} limited the response")
                print(f"   There are more than {situation_count} situations available")
            else:
                print(f"\n✓ Complete response - all {situation_count} situations returned")
            
            return {
                "max_size": max_size,
                "situations": situation_count,
                "more_data": more_data,
                "size_kb": response_size / 1024,
            }

async def main():
    """Test different maxSize values."""
    print("🧪 Entur API MoreData Flag Test")
    print("Testing how maxSize parameter affects response truncation\n")
    
    # Test various maxSize values
    test_values = [10, 50, 100, 200, 500, 1500]  # 1500 is the default
    
    results = []
    for max_size in test_values:
        result = await test_max_size(max_size)
        results.append(result)
        await asyncio.sleep(2)  # Brief delay between requests
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"{'maxSize':<10} {'Situations':<12} {'Size (KB)':<12} {'MoreData':<10} {'Status'}")
    print("-" * 70)
    
    for r in results:
        status = "TRUNCATED" if r['more_data'] else "Complete"
        more_data_str = "true" if r['more_data'] else "false"
        print(f"{r['max_size']:<10} {r['situations']:<12} {r['size_kb']:<12.1f} {more_data_str:<10} {status}")
    
    print(f"\n💡 Findings:")
    print(f"   - Default maxSize is 1500")
    
    # Find where MoreData becomes false
    complete = [r for r in results if not r['more_data']]
    if complete:
        min_complete = min(complete, key=lambda x: x['max_size'])
        print(f"   - maxSize >= {min_complete['max_size']} returns complete dataset")
        print(f"   - Total situations in system: {min_complete['situations']}")
    
    truncated = [r for r in results if r['more_data']]
    if truncated:
        print(f"   - MoreData=true indicates missing disruptions")
        print(f"   - Units: maxSize appears to be count of PtSituationElement items")

if __name__ == "__main__":
    asyncio.run(main())
