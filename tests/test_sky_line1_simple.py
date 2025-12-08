"""Check current status of SKY:Line:1 from Entur API using requests."""
import requests
from datetime import datetime


def check_sky_line1():
    """Fetch and display current disruptions for SKY:Line:1."""
    url = "https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY"
    
    try:
        from datetime import datetime
        print(f"Fetch time: {datetime.now()}")
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Error: HTTP {resp.status_code}")
            return
        
        xml_data = resp.text
        
        # Save raw XML for inspection
        with open("sky_response.xml", "w", encoding="utf-8") as f:
            f.write(xml_data)
        
        print(f"Response saved to sky_response.xml")
        print(f"Response length: {len(xml_data)} characters")
        
        # Look for Line:1 references
        line_formats = ["SKY:Line:1", "Line:1", ":Line:1", "Line:01"]
        for fmt in line_formats:
            if fmt in xml_data:
                count = xml_data.count(fmt)
                print(f"\n✓ Found '{fmt}' - {count} occurrence(s)")
                
                # Show context around first occurrence
                idx = xml_data.find(fmt)
                start = max(0, idx - 300)
                end = min(len(xml_data), idx + 500)
                print(f"\n  Context:")
                print(f"  ...{xml_data[start:end]}...")
                break
        else:
            print("\n✗ No Line:1 reference found in any format")
            
            # Show what lines ARE present
            if "LineRef" in xml_data:
                print("\n  LineRef elements found in response:")
                import re
                lines = re.findall(r'<LineRef>([^<]+)</LineRef>', xml_data)
                unique_lines = sorted(set(lines))
                for line in unique_lines[:20]:  # Show first 20
                    print(f"    - {line}")
                if len(unique_lines) > 20:
                    print(f"    ... and {len(unique_lines) - 20} more")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_sky_line1()
