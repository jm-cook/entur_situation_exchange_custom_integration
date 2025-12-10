"""Test what requestorId the API returns and if we can reuse it for pagination.

According to docs:
- If we don't provide requestorId, API creates one and returns it
- The returned id can be used for subsequent requests
- This is perfect for pagination when MoreData=true
"""
import asyncio
import aiohttp
import json

API_URL = "https://api.entur.io/realtime/v1/rest/sx"

async def test_returned_requestor_id():
    """Test using the API's returned requestorId for pagination."""
    headers = {"Content-Type": "application/json"}
    max_size = 50
    
    print("🧪 Testing API-Generated requestorId for Pagination")
    print("="*80)
    print(f"Strategy: Provide requestorId, check what API returns, reuse for pagination\n")
    
    async with aiohttp.ClientSession() as session:
        # Request 1: Provide our own requestorId
        import uuid
        our_requestor_id = str(uuid.uuid4())
        
        print("📡 REQUEST #1 (providing our requestorId)")
        print("-"*80)
        url1 = f"{API_URL}?requestorId={our_requestor_id}&maxSize={max_size}"
        print(f"Our requestorId: {our_requestor_id}\n")
        
        async with session.get(url1, headers=headers) as response:
            text1 = await response.text()
            data1 = json.loads(text1)
            
            service_delivery1 = data1.get("Siri", {}).get("ServiceDelivery", {})
            more_data1 = service_delivery1.get("MoreData", False)
            returned_id1 = service_delivery1.get("RequestMessageRef", {}).get("value", "")
            
            sx_delivery1 = service_delivery1.get("SituationExchangeDelivery", [])
            situations1 = []
            if sx_delivery1:
                sits = sx_delivery1[0].get("Situations", {})
                elements = sits.get("PtSituationElement", [])
                for elem in elements:
                    sit_num_field = elem.get("SituationNumber", "")
                    if isinstance(sit_num_field, dict):
                        sit_num = sit_num_field.get("value", "")
                    else:
                        sit_num = sit_num_field
                    situations1.append(sit_num)
            
            print(f"Situations returned: {len(situations1)}")
            print(f"MoreData: {more_data1}")
            print(f"RequestMessageRef (returned ID): {returned_id1}")
            print(f"First 3 IDs: {situations1[:3]}\n")
        
        if not returned_id1:
            print("❌ API did not return a RequestMessageRef!")
            return
        
        # Request 2: Use the returned requestorId
        await asyncio.sleep(2)
        
        print("📡 REQUEST #2 (using returned requestorId)")
        print("-"*80)
        url2 = f"{API_URL}?requestorId={returned_id1}&maxSize={max_size}"
        print(f"requestorId: {returned_id1}\n")
        
        async with session.get(url2, headers=headers) as response:
            text2 = await response.text()
            data2 = json.loads(text2)
            
            service_delivery2 = data2.get("Siri", {}).get("ServiceDelivery", {})
            more_data2 = service_delivery2.get("MoreData", False)
            returned_id2 = service_delivery2.get("RequestMessageRef", {}).get("value", "")
            
            sx_delivery2 = service_delivery2.get("SituationExchangeDelivery", [])
            situations2 = []
            if sx_delivery2:
                sits = sx_delivery2[0].get("Situations", {})
                elements = sits.get("PtSituationElement", [])
                for elem in elements:
                    sit_num_field = elem.get("SituationNumber", "")
                    if isinstance(sit_num_field, dict):
                        sit_num = sit_num_field.get("value", "")
                    else:
                        sit_num = sit_num_field
                    situations2.append(sit_num)
            
            print(f"Situations returned: {len(situations2)}")
            print(f"MoreData: {more_data2}")
            print(f"RequestMessageRef: {returned_id2}")
            print(f"First 3 IDs: {situations2[:3]}\n")
        
        # Request 3: Continue pagination if still more data
        if more_data2 and returned_id2:
            await asyncio.sleep(2)
            
            print("📡 REQUEST #3 (continuing pagination)")
            print("-"*80)
            url3 = f"{API_URL}?requestorId={returned_id2}&maxSize={max_size}"
            
            async with session.get(url3, headers=headers) as response:
                text3 = await response.text()
                data3 = json.loads(text3)
                
                service_delivery3 = data3.get("Siri", {}).get("ServiceDelivery", {})
                more_data3 = service_delivery3.get("MoreData", False)
                
                sx_delivery3 = service_delivery3.get("SituationExchangeDelivery", [])
                situations3 = []
                if sx_delivery3:
                    sits = sx_delivery3[0].get("Situations", {})
                    elements = sits.get("PtSituationElement", [])
                    for elem in elements:
                        sit_num_field = elem.get("SituationNumber", "")
                        if isinstance(sit_num_field, dict):
                            sit_num = sit_num_field.get("value", "")
                        else:
                            sit_num = sit_num_field
                        situations3.append(sit_num)
                
                print(f"Situations returned: {len(situations3)}")
                print(f"MoreData: {more_data3}")
                print(f"First 3 IDs: {situations3[:3]}\n")
        else:
            situations3 = []
        
        # Analysis
        print("="*80)
        print("ANALYSIS")
        print("="*80)
        
        all_situations = set(situations1) | set(situations2) | set(situations3)
        overlap_1_2 = set(situations1) & set(situations2)
        overlap_2_3 = set(situations2) & set(situations3)
        
        print(f"Request 1: {len(situations1)} situations")
        print(f"Request 2: {len(situations2)} situations")
        print(f"Request 3: {len(situations3)} situations")
        print(f"Total unique: {len(all_situations)}")
        print(f"Overlap 1-2: {len(overlap_1_2)}")
        print(f"Overlap 2-3: {len(overlap_2_3)}\n")
        
        if len(overlap_1_2) == 0 and len(overlap_2_3) == 0:
            print("✅ PERFECT PAGINATION")
            print("   Each request returned different situations")
            print("   Zero overlap - requestorId pagination works!\n")
            print("💡 Implementation Strategy:")
            print("   1. Make initial request (no requestorId)")
            print("   2. Check MoreData flag")
            print("   3. If MoreData=true, use returned RequestMessageRef for next request")
            print("   4. Repeat until MoreData=false")
            print("   5. Merge all results")
        else:
            print("⚠️  Unexpected overlap detected")
            print("   Pagination might not work as expected")

if __name__ == "__main__":
    asyncio.run(test_returned_requestor_id())
