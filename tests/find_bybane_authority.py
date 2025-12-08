"""Try to find Bybanen under different authorities."""
import requests


def find_bybane_authority():
    """Search for Bybane under different authority codes."""
    
    url = "https://api.entur.io/realtime/v1/rest/sx"
    
    # Try different codespaces
    codespaces = ["SKY", "BYB", "GCO", "NSB"]
    
    for codespace in codespaces:
        print(f"\n{'=' * 80}")
        print(f"Checking codespace: {codespace}")
        print('=' * 80)
        
        try:
            response = requests.get(
                f"{url}?datasetId={codespace}",
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                continue
            
            xml_data = response.text
            print(f"Response size: {len(xml_data)} characters")
            
            # Look for Bybane references
            if "bybane" in xml_data.lower():
                print("✓ Found 'bybane' references!")
                
                # Count
                count = xml_data.lower().count("bybane")
                print(f"  Appears {count} time(s)")
                
                # Show context
                idx = xml_data.lower().find("bybane")
                start = max(0, idx - 300)
                end = min(len(xml_data), idx + 400)
                print(f"\n  Context:")
                print(f"  ...{xml_data[start:end]}...")
            else:
                print("✗ No 'bybane' references found")
            
            # Look for Line:1
            import re
            line1_refs = re.findall(r'<LineRef>([^<]*1[^<]*)</LineRef>', xml_data)
            if line1_refs:
                unique_refs = sorted(set(line1_refs))
                print(f"\n  Found LineRef values containing '1':")
                for ref in unique_refs[:10]:
                    print(f"    - {ref}")
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    find_bybane_authority()
