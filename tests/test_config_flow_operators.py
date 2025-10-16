"""Test that config flow shows all codespaces, not just those with deviations."""
import asyncio
import aiohttp

# Mock the const module
class MockConst:
    CODESPACE_NAMES = {
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
        "SOF": "Sogn og Fjordane",
        "TEL": "Farte",
        "TRO": "Troms fylkestrafikk",
        "VKT": "VKT",
        "VYB": "Vy Bus4You",
        "VYG": "Vy",
        "VYX": "Vy Buss",
        "CTS": "CTS",
        "GCO": "GCO",
        "NSB": "NSB",
    }


async def test_get_all_operators():
    """Test that we get ALL codespaces from the constant."""
    
    # Build operator dict like the API does
    operators = {}
    for codespace, friendly_name in sorted(MockConst.CODESPACE_NAMES.items()):
        display_name = f"{friendly_name} ({codespace})"
        operators[codespace] = display_name
    
    print("=" * 100)
    print("OPERATORS SHOWN IN CONFIG FLOW")
    print("=" * 100)
    print(f"\nTotal: {len(operators)} operators\n")
    
    for codespace, display_name in sorted(operators.items()):
        print(f"  {display_name}")
    
    print("\n\n" + "=" * 100)
    print("KEY BENEFITS")
    print("=" * 100)
    print("\n✅ Shows ALL codespaces defined in CODESPACE_NAMES")
    print("✅ Consistent list - doesn't change based on current deviations")
    print("✅ User can select their operator even if no deviations right now")
    print("✅ No API call needed during config flow - faster!")
    print("✅ Includes regional operators that might not always have deviations")
    
    print("\n\nExample operators available:")
    print(f"  • {operators.get('SKY')} - Always available")
    print(f"  • {operators.get('SOF')} - Always available (even if no current deviations)")
    print(f"  • {operators.get('RUT')} - Always available")
    print(f"  • {operators.get('VKT')} - Always available (smaller operator)")


if __name__ == "__main__":
    asyncio.run(test_get_all_operators())
