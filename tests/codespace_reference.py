"""Create authoritative codespace mapping with manual overrides for known issues."""

# Official codespace names from Entur documentation + GraphQL APIs
# https://enturas.atlassian.net/wiki/spaces/PUBLIC/pages/637370434/List+of+current+Codespaces
# Generated: January 16, 2025

CODESPACE_NAMES = {
    # From GraphQL Authorities API (canonical where available)
    "AKT": "Agder Kollektivtrafikk",
    "ATB": "AtB",
    "BRA": "Brakar",
    "GOA": "Go-Ahead Norge",
    "INN": "Innlandstrafikk",
    "KOL": "Kolumbus",
    "MOR": "FRAM",
    "NBU": "Flybussen Connect",
    "OST": "Østfold kollektivtrafikk",
    "RUT": "Ruter",
    "SJN": "SJ Nord",
    "SKY": "Skyss",
    "TEL": "Farte",
    "TRO": "Troms fylkestrafikk",
    "VKT": "VKT",
    "VYB": "Vy Bus4You",
    "VYG": "Vy",
    "VYX": "Vy Buss",
    
    # Manual overrides for known API issues
    # SOF returns "Skyss" in authorities API but should be regional authority
    "SOF": "Sogn og Fjordane",  # Regional authority (lines may be operated by various companies)
    
    # Codespaces found in SIRI-SX but not in GraphQL (fall back to codespace)
    "CTS": "CTS",
    "GCO": "GCO",
    "NSB": "NSB",  # Legacy codespace, now mostly VYG
}


def get_codespace_display_name(codespace: str) -> str:
    """Get friendly display name for a codespace.
    
    Args:
        codespace: 3-letter codespace (e.g., "SKY", "SOF")
        
    Returns:
        Display name with codespace, e.g., "Skyss (SKY)" or "Sogn og Fjordane (SOF)"
    """
    friendly_name = CODESPACE_NAMES.get(codespace, codespace)
    return f"{friendly_name} ({codespace})"


if __name__ == "__main__":
    print("Codespace Display Names")
    print("=" * 60)
    
    for codespace in sorted(CODESPACE_NAMES.keys()):
        print(f"{codespace}: {get_codespace_display_name(codespace)}")
    
    print("\n\nExamples:")
    print(f"  SKY → {get_codespace_display_name('SKY')}")
    print(f"  SOF → {get_codespace_display_name('SOF')}")
    print(f"  RUT → {get_codespace_display_name('RUT')}")
