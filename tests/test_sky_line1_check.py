"""Check current status of SKY:Line:1 from Entur API."""
import asyncio
import aiohttp
import json
from datetime import datetime


async def check_sky_line1():
    """Fetch and display current disruptions for SKY:Line:1."""
    url = "https://api.entur.io/realtime/v1/services?datasetId=SKY"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Error: HTTP {resp.status}")
                return
            
            xml_data = await resp.text()
            
            # Save raw XML for inspection
            with open("sky_response.xml", "w", encoding="utf-8") as f:
                f.write(xml_data)
            
            print(f"Response saved to sky_response.xml")
            print(f"Response length: {len(xml_data)} characters")
            
            # Look for Line:1 references
            if "Line:1" in xml_data:
                print("\n✓ Found 'Line:1' in response")
                
                # Count occurrences
                count = xml_data.count("Line:1")
                print(f"  Appears {count} time(s)")
                
                # Show context around first occurrence
                idx = xml_data.find("Line:1")
                start = max(0, idx - 200)
                end = min(len(xml_data), idx + 400)
                print(f"\n  Context around first occurrence:")
                print(f"  {xml_data[start:end]}")
            else:
                print("\n✗ No 'Line:1' found in response")
            
            # Check for various line reference formats
            formats = ["SKY:Line:1", "Line:1", ":Line:1", "Line:01"]
            for fmt in formats:
                if fmt in xml_data:
                    print(f"\n✓ Found '{fmt}' in response")


if __name__ == "__main__":
    asyncio.run(check_sky_line1())
