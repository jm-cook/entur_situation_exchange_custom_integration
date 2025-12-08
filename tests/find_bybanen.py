"""Search for how Bybanen is classified in Entur."""
import requests
import json


def find_bybanen():
    """Search for Bybanen/Line 1 in various ways."""
    
    url = "https://api.entur.io/journey-planner/v3/graphql"
    headers = {
        "Content-Type": "application/json",
        "ET-Client-Name": "entur_sx_integration_test"
    }
    
    # Try searching by name
    queries = [
        ("by name 'Bybanen'", """
        query {
          lines(name: "Bybanen") {
            id
            publicCode
            name
            transportMode
            authority { name }
          }
        }
        """),
        ("all SKY lines", """
        query {
          lines(authorities: ["SKY"]) {
            id
            publicCode
            name
            transportMode
          }
        }
        """),
    ]
    
    for query_name, query in queries:
        print(f"\n{'=' * 80}")
        print(f"Searching {query_name}...")
        print('=' * 80)
        
        try:
            response = requests.post(
                url,
                json={"query": query},
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                continue
            
            data = response.json()
            
            if "errors" in data:
                print("Errors:", data["errors"])
                continue
            
            lines = data.get("data", {}).get("lines", [])
            
            if query_name == "all SKY lines":
                print(f"Found {len(lines)} total lines\n")
                
                # Look for anything that might be Bybane
                bybane_keywords = ['bybane', 'light', 'rail', 'tram', '1']
                
                for line in lines:
                    name = line.get('name', '').lower()
                    code = line.get('publicCode', '').lower()
                    
                    if any(kw in name or kw in code for kw in bybane_keywords):
                        print(f"  Potential match:")
                        print(f"    Code: {line.get('publicCode')}")
                        print(f"    Name: {line.get('name')}")
                        print(f"    Mode: {line.get('transportMode')}")
                        print(f"    ID: {line.get('id')}")
                        print()
            else:
                print(f"Found {len(lines)} lines\n")
                for line in lines:
                    print(f"  Code: {line.get('publicCode')}")
                    print(f"  Name: {line.get('name')}")
                    print(f"  Mode: {line.get('transportMode')}")
                    print(f"  Authority: {line.get('authority', {}).get('name')}")
                    print(f"  ID: {line.get('id')}")
                    print()
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    find_bybanen()
