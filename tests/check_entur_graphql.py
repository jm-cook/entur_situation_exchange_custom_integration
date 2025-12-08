"""Check Entur's GraphQL API for Line 1 (Bybanen) disruptions."""
import requests
import json


def check_entur_graphql():
    """Query Entur's GraphQL API for situation messages."""
    
    url = "https://api.entur.io/journey-planner/v3/graphql"
    
    # GraphQL query for situations affecting a specific line
    query = """
    query GetSituations {
      situations(codespaces: ["SKY"]) {
        id
        situationNumber
        summary {
          language
          value
        }
        description {
          language
          value
        }
        validityPeriod {
          startTime
          endTime
        }
        reportType
        severity
        affects {
          ... on AffectedLine {
            line {
              id
              publicCode
              name
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "entur_sx_integration_test"
    }
    
    try:
        print("Querying Entur GraphQL API for SKY situations...")
        print("=" * 80)
        
        response = requests.post(
            url,
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        # Save full response
        with open("entur_graphql_situations.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Response saved to entur_graphql_situations.json\n")
        
        if "errors" in data:
            print("GraphQL Errors:")
            for error in data["errors"]:
                print(f"  - {error.get('message', error)}")
            return
        
        situations = data.get("data", {}).get("situations", [])
        
        print(f"Found {len(situations)} total situations for SKY\n")
        
        # Filter for Line 1 / Bybane 1
        line1_situations = []
        for sit in situations:
            affects = sit.get("affects", [])
            for affect in affects:
                line = affect.get("line", {})
                public_code = line.get("publicCode", "")
                line_name = line.get("name", "")
                
                # Check if it's Line 1 or Bybane 1
                if "1" in public_code or "Bybane" in line_name:
                    line1_situations.append((sit, line))
                    break
        
        print(f"Found {len(line1_situations)} situations affecting Line 1 / Bybane\n")
        print("=" * 80)
        
        for i, (sit, line) in enumerate(line1_situations, 1):
            print(f"\nSITUATION {i}:")
            print("-" * 80)
            print(f"ID: {sit.get('id')}")
            print(f"Situation Number: {sit.get('situationNumber')}")
            
            summaries = sit.get('summary', [])
            for s in summaries:
                if s.get('language') == 'no':
                    print(f"Summary: {s.get('value')}")
            
            descriptions = sit.get('description', [])
            for d in descriptions:
                if d.get('language') == 'no':
                    print(f"Description: {d.get('value')}")
            
            validity = sit.get('validityPeriod', {})
            print(f"Valid from: {validity.get('startTime')}")
            print(f"Valid to: {validity.get('endTime')}")
            
            print(f"Report Type: {sit.get('reportType')}")
            print(f"Severity: {sit.get('severity')}")
            
            print(f"Affects Line: {line.get('publicCode')} - {line.get('name')}")
        
        # Also show all unique lines affected
        print("\n" + "=" * 80)
        print("All affected lines in SKY situations:")
        all_lines = set()
        for sit in situations:
            for affect in sit.get("affects", []):
                line = affect.get("line", {})
                if line.get("publicCode"):
                    all_lines.add(f"{line.get('publicCode')} - {line.get('name')}")
        
        for line in sorted(all_lines):
            print(f"  - {line}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_entur_graphql()
