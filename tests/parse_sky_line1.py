"""Parse SKY:Line:1 disruptions from the XML response."""
import re
import xml.etree.ElementTree as ET


def parse_sky_line1():
    """Parse and display disruptions for SKY:Line:1."""
    with open("sky_response.xml", encoding="utf-8") as f:
        xml_data = f.read()
    
    # Find all situations that affect SKY:Line:1
    print("=" * 80)
    print("SKY:Line:1 DISRUPTIONS")
    print("=" * 80)
    
    # Parse XML
    try:
        root = ET.fromstring(xml_data)
        
        # Define namespaces (SIRI-SX uses namespaces)
        ns = {
            '': 'http://www.siri.org.uk/siri',
            'siri': 'http://www.siri.org.uk/siri'
        }
        
        # Find all PtSituationElement
        situations = root.findall('.//{http://www.siri.org.uk/siri}PtSituationElement')
        
        line1_situations = []
        
        for sit in situations:
            # Check if this situation affects SKY:Line:1
            line_refs = sit.findall('.//{http://www.siri.org.uk/siri}LineRef')
            
            for line_ref in line_refs:
                if line_ref.text == 'SKY:Line:1':
                    line1_situations.append(sit)
                    break
        
        print(f"\nFound {len(line1_situations)} situation(s) affecting SKY:Line:1\n")
        
        for i, sit in enumerate(line1_situations, 1):
            print(f"\n--- SITUATION {i} ---")
            
            # Extract key fields
            situation_number = sit.find('.//{http://www.siri.org.uk/siri}SituationNumber')
            creation_time = sit.find('.//{http://www.siri.org.uk/siri}CreationTime')
            version_time = sit.find('.//{http://www.siri.org.uk/siri}VersionTime')
            participant_ref = sit.find('.//{http://www.siri.org.uk/siri}ParticipantRef')
            
            summary = sit.find('.//{http://www.siri.org.uk/siri}Summary')
            description = sit.find('.//{http://www.siri.org.uk/siri}Description')
            
            valid_from = sit.find('.//{http://www.siri.org.uk/siri}StartTime')
            valid_to = sit.find('.//{http://www.siri.org.uk/siri}EndTime')
            
            progress = sit.find('.//{http://www.siri.org.uk/siri}Progress')
            report_type = sit.find('.//{http://www.siri.org.uk/siri}ReportType')
            
            print(f"Situation Number: {situation_number.text if situation_number is not None else 'N/A'}")
            print(f"Created: {creation_time.text if creation_time is not None else 'N/A'}")
            print(f"Version: {version_time.text if version_time is not None else 'N/A'}")
            print(f"Participant: {participant_ref.text if participant_ref is not None else 'N/A'}")
            print(f"\nSummary: {summary.text if summary is not None else 'N/A'}")
            print(f"\nDescription: {description.text if description is not None else 'N/A'}")
            print(f"\nValid From: {valid_from.text if valid_from is not None else 'N/A'}")
            print(f"Valid To: {valid_to.text if valid_to is not None else 'N/A'}")
            print(f"\nProgress: {progress.text if progress is not None else 'N/A'}")
            print(f"Report Type: {report_type.text if report_type is not None else 'N/A'}")
            
    except Exception as e:
        print(f"Error parsing XML: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parse_sky_line1()
