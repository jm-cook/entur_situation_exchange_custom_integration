"""Check if there's actually a disruption for exactly SKY:Line:1."""
import re


def check_exact_line1():
    """Check for exact SKY:Line:1 LineRef."""
    with open("sky_response.xml", encoding="utf-8") as f:
        xml_data = f.read()
    
    # Search for exact LineRef with SKY:Line:1
    # Must have closing tag immediately after
    exact_pattern = r'<LineRef>SKY:Line:1</LineRef>'
    matches = list(re.finditer(exact_pattern, xml_data))
    
    print(f"Exact matches for <LineRef>SKY:Line:1</LineRef>: {len(matches)}")
    
    if matches:
        print("\n✓ Found disruption(s) for SKY:Line:1")
        for i, match in enumerate(matches[:2], 1):
            start = max(0, match.start() - 1000)
            end = min(len(xml_data), match.end() + 1500)
            print(f"\n{'=' * 80}")
            print(f"CONTEXT {i}")
            print(f"{'=' * 80}")
            print(xml_data[start:end])
    else:
        print("\n✗ No disruption for SKY:Line:1")
        print("\nChecking what lines ARE affected...")
        
        # Find all unique LineRef values
        all_lines = re.findall(r'<LineRef>([^<]+)</LineRef>', xml_data)
        unique_lines = sorted(set(all_lines))
        
        print(f"\nFound {len(unique_lines)} unique lines with disruptions:")
        for line in unique_lines:
            print(f"  - {line}")


if __name__ == "__main__":
    check_exact_line1()
