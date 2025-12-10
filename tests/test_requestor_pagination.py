"""Test if requestorId helps retrieve remaining data when MoreData=true.

Hypothesis: When MoreData=true, making another request with the same requestorId
might return the next batch of data (pagination).

Test:
1. Request with maxSize=50 (will trigger MoreData=true)
2. Make another request with same requestorId
3. Check if we get the next 50 situations or the same 50
"""
import asyncio
import aiohttp
import json
import uuid

API_URL = "https://api.entur.io/realtime/v1/rest/sx"

async def test_pagination():
    """Test if requestorId provides pagination when MoreData=true."""
    requestor_id = str(uuid.uuid4())
    max_size = 50
    headers = {"Content-Type": "application/json"}
    
    print("🧪 Testing requestorId Pagination with MoreData")
    print("="*80)
    print(f"requestorId: {requestor_id}")
    print(f"maxSize: {max_size}\n")
    
    async with aiohttp.ClientSession() as session:
        # First request
        print("📡 REQUEST #1")
        print("-"*80)
        url = f"{API_URL}?requestorId={requestor_id}&maxSize={max_size}"
        
        async with session.get(url, headers=headers) as response:
            text1 = await response.text()
            data1 = json.loads(text1)
            
            service_delivery1 = data1.get("Siri", {}).get("ServiceDelivery", {})
            more_data1 = service_delivery1.get("MoreData", False)
            
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
            print(f"First 3 IDs: {situations1[:3]}")
            print(f"Last 3 IDs: {situations1[-3:]}\n")
        
        # Second request with same requestorId
        await asyncio.sleep(2)
        
        print("📡 REQUEST #2 (same requestorId)")
        print("-"*80)
        
        async with session.get(url, headers=headers) as response:
            text2 = await response.text()
            data2 = json.loads(text2)
            
            service_delivery2 = data2.get("Siri", {}).get("ServiceDelivery", {})
            more_data2 = service_delivery2.get("MoreData", False)
            
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
            print(f"First 3 IDs: {situations2[:3]}")
            print(f"Last 3 IDs: {situations2[-3:]}\n")
        
        # Compare
        print("="*80)
        print("ANALYSIS")
        print("="*80)
        
        if situations1 == situations2:
            print("❌ SAME DATA - Got identical situations in both requests")
            print("   requestorId does NOT provide pagination")
            print("   Second request returned the same first 50 situations\n")
            
            # Check overlap
            same_count = len(set(situations1) & set(situations2))
            print(f"   Identical situation IDs: {same_count}/{len(situations1)}")
            
        else:
            print("✅ DIFFERENT DATA - Got different situations!")
            print("   requestorId might provide pagination\n")
            
            # Check overlap
            overlap = set(situations1) & set(situations2)
            unique_to_1 = set(situations1) - set(situations2)
            unique_to_2 = set(situations2) - set(situations1)
            
            print(f"   Request 1: {len(situations1)} situations")
            print(f"   Request 2: {len(situations2)} situations")
            print(f"   Overlap: {len(overlap)} situations")
            print(f"   Unique to request 1: {len(unique_to_1)}")
            print(f"   Unique to request 2: {len(unique_to_2)}\n")
            
            if len(overlap) == 0:
                print("   💡 Zero overlap suggests pagination is working!")
                print("   Total unique situations: {len(set(situations1) | set(situations2))}")
        
        # Test without maxSize to get total
        print("\n📡 REQUEST #3 (no maxSize limit, for reference)")
        print("-"*80)
        url_full = f"{API_URL}?requestorId={uuid.uuid4()}"
        
        async with session.get(url_full, headers=headers) as response:
            text_full = await response.text()
            data_full = json.loads(text_full)
            
            service_delivery_full = data_full.get("Siri", {}).get("ServiceDelivery", {})
            sx_delivery_full = service_delivery_full.get("SituationExchangeDelivery", [])
            total_situations = 0
            if sx_delivery_full:
                sits = sx_delivery_full[0].get("Situations", {})
                elements = sits.get("PtSituationElement", [])
                total_situations = len(elements)
            
            print(f"Total situations in system: {total_situations}")
            print(f"MoreData: {service_delivery_full.get('MoreData', False)}\n")
        
        # Conclusion
        print("="*80)
        print("CONCLUSION")
        print("="*80)
        
        if situations1 == situations2:
            print("requestorId does NOT provide pagination when MoreData=true")
            print("To get all data, you must increase maxSize parameter")
            print(f"Currently: maxSize={max_size} returns {len(situations1)} of {total_situations}")
            print(f"Needed: maxSize={total_situations} to get complete dataset")

if __name__ == "__main__":
    asyncio.run(test_pagination())
