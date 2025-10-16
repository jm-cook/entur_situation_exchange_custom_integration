"""Search for all situations that might relate to line 925."""
import asyncio
import aiohttp


async def search_all_925_situations():
    """Search for any situation mentioning 925."""
    print("="*80)
    print("SEARCHING ALL SITUATIONS FOR LINE 925 REFERENCES")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        sx_url = "https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY"
        headers = {"Content-Type": "application/json"}
        
        async with session.get(sx_url, headers=headers) as response:
            text = await response.text()
            import json
            data = json.loads(text)
            
            # Navigate to situations
            siri = data.get("Siri", {})
            service_delivery = siri.get("ServiceDelivery", {})
            sx_deliveries = service_delivery.get("SituationExchangeDelivery", [])
            
            print(f"\nTotal SX deliveries: {len(sx_deliveries)}")
            
            all_925_refs = []
            
            for sx_delivery in sx_deliveries:
                situations = sx_delivery.get("Situations", {})
                elements = situations.get("PtSituationElement", [])
                
                print(f"Total situations in this delivery: {len(elements)}")
                
                for element in elements:
                    situation_number = element.get("SituationNumber", {}).get("value", "N/A")
                    progress = element.get("Progress", "N/A")
                    
                    # Check if 925 appears ANYWHERE in this situation
                    affects = element.get("Affects", {})
                    networks = affects.get("Networks")
                    
                    if not networks:
                        continue
                    
                    # Collect all affected lines
                    affected_line_refs = []
                    affected_networks = networks.get("AffectedNetwork", [])
                    for network in affected_networks:
                        lines = network.get("AffectedLine", [])
                        for line in lines:
                            line_ref_obj = line.get("LineRef", {})
                            line_ref = line_ref_obj.get("value", "")
                            affected_line_refs.append(line_ref)
                    
                    # Check if 925 is in any of the affected lines
                    has_925 = any("925" in ref for ref in affected_line_refs)
                    
                    if has_925:
                        summaries = element.get("Summary", [])
                        summary = summaries[0].get("value", "N/A") if summaries else "N/A"
                        validity = element.get("ValidityPeriod", [{}])[0] if element.get("ValidityPeriod") else {}
                        
                        all_925_refs.append({
                            "situation_number": situation_number,
                            "progress": progress,
                            "affected_lines": affected_line_refs,
                            "summary": summary,
                            "start": validity.get("StartTime", "N/A"),
                            "end": validity.get("EndTime", "N/A"),
                        })
            
            print(f"\n{'='*80}")
            print(f"FOUND {len(all_925_refs)} SITUATION(S) MENTIONING LINE 925:")
            print('='*80)
            
            for i, sit in enumerate(all_925_refs, 1):
                print(f"\n{'='*60}")
                print(f"Situation {i}:")
                print('='*60)
                print(f"  Number: {sit['situation_number']}")
                print(f"  Progress: {sit['progress']}")
                print(f"  Start: {sit['start']}")
                print(f"  End: {sit['end']}")
                print(f"  Summary: {sit['summary']}")
                print(f"  \n  Affected lines ({len(sit['affected_lines'])}):")
                for line_ref in sit['affected_lines']:
                    marker = " ← LINE 925" if "925" in line_ref else ""
                    print(f"    - {line_ref}{marker}")
            
            if len(all_925_refs) == 0:
                print("\n❌ No situations found mentioning line 925")
            elif len(all_925_refs) == 1:
                print("\n⚠️  Only 1 situation found (skyss.no shows 2)")
                print("   Possible reasons:")
                print("   - The second deviation on skyss.no might be from a different source")
                print("   - The second deviation might have been resolved very recently")
                print("   - skyss.no might show planned future deviations not yet in API")
            else:
                print(f"\n✅ Found {len(all_925_refs)} situations!")
                print("   This matches or exceeds the skyss.no count.")


if __name__ == "__main__":
    asyncio.run(search_all_925_situations())
