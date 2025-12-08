"""Look for Vue.js data or API endpoints in the Skyss page."""
import re


def analyze_skyss_html():
    """Analyze the saved HTML for Vue data and API calls."""
    with open("skyss_avvik_page.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    print("Analyzing Skyss avvik page HTML...\n")
    print("=" * 80)
    
    # Look for JSON data in the page
    print("Looking for embedded JSON data...")
    
    # Vue often embeds data in window.__INITIAL_STATE__ or similar
    json_patterns = [
        r'window\.__[A-Z_]+__\s*=\s*(\{.+?\});',
        r'var\s+initialData\s*=\s*(\{.+?\});',
        r'const\s+data\s*=\s*(\{.+?\});',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"\n✓ Found JSON data with pattern: {pattern}")
            for i, match in enumerate(matches[:2], 1):
                print(f"\n  Match {i} (first 500 chars):")
                print(f"  {match[:500]}...")
    
    # Look for URLs in the HTML
    print("\n" + "=" * 80)
    print("Looking for all URLs in the page...")
    
    urls = re.findall(r'https://[^\s"\'<>]+', html)
    unique_urls = set(urls)
    
    # Filter for interesting URLs
    interesting = [url for url in unique_urls if any(keyword in url.lower() 
                   for keyword in ['api', 'data', 'json', 'rest', 'graphql', 'entur', 'realtime'])]
    
    if interesting:
        print(f"\nFound {len(interesting)} interesting URLs:")
        for url in sorted(interesting)[:20]:
            print(f"  - {url}")
    else:
        print("\nNo obvious API URLs found")
    
    # Look for the specific disruption ID format
    print("\n" + "=" * 80)
    print("Looking for disruption ID patterns...")
    
    # Look for forseinkingar_XXXXXX pattern
    disruption_ids = re.findall(r'forseinkingar_(\d+)', html)
    if disruption_ids:
        print(f"\n✓ Found {len(disruption_ids)} disruption IDs with 'forseinkingar_' prefix:")
        for did in sorted(set(disruption_ids))[:10]:
            print(f"  - forseinkingar_{did}")
    
    # Look for any 6-digit numbers that might be IDs
    six_digit = re.findall(r'\b\d{6}\b', html)
    if six_digit:
        unique_ids = sorted(set(six_digit))
        print(f"\n✓ Found {len(unique_ids)} unique 6-digit numbers (potential IDs):")
        for did in unique_ids[:20]:
            print(f"  - {did}")
    
    # Search for specific text about the disruption
    print("\n" + "=" * 80)
    print("Searching for the specific disruption text...")
    
    search_terms = [
        'driftsstans',
        'forseinkingar',
        '156911',
        'Line:1',
        'Bybane 1',
    ]
    
    for term in search_terms:
        if term in html:
            count = html.count(term)
            print(f"\n✓ Found '{term}' - {count} occurrence(s)")
            
            # Show context
            idx = html.find(term)
            start = max(0, idx - 200)
            end = min(len(html), idx + 300)
            context = html[start:end].replace('\n', ' ')
            print(f"  Context: ...{context}...")


if __name__ == "__main__":
    analyze_skyss_html()
