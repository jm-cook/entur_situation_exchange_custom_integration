"""Check if the second deviation appears in the full Norway SX feed."""
import asyncio
import aiohttp


async def check_norway_feed():
    """Check the entire Norway SX feed for line 925."""
    print("="*80)
    print("CHECKING ENTIRE NORWAY SX FEED (no datasetId filter)")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        # Try without datasetId - gets ALL of Norway
        sx_url = "https://api.entur.io/realtime/v1/rest/sx"
        headers = {"Content-Type": "application/json"}
        
        print(f"\nFetching: {sx_url}")
        print("This may take a moment - it's all of Norway's situations...\n")
        
        async with session.get(sx_url, headers=headers) as response:
            print(f"Response status: {response.status}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            text = await response.text()
            print(f"Response size: {len(text)} characters")
            
            import json
            data = json.loads(text)
            
            # Navigate to situations
            siri = data.get("Siri", {})
            service_delivery = siri.get("ServiceDelivery", {})
            sx_deliveries = service_delivery.get("SituationExchangeDelivery", [])
            
            print(f"\nTotal SX deliveries: {len(sx_deliveries)}")
            
            total_situations = 0
            line_925_situations = []
            
            for sx_delivery in sx_deliveries:
                situations = sx_delivery.get("Situations", {})
                elements = situations.get("PtSituationElement", [])
                total_situations += len(elements)
                
                for element in elements:
                    # Check if this affects line 925
                    affects = element.get("Affects", {})
                    networks = affects.get("Networks")
                    
                    if not networks:
                        continue
                    
                    # Check all affected lines
                    affected_networks = networks.get("AffectedNetwork", [])
                    for network in affected_networks:
                        lines = network.get("AffectedLine", [])
                        for line in lines:
                            line_ref_obj = line.get("LineRef", {})
                            line_ref = line_ref_obj.get("value", "")
                            
                            if "925" in line_ref:
                                situation_number = element.get("SituationNumber", {}).get("value", "N/A")
                                summaries = element.get("Summary", [])
                                summary = summaries[0].get("value", "N/A") if summaries else "N/A"
                                progress = element.get("Progress", "N/A")
                                validity = element.get("ValidityPeriod", [{}])[0] if element.get("ValidityPeriod") else {}
                                participant_ref = element.get("ParticipantRef", {}).get("value", "N/A")
                                
                                line_925_situations.append({
                                    "situation_number": situation_number,
                                    "participant_ref": participant_ref,
                                    "line_ref": line_ref,
                                    "summary": summary,
                                    "progress": progress,
                                    "start": validity.get("StartTime", "N/A"),
                                    "end": validity.get("EndTime", "N/A")
                                })
                                break  # Found this line
            
            print(f"Total situations in Norway feed: {total_situations}")
            print(f"\n{'='*80}")
            print(f"FOUND {len(line_925_situations)} SITUATION(S) FOR LINE 925 IN NORWAY FEED:")
            print('='*80)
            
            for i, sit in enumerate(line_925_situations, 1):
                print(f"\n{'='*60}")
                print(f"Situation {i}:")
                print('='*60)
                print(f"  Number: {sit['situation_number']}")
                print(f"  ParticipantRef: {sit['participant_ref']}")
                print(f"  Line Ref: {sit['line_ref']}")
                print(f"  Progress: {sit['progress']}")
                print(f"  Start: {sit['start']}")
                print(f"  End: {sit['end']}")
                print(f"  Summary: {sit['summary']}")
            
            print("\n" + "="*80)
            print("CONCLUSION:")
            print("="*80)
            
            if len(line_925_situations) == 1:
                print("⚠️  Still only 1 situation for line 925 even in full Norway feed")
                print("\nPossible explanations:")
                print("1. The second deviation on skyss.no was resolved recently")
                print("2. skyss.no shows additional data not in Entur SX API")
                print("3. skyss.no might have a longer retention period for messages")
                print("4. The second message might be in a different category (not SX)")
            elif len(line_925_situations) > 1:
                print(f"✅ Found {len(line_925_situations)} situations!")
                print("   The second one exists in the Norway feed but not SKY feed.")
                print("   This could be a filtering issue.")
            else:
                print("❌ No situations found at all!")


if __name__ == "__main__":
    asyncio.run(check_norway_feed())
