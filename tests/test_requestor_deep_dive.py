"""Deep dive into requestorId behavior - what does the API actually return?

Testing:
1. Request WITHOUT requestorId - does API create one and return it?
2. Request WITH requestorId - does API echo it back in RequestMessageRef?
3. Where is MoreData - in headers or XML body?
"""
import asyncio
import aiohttp
import json
import uuid

API_URL = "https://api.entur.io/realtime/v1/rest/sx"

async def test_no_requestor_id():
    """Test what happens when we DON'T provide requestorId."""
    print("="*80)
    print("TEST 1: NO requestorId provided")
    print("="*80)
    print("Question: Does API create ID and return it?\n")
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}?maxSize=50"
        print(f"URL: {url}\n")
        
        async with session.get(url) as response:
            print(f"Response headers:")
            for key, value in response.headers.items():
                if 'request' in key.lower() or 'more' in key.lower():
                    print(f"  {key}: {value}")
            
            print(f"\n⚠️  Content-Type: {response.content_type}")
            text = await response.text()
            
            # Check if XML or JSON
            if text.strip().startswith('<?xml') or text.strip().startswith('<'):
                print(f"📄 Response is XML, searching for patterns...\n")
                
                if '<MoreData>' in text:
                    start = text.find('<MoreData>')
                    end = text.find('</MoreData>') + len('</MoreData>')
                    print(f"  MoreData: {text[start:end]}")
                
                if '<RequestMessageRef>' in text or 'RequestMessageRef' in text:
                    idx = text.find('RequestMessageRef')
                    snippet = text[max(0, idx-50):min(len(text), idx+250)]
                    print(f"  RequestMessageRef context: ...{snippet}...")
                else:
                    print(f"  RequestMessageRef: NOT FOUND")
                return
            
            data = json.loads(text)
            
            # Check ServiceDelivery
            service = data.get("Siri", {}).get("ServiceDelivery", {})
            
            print(f"\n📦 ServiceDelivery fields:")
            print(f"  ResponseTimestamp: {service.get('ResponseTimestamp', 'N/A')}")
            print(f"  ProducerRef: {service.get('ProducerRef', 'N/A')}")
            print(f"  MoreData: {service.get('MoreData', 'N/A')}")
            
            # Check for RequestMessageRef
            req_msg_ref = service.get("RequestMessageRef")
            if req_msg_ref:
                print(f"  RequestMessageRef: {req_msg_ref}")
            else:
                print(f"  RequestMessageRef: NOT PRESENT")
            
            # All keys in ServiceDelivery
            print(f"\n🔍 All ServiceDelivery keys:")
            for key in service.keys():
                print(f"  - {key}")

async def test_with_requestor_id():
    """Test what happens when we DO provide requestorId."""
    print("\n" + "="*80)
    print("TEST 2: WITH requestorId provided")
    print("="*80)
    print("Question: Does API echo back our ID in RequestMessageRef?\n")
    
    our_id = str(uuid.uuid4())
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}?requestorId={our_id}&maxSize=50"
        print(f"Our requestorId: {our_id}")
        print(f"URL: {url}\n")
        
        async with session.get(url) as response:
            print(f"Response headers:")
            for key, value in response.headers.items():
                if 'request' in key.lower() or 'more' in key.lower():
                    print(f"  {key}: {value}")
            
            print(f"\n⚠️  Content-Type: {response.content_type}")
            text = await response.text()
            
            # Check if XML or JSON
            if text.strip().startswith('<?xml') or text.strip().startswith('<'):
                print(f"📄 Response is XML, searching for patterns...\n")
                
                if '<MoreData>' in text:
                    start = text.find('<MoreData>')
                    end = text.find('</MoreData>') + len('</MoreData>')
                    print(f"  MoreData: {text[start:end]}")
                
                if '<RequestMessageRef>' in text or 'RequestMessageRef' in text:
                    idx = text.find('RequestMessageRef')
                    snippet = text[max(0, idx-50):min(len(text), idx+250)]
                    print(f"  RequestMessageRef context: ...{snippet}...")
                    
                    # Try to extract value
                    if '<RequestMessageRef>' in text:
                        start = text.find('<RequestMessageRef>')
                        end = text.find('</RequestMessageRef>') + len('</RequestMessageRef>')
                        full_tag = text[start:end]
                        print(f"  Full tag: {full_tag}")
                        
                        # Check if it matches
                        if our_id in full_tag:
                            print(f"  ✅ MATCH! API echoed back our requestorId")
                        else:
                            print(f"  ❌ DIFFERENT! Our ID not found in tag")
                else:
                    print(f"  RequestMessageRef: NOT FOUND")
                return
            
            data = json.loads(text)
            
            # Check ServiceDelivery
            service = data.get("Siri", {}).get("ServiceDelivery", {})
            
            print(f"\n📦 ServiceDelivery fields:")
            print(f"  ResponseTimestamp: {service.get('ResponseTimestamp', 'N/A')}")
            print(f"  ProducerRef: {service.get('ProducerRef', 'N/A')}")
            print(f"  MoreData: {service.get('MoreData', 'N/A')}")
            
            # Check for RequestMessageRef
            req_msg_ref = service.get("RequestMessageRef")
            if req_msg_ref:
                print(f"  RequestMessageRef: {req_msg_ref}")
                # Check if it matches our ID
                if isinstance(req_msg_ref, dict):
                    returned_id = req_msg_ref.get("value", "")
                else:
                    returned_id = req_msg_ref
                
                if returned_id == our_id:
                    print(f"  ✅ MATCH! API echoed back our requestorId")
                else:
                    print(f"  ❌ DIFFERENT! API returned: {returned_id}")
            else:
                print(f"  RequestMessageRef: NOT PRESENT")
            
            # All keys in ServiceDelivery
            print(f"\n🔍 All ServiceDelivery keys:")
            for key in service.keys():
                print(f"  - {key}")

async def test_xml_response():
    """Test XML response format (not JSON)."""
    print("\n" + "="*80)
    print("TEST 3: XML Response Format")
    print("="*80)
    print("Question: Does XML have different structure than JSON?\n")
    
    our_id = str(uuid.uuid4())
    
    async with aiohttp.ClientSession() as session:
        # Try XML endpoint
        url = f"https://api.entur.io/realtime/v1/services/sx.xml?requestorId={our_id}&maxSize=50"
        print(f"Our requestorId: {our_id}")
        print(f"URL: {url}\n")
        
        async with session.get(url) as response:
            text = await response.text()
            
            # Search for key patterns
            print(f"🔍 Searching XML for key patterns:\n")
            
            if '<MoreData>' in text:
                start = text.find('<MoreData>')
                end = text.find('</MoreData>') + len('</MoreData>')
                print(f"  MoreData: {text[start:end]}")
            else:
                print(f"  MoreData: NOT FOUND")
            
            if '<RequestMessageRef>' in text:
                start = text.find('<RequestMessageRef>')
                end = text.find('</RequestMessageRef>') + len('</RequestMessageRef>')
                print(f"  RequestMessageRef: {text[start:end]}")
            elif 'RequestMessageRef' in text:
                print(f"  RequestMessageRef: FOUND (searching context)...")
                # Find it in context
                idx = text.find('RequestMessageRef')
                snippet = text[max(0, idx-50):min(len(text), idx+200)]
                print(f"  Context: ...{snippet}...")
            else:
                print(f"  RequestMessageRef: NOT FOUND")

async def main():
    await test_no_requestor_id()
    await asyncio.sleep(1)
    
    await test_with_requestor_id()
    await asyncio.sleep(1)
    
    await test_xml_response()

if __name__ == "__main__":
    asyncio.run(main())
