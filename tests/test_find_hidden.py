"""Find the hidden situation TX1222568 and figure out why it's not showing up."""
import asyncio
import aiohttp
import json


async def find_hidden_situation():
    """Find situation TX1222568 and analyze why it's hidden."""
    print("="*80)
    print("SEARCHING FOR: SKY:SituationNumber:TX1222568")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        # Check both SKY-filtered and full Norway feed
        test_urls = [
            ("SKY filtered feed", "https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY"),
            ("Full Norway feed", "https://api.entur.io/realtime/v1/rest/sx")
        ]
        
        for feed_name, sx_url in test_urls:
            print(f"\n{'='*80}")
            print(f"CHECKING: {feed_name}")
            print('='*80)
            
            headers = {"Content-Type": "application/json"}
            
            async with session.get(sx_url, headers=headers) as response:
                text = await response.text()
                data = json.loads(text)
                
                # Navigate to situations
                siri = data.get("Siri", {})
                service_delivery = siri.get("ServiceDelivery", {})
                sx_deliveries = service_delivery.get("SituationExchangeDelivery", [])
                
                found = False
                
                for sx_delivery in sx_deliveries:
                    situations = sx_delivery.get("Situations", {})
                    elements = situations.get("PtSituationElement", [])
                    
                    for element in elements:
                        situation_number = element.get("SituationNumber", {}).get("value", "")
                        
                        if "TX1222568" in situation_number:
                            found = True
                            print(f"\n✅ FOUND IT!")
                            print(f"\nSituation Number: {situation_number}")
                            
                            # Extract all relevant fields
                            progress = element.get("Progress", "N/A")
                            participant_ref = element.get("ParticipantRef", {}).get("value", "N/A")
                            creation_time = element.get("CreationTime", "N/A")
                            
                            summaries = element.get("Summary", [])
                            summary = summaries[0].get("value", "N/A") if summaries else "N/A"
                            
                            descriptions = element.get("Description", [])
                            description = descriptions[0].get("value", "N/A") if descriptions else "N/A"
                            
                            validity_periods = element.get("ValidityPeriod", [])
                            if validity_periods:
                                validity = validity_periods[0]
                                start_time = validity.get("StartTime", "N/A")
                                end_time = validity.get("EndTime", "N/A")
                            else:
                                start_time = "N/A"
                                end_time = "N/A"
                            
                            # Check affected entities
                            affects = element.get("Affects", {})
                            networks = affects.get("Networks")
                            
                            affected_lines = []
                            if networks:
                                affected_networks = networks.get("AffectedNetwork", [])
                                for network in affected_networks:
                                    lines = network.get("AffectedLine", [])
                                    for line in lines:
                                        line_ref_obj = line.get("LineRef", {})
                                        line_ref = line_ref_obj.get("value", "")
                                        if line_ref:
                                            affected_lines.append(line_ref)
                            
                            print(f"\n📋 SITUATION DETAILS:")
                            print(f"  ParticipantRef: {participant_ref}")
                            print(f"  Progress: {progress}")
                            print(f"  CreationTime: {creation_time}")
                            print(f"  Start Time: {start_time}")
                            print(f"  End Time: {end_time}")
                            print(f"  Summary: {summary}")
                            print(f"  Description: {description[:200]}..." if len(description) > 200 else f"  Description: {description}")
                            print(f"\n  Affected Lines ({len(affected_lines)}):")
                            for line_ref in affected_lines:
                                marker = " ← LINE 925" if "925" in line_ref else ""
                                print(f"    - {line_ref}{marker}")
                            
                            # Check what might filter it out
                            print(f"\n🔍 FILTERING ANALYSIS:")
                            
                            # Check Progress
                            if progress.lower() != "open":
                                print(f"  ⚠️  Progress is '{progress}' (not 'open')")
                            else:
                                print(f"  ✓ Progress is 'open'")
                            
                            # Check if line 925 is affected
                            has_925 = any("925" in line for line in affected_lines)
                            if has_925:
                                print(f"  ✓ Line 925 is in affected lines")
                            else:
                                print(f"  ❌ Line 925 is NOT in affected lines")
                                print(f"     This is why it doesn't show up for line 925!")
                            
                            # Check if it has validity period
                            if not validity_periods:
                                print(f"  ❌ No ValidityPeriod - would be filtered out")
                            else:
                                print(f"  ✓ Has ValidityPeriod")
                            
                            # Check start time
                            if start_time == "N/A":
                                print(f"  ❌ No StartTime - would be filtered out")
                            else:
                                print(f"  ✓ Has StartTime")
                            
                            # Check if Networks exists
                            if not networks:
                                print(f"  ❌ No Networks - would be filtered out")
                            else:
                                print(f"  ✓ Has Networks")
                            
                            break
                
                if not found:
                    print(f"❌ NOT FOUND in {feed_name}")
        
        print("\n" + "="*80)
        print("CONCLUSION:")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(find_hidden_situation())
