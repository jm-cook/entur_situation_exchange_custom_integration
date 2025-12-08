"""Search for TX1233507 in the API response."""
import re


def find_tx1233507():
    """Find TX1233507 in the XML."""
    with open("sky_response.xml", encoding="utf-8") as f:
        xml_data = f.read()
    
    # Search for TX1233507
    if "TX1233507" in xml_data:
        print("✓ Found TX1233507 in API response\n")
        
        # Find the full PtSituationElement
        idx = xml_data.find("TX1233507")
        situation_start = xml_data.rfind("<PtSituationElement>", 0, idx)
        situation_end = xml_data.find("</PtSituationElement>", idx)
        
        if situation_start >= 0 and situation_end >= 0:
            situation_xml = xml_data[situation_start:situation_end + len("</PtSituationElement>")]
            
            print("=" * 80)
            print("FULL SITUATION ELEMENT FOR TX1233507")
            print("=" * 80)
            print(situation_xml)
            print("\n" + "=" * 80)
            
            # Extract key fields
            summary = re.search(r'<Summary>([^<]+)</Summary>', situation_xml)
            description = re.search(r'<Description>([^<]+)</Description>', situation_xml)
            start_time = re.search(r'<StartTime>([^<]+)</StartTime>', situation_xml)
            end_time = re.search(r'<EndTime>([^<]+)</EndTime>', situation_xml)
            progress = re.search(r'<Progress>([^<]+)</Progress>', situation_xml)
            line_refs = re.findall(r'<LineRef>([^<]+)</LineRef>', situation_xml)
            
            print("\nKEY INFORMATION:")
            print("-" * 80)
            if summary:
                print(f"Summary: {summary.group(1)}")
            if description:
                print(f"Description: {description.group(1)}")
            if start_time:
                print(f"Start: {start_time.group(1)}")
            if end_time:
                print(f"End: {end_time.group(1)}")
            if progress:
                print(f"Progress: {progress.group(1)}")
            if line_refs:
                print(f"Affected Lines: {', '.join(line_refs)}")
            else:
                print("Affected Lines: NONE (no LineRef found!)")
                
                # Check for other affected elements
                if '<Affects>' in situation_xml:
                    affects_start = situation_xml.find('<Affects>')
                    affects_end = situation_xml.find('</Affects>', affects_start)
                    affects_section = situation_xml[affects_start:affects_end + len('</Affects>')]
                    print(f"\nAffects section:\n{affects_section}")
    else:
        print("✗ TX1233507 NOT found in API response")
        
        # Show what we do have
        print("\nMost recent TX situation numbers:")
        tx_nums = re.findall(r'TX(\d+)', xml_data)
        recent = sorted(set(tx_nums), reverse=True)[:15]
        for num in recent:
            print(f"  - TX{num}")


if __name__ == "__main__":
    find_tx1233507()
