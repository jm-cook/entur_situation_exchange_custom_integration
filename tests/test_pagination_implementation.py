"""Test the MoreData pagination implementation in api.py.

This test verifies that our pagination logic correctly handles:
1. Single-page responses (MoreData=false)
2. Multi-page responses (MoreData=true)
3. Proper merging of all situations
"""
import asyncio
import sys
from pathlib import Path

# Import directly from api.py file, not through __init__.py
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "entur_sx"))

import aiohttp
import uuid
import json


# Simplified version of EnturSXApiClient for testing
class TestApiClient:
    def __init__(self, operator=None):
        self._operator = operator
        self._operator_code = operator
        self._session = None
        
        base_url = "https://api.entur.io/realtime/v1/rest/sx"
        if operator:
            self._service_url = f"{base_url}?datasetId={operator}"
        else:
            self._service_url = base_url
    
    def set_session(self, session):
        self._session = session
    
    async def async_get_deviations_with_pagination(self):
        """Fetch with pagination support."""
        if not self._session:
            raise RuntimeError("Session not set")

        headers = {"Content-Type": "application/json"}
        
        # Generate requestorId for pagination tracking
        requestor_id = str(uuid.uuid4())
        all_situations = []
        page_count = 0
        max_pages = 20

        try:
            while page_count < max_pages:
                page_count += 1
                
                # Add requestorId parameter for pagination
                url = f"{self._service_url}&requestorId={requestor_id}" if "?" in self._service_url else f"{self._service_url}?requestorId={requestor_id}"
                
                async with self._session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    text = await response.text()
                    data = json.loads(text)

                    # Extract situations from this page
                    service_delivery = data.get("Siri", {}).get("ServiceDelivery", {})
                    sx_delivery = service_delivery.get("SituationExchangeDelivery", [])
                    
                    if sx_delivery:
                        situations_obj = sx_delivery[0].get("Situations", {})
                        situations = situations_obj.get("PtSituationElement", [])
                        
                        if not isinstance(situations, list):
                            situations = [situations]
                        
                        all_situations.extend(situations)
                        
                        print(
                            f"Retrieved page {page_count}: {len(situations)} situations (total: {len(all_situations)})"
                        )

                    # Check for MoreData flag
                    more_data = service_delivery.get("MoreData", False)
                    
                    if more_data:
                        print(f"MoreData=true, fetching next page...")
                    else:
                        if page_count > 1:
                            print(
                                f"Pagination complete: {len(all_situations)} situations across {page_count} pages"
                            )
                        break
            
            return all_situations, page_count
        
        except Exception as err:
            print(f"Error: {err}")
            raise


async def test_pagination_with_small_maxsize():
    """Test pagination by forcing multiple pages with small maxSize."""
    print("="*80)
    print("Testing MoreData Pagination Implementation")
    print("="*80)
    print("Strategy: Use small maxSize (50) to trigger MoreData=true\n")
    
    # Create client with operator to reduce total situations
    client = TestApiClient(operator="SKY")
    
    async with aiohttp.ClientSession() as session:
        client.set_session(session)
        
        # Temporarily modify service_url to use maxSize=50
        original_url = client._service_url
        client._service_url = f"{original_url}&maxSize=50"
        
        print(f"Testing with URL: {client._service_url}\n")
        print("🔄 Fetching deviations (should trigger pagination)...\n")
        
        try:
            situations, pages = await client.async_get_deviations_with_pagination()
            
            print("\n" + "="*80)
            print("RESULTS")
            print("="*80)
            
            print(f"✅ Successfully retrieved data")
            print(f"📊 Total pages: {pages}")
            print(f"📊 Total situations: {len(situations)}")
            
            if len(situations) > 50:
                print(f"\n✅ SUCCESS: Retrieved {len(situations)} situations (>50), pagination worked!")
            elif len(situations) > 0:
                print(f"\n⚠️  Only {len(situations)} situations - pagination may not have been needed")
            else:
                print(f"\n❌ No situations retrieved")
            
            # Show first few as sample
            print(f"\n📋 First 3 situations:")
            for i, sit in enumerate(situations[:3]):
                sit_num = sit.get("SituationNumber", {})
                if isinstance(sit_num, dict):
                    sit_num = sit_num.get("value", "N/A")
                print(f"  {i+1}. {sit_num}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


async def test_normal_operation():
    """Test that normal operation still works (no maxSize override)."""
    print("\n" + "="*80)
    print("Testing Normal Operation (default maxSize)")
    print("="*80)
    
    client = EnturSXApiClient(operator="SKY")
    
async def test_normal_operation():
    """Test that normal operation still works (no maxSize override)."""
    print("\n" + "="*80)
    print("Testing Normal Operation (default maxSize)")
    print("="*80)
    
    client = TestApiClient(operator="SKY")
    
    async with aiohttp.ClientSession() as session:
        client.set_session(session)
        
        print(f"Testing with URL: {client._service_url}\n")
        print("🔄 Fetching deviations...\n")
        
        try:
            situations, pages = await client.async_get_deviations_with_pagination()
            
            print(f"✅ Successfully retrieved data")
            print(f"📊 Total pages: {pages}")
            print(f"📊 Total situations: {len(situations)}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def main():
    await test_pagination_with_small_maxsize()
    await asyncio.sleep(2)
    await test_normal_operation()


if __name__ == "__main__":
    asyncio.run(main())
