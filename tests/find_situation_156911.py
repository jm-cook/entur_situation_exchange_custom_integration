"""Search for situation number 156911 in the API response."""
import re


def find_situation_156911():
    """Find situation number 156911 in the XML."""
    with open("sky_response.xml", encoding="utf-8") as f:
        xml_data = f.read()
    
    # Search for 156911
    if "156911" in xml_data:
        print("✓ Found situation 156911 in API response\n")
        
        # Find context around it
        idx = xml_data.find("156911")
        start = max(0, idx - 1500)
        end = min(len(xml_data), idx + 2000)
        
        print("Context:")
        print("=" * 80)
        print(xml_data[start:end])
        print("=" * 80)
        
        # Extract the full PtSituationElement
        # Find the start of the PtSituationElement that contains this
        situation_start = xml_data.rfind("<PtSituationElement>", 0, idx)
        situation_end = xml_data.find("</PtSituationElement>", idx)
        
        if situation_start >= 0 and situation_end >= 0:
            print("\n\nFull Situation Element:")
            print("=" * 80)
            situation_xml = xml_data[situation_start:situation_end + len("</PtSituationElement>")]
            
            # Pretty print key fields
            print("\nKey Information:")
            print("-" * 80)
            
            # Extract fields using regex
            situation_num = re.search(r'<SituationNumber>([^<]+)</SituationNumber>', situation_xml)
            summary = re.search(r'<Summary>([^<]+)</Summary>', situation_xml)
            description = re.search(r'<Description>([^<]+)</Description>', situation_xml)
            start_time = re.search(r'<StartTime>([^<]+)</StartTime>', situation_xml)
            end_time = re.search(r'<EndTime>([^<]+)</EndTime>', situation_xml)
            progress = re.search(r'<Progress>([^<]+)</Progress>', situation_xml)
            severity = re.search(r'<Severity>([^<]+)</Severity>', situation_xml)
            
            # Find all LineRef values
            line_refs = re.findall(r'<LineRef>([^<]+)</LineRef>', situation_xml)
            
            if situation_num:
                print(f"Situation Number: {situation_num.group(1)}")
            if summary:
                print(f"Summary: {summary.group(1)}")
            if description:
                print(f"Description: {description.group(1)}")
            if start_time:
                print(f"Start Time: {start_time.group(1)}")
            if end_time:
                print(f"End Time: {end_time.group(1)}")
            if progress:
                print(f"Progress: {progress.group(1)}")
            if severity:
                print(f"Severity: {severity.group(1)}")
            if line_refs:
                print(f"Affected Lines: {', '.join(line_refs)}")
            
            print("\n" + "=" * 80)
    else:
        print("✗ Situation 156911 NOT found in API response")
        print("\nSearching for recent situation numbers...")
        
        # Find all situation numbers
        situation_nums = re.findall(r'<SituationNumber>SKY:SituationNumber:TX(\d+)</SituationNumber>', xml_data)
        if situation_nums:
            recent = sorted(situation_nums, reverse=True)[:10]
            print(f"\nMost recent situation numbers (top 10):")
            for num in recent:
                print(f"  - TX{num}")


if __name__ == "__main__":
    find_situation_156911()
