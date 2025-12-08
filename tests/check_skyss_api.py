"""Check what API the Skyss avvik page uses."""
import requests
import re


def check_skyss_avvik_api():
    """Fetch the Skyss avvik page and look for API calls."""
    url = "https://www.skyss.no/avvik/"
    
    print("Fetching Skyss avvik page...")
    resp = requests.get(url, timeout=10)
    
    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}")
        return
    
    html = resp.text
    
    print(f"Page size: {len(html)} characters\n")
    
    # Look for API endpoints in the HTML
    api_patterns = [
        r'https://[^"\']+api[^"\']+',
        r'https://[^"\']+/rest/[^"\']+',
        r'https://[^"\']+entur[^"\']+',
        r'https://[^"\']+realtime[^"\']+',
        r'https://[^"\']+avvik[^"\']+',
    ]
    
    print("Looking for API endpoints in HTML...")
    print("=" * 80)
    
    found_apis = set()
    for pattern in api_patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            # Clean up the match
            match = match.rstrip('",;')
            found_apis.add(match)
    
    if found_apis:
        print("\nFound potential API endpoints:")
        for api in sorted(found_apis):
            print(f"  - {api}")
    else:
        print("\nNo obvious API endpoints found in HTML")
    
    # Look for JavaScript files that might contain API calls
    print("\n" + "=" * 80)
    print("Looking for JavaScript files...")
    
    js_files = re.findall(r'<script[^>]+src="([^"]+)"', html)
    
    if js_files:
        print(f"\nFound {len(js_files)} JavaScript files:")
        for js in js_files[:10]:  # Show first 10
            print(f"  - {js}")
    
    # Look for specific keywords
    print("\n" + "=" * 80)
    print("Searching for keywords...")
    
    keywords = [
        'realtime',
        'siri',
        'situation',
        'avvik',
        'disruption',
        'graphql',
        'journey-planner'
    ]
    
    for keyword in keywords:
        if keyword.lower() in html.lower():
            count = html.lower().count(keyword.lower())
            print(f"  ✓ '{keyword}' found {count} time(s)")
            
            # Show context for first occurrence
            idx = html.lower().find(keyword.lower())
            if idx >= 0:
                start = max(0, idx - 100)
                end = min(len(html), idx + 150)
                context = html[start:end].replace('\n', ' ')
                print(f"    Context: ...{context}...")
    
    # Save the HTML for manual inspection
    with open("skyss_avvik_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✓ Full HTML saved to skyss_avvik_page.html")


if __name__ == "__main__":
    check_skyss_avvik_api()
