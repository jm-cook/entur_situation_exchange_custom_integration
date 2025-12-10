"""Capture a response with MoreData=true for analysis.

Sets maxSize=10 to force truncation, captures the full XML response.
"""
import asyncio
import aiohttp
from pathlib import Path

API_URL = "https://api.entur.io/realtime/v1/rest/sx"


async def capture_moredata_response():
    """Fetch with small maxSize and save raw response."""
    print("="*80)
    print("Capturing MoreData Response")
    print("="*80)
    print("Using maxSize=10 to force truncation\n")
    
    # Use SKY operator to get manageable dataset
    url = f"{API_URL}?datasetId=SKY&maxSize=10"
    
    print(f"URL: {url}\n")
    print("🔄 Fetching response...\n")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.content_type}")
            
            # Print all HTTP response headers
            print(f"\n📋 HTTP Response Headers:")
            print("-" * 80)
            for header_name, header_value in response.headers.items():
                print(f"  {header_name}: {header_value}")
            print("-" * 80)
            
            # Get raw text
            text = await response.text()
            
            # Save to file
            output_dir = Path(__file__).parent
            output_file = output_dir / "moredata_response.xml"
            
            output_file.write_text(text, encoding='utf-8')
            
            print(f"\n✅ Response saved to:")
            print(f"   {output_file.absolute()}")
            
            # Show key info
            if '<MoreData>' in text:
                start = text.find('<MoreData>')
                end = text.find('</MoreData>') + len('</MoreData>')
                more_data_tag = text[start:end]
                print(f"\n📊 {more_data_tag}")
            
            if 'RequestMessageRef' in text:
                print(f"📊 RequestMessageRef: Present in response")
            else:
                print(f"📊 RequestMessageRef: Not present")
            
            # Count situations
            import re
            situations = re.findall(r'<PtSituationElement>', text)
            print(f"📊 Situations in response: {len(situations)}")
            
            print(f"\n💾 File size: {len(text):,} bytes")


if __name__ == "__main__":
    asyncio.run(capture_moredata_response())
