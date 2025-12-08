"""Find SKY:Line:1 references in raw XML."""
import re


def find_line1_raw():
    """Find all SKY:Line:1 references in the XML."""
    with open("sky_response.xml", encoding="utf-8") as f:
        xml_data = f.read()
    
    # Find all occurrences of SKY:Line:1
    pattern = r'.{0,500}SKY:Line:1.{0,1500}'
    matches = re.findall(pattern, xml_data, re.DOTALL)
    
    print(f"Found {len(matches)} sections containing 'SKY:Line:1'\n")
    
    for i, match in enumerate(matches[:3], 1):  # Show first 3
        print(f"\n{'=' * 80}")
        print(f"MATCH {i}")
        print(f"{'=' * 80}")
        print(match)
        print()


if __name__ == "__main__":
    find_line1_raw()
