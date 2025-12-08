"""Check for Bybane specifically in GraphQL."""
import requests
import json


def check_bybane_graphql():
    """Query for Bybane/Light rail disruptions."""
    
    url = "https://api.entur.io/journey-planner/v3/graphql"
    
    # Query for lines in Bergen area
    query = """
    query GetBybane {
      lines(
        authorities: ["SKY"]
        transportModes: [rail, tram, metro]
      ) {
        id
        publicCode
        name
        transportMode
        authority {
          id
          name
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "entur_sx_integration_test"
    }
    
    try:
        print("Searching for Bybane/Light rail lines...")
        print("=" * 80)
        
        response = requests.post(
            url,
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return
        
        data = response.json()
        
        if "errors" in data:
            print("GraphQL Errors:")
            for error in data["errors"]:
                print(f"  - {error.get('message', error)}")
            return
        
        lines = data.get("data", {}).get("lines", [])
        
        print(f"Found {len(lines)} rail/tram/metro lines for SKY:\n")
        
        for line in lines:
            print(f"  Line: {line.get('publicCode')} - {line.get('name')}")
            print(f"    ID: {line.get('id')}")
            print(f"    Mode: {line.get('transportMode')}")
            print(f"    Authority: {line.get('authority', {}).get('name')}")
            print()
        
        # Now query situations for these specific line IDs
        if lines:
            line_ids = [line.get('id') for line in lines]
            print("\n" + "=" * 80)
            print(f"Querying situations for these {len(line_ids)} lines...")
            
            for line in lines:
                line_id = line.get('id')
                print(f"\nChecking {line.get('publicCode')} - {line.get('name')}...")
                
                sit_query = f"""
                query {{
                  line(id: "{line_id}") {{
                    id
                    publicCode
                    name
                    situations {{
                      id
                      situationNumber
                      summary {{
                        value
                      }}
                      validityPeriod {{
                        startTime
                        endTime
                      }}
                    }}
                  }}
                }}
                """
                
                sit_response = requests.post(
                    url,
                    json={"query": sit_query},
                    headers=headers,
                    timeout=10
                )
                
                if sit_response.status_code == 200:
                    sit_data = sit_response.json()
                    line_info = sit_data.get("data", {}).get("line", {})
                    situations = line_info.get("situations", [])
                    
                    if situations:
                        print(f"  ✓ {len(situations)} situation(s) found:")
                        for sit in situations:
                            summaries = sit.get('summary', [])
                            summary = summaries[0].get('value') if summaries else 'No summary'
                            print(f"    - {sit.get('situationNumber')}: {summary}")
                    else:
                        print("  No situations")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_bybane_graphql()
